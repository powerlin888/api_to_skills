import asyncio
import json
import random
import re
import logging
import httpx
from openai import (APIStatusError, APIConnectionError, APITimeoutError,
                    InternalServerError, RateLimitError, OpenAI)
from app.core.config import get_settings

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """你是一个编程指南分析专家。你的任务是将编程指南文档拆解为独立的、可复用的Agent Skills，遵循SKILL.md规范。

每个Skill将生成一个SKILL.md文件，其结构为：
```
---
name: skill-name
description: 简短描述
---
# Skill标题

## 核心指令
操作步骤

## 参考资源
- [api-signature.md](references/api-signature.md): API签名和参数说明
- [code-example.md](references/code-example.md): 代码示例
```

拆解原则：
1. 原子性：每个Skill对应一个独立的、完整的能力单元（如"错误处理"、"认证配置"等）
2. 可执行性：instructions必须包含具体步骤，使Agent能据此直接行动
3. 参考分离：API签名、参数表、代码示例、配置模板归入references数组；操作流程、步骤性指导归入instructions
4. 命名规范：name必须小写、连字符分隔，如"fastapi-error-handling"、"qmt-order-submission"
5. 完整性：每个Skill应自包含，不依赖其他Skill的上下文

references数组中每个元素必须包含name和content两个字段：
- name: 参考资源的文件名（不含扩展名），如"api-signature"、"code-example"
- content: 参考资源的完整内容（API签名、参数表、代码示例等原始文本）

请分析以下Markdown编程指南，输出JSON格式的技能规划清单：
{
  "skills": [
    {
      "name": "skill-name",
      "description": "一句话描述技能用途(<=1024字符)",
      "instructions": "详细的步骤式操作指令，包含前置条件、核心步骤、预期结果(>=50字符)",
      "references": [
        {"name": "api-signature", "content": "完整的API签名和参数说明"},
        {"name": "code-example", "content": "完整的代码示例"}
      ],
      "scripts": ["可选的辅助脚本内容"],
      "tags": ["分类标签1", "分类标签2"]
    }
  ]
}
"""

MERGE_PROMPT = """你是一个Skills去重合并专家。给定多组分段分析产生的Skills列表，请：
1. 去除语义重复的Skills
2. 合并内容高度相似的Skills（合并instructions和references）
3. 确保每个Skill命名唯一

references中每个元素为 {"name": "...", "content": "..."} 格式，合并时需保留所有不重复的reference，名称冲突时合并content。

输出格式与输入相同的JSON：
{
  "skills": [...]
}
"""

CHUNK_MAX_CHARS = 80000
OVERLAP_CHARS = 500
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0
RETRY_MAX_DELAY = 10.0
INTER_CHUNK_DELAY = 2.0


def _split_by_headings(markdown: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    heading_pattern = re.compile(r'^(#{1,3})\s+.+$', re.MULTILINE)
    splits = list(heading_pattern.finditer(markdown))
    if not splits:
        if len(markdown) <= max_chars:
            return [markdown] if markdown.strip() else []
        page_breaks = [m.start() for m in re.finditer(r'\f', markdown)]
        if page_breaks:
            segments = []
            prev = 0
            for pb in page_breaks:
                segments.append(markdown[prev:pb])
                prev = pb + 1
            segments.append(markdown[prev:])
            segments = [s for s in segments if s.strip()]
            chunks = []
            current = segments[0]
            for seg in segments[1:]:
                if len(current) + len(seg) > max_chars:
                    if current.strip():
                        chunks.append(current)
                    current = seg
                else:
                    current += seg
            if current.strip():
                chunks.append(current)
            return chunks
        chunks = []
        i = 0
        while i < len(markdown):
            chunks.append(markdown[i:i + max_chars])
            i += max_chars - OVERLAP_CHARS
        return chunks

    sections = []
    if splits[0].start() > 0:
        sections.append(markdown[:splits[0].start()])
    for idx, match in enumerate(splits):
        start = match.start()
        end = splits[idx + 1].start() if idx + 1 < len(splits) else len(markdown)
        sections.append(markdown[start:end])

    if not sections:
        return [markdown] if markdown.strip() else []

    chunks = []
    current = sections[0]
    for sec in sections[1:]:
        if len(current) + len(sec) > max_chars:
            if current.strip():
                chunks.append(current)
            current = sec
        else:
            current += sec
    if current.strip():
        chunks.append(current)

    return chunks


def _deduplicate_skills(skills: list[dict]) -> list[dict]:
    seen = {}
    for skill in skills:
        name = skill.get("name", "").strip().lower()
        if not name:
            continue
        if name not in seen or len(skill.get("instructions", "")) > len(seen[name].get("instructions", "")):
            seen[name] = skill
    return list(seen.values())


class LlmPlanner:
    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 model_id: str | None = None):
        settings = get_settings()
        timeout_sec = settings.LLM_TIMEOUT_SECONDS
        http_client = httpx.Client(
            timeout=httpx.Timeout(timeout_sec, connect=30.0, read=timeout_sec, write=60.0),
            limits=httpx.Limits(max_keepalive_connections=5),
        )
        self.client = OpenAI(
            api_key=api_key or settings.LLM_DEFAULT_API_KEY,
            base_url=base_url or settings.LLM_DEFAULT_BASE_URL,
            max_retries=0,
            http_client=http_client,
        )
        self.model_id = model_id or settings.LLM_DEFAULT_MODEL_ID
        self.timeout = timeout_sec

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        logger.info(f"[LLM] 调用模型: {self.model_id}, 用户输入长度: {len(user_prompt)}")
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            timeout=self.timeout,
        )
        if response.choices is None or len(response.choices) == 0:
            raise ValueError("LLM返回空choices (可能被限流或服务端异常)")
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM返回空内容")
        logger.info(f"[LLM] 响应长度: {len(content)}, 前200字: {content[:200]}")
        return content

    async def _call_llm_with_retry(self, system_prompt: str, user_prompt: str) -> str:
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                return self._call_llm(system_prompt, user_prompt)
            except UnicodeDecodeError as e:
                last_exception = e
                reason = "响应解码失败 (非UTF-8编码)"
            except ValueError as e:
                last_exception = e
                reason = f"LLM响应异常 ({e})"
            except (APIConnectionError, APITimeoutError) as e:
                last_exception = e
                reason = f"网络错误 ({type(e).__name__})"
            except RateLimitError as e:
                last_exception = e
                reason = "请求频率超限 (RateLimit)"
            except APIStatusError as e:
                if e.status_code >= 500:
                    last_exception = e
                    reason = f"服务端错误 (HTTP {e.status_code})"
                else:
                    raise
            except (httpx.TimeoutException, httpx.ConnectError,
                    httpx.RemoteProtocolError) as e:
                last_exception = e
                reason = f"HTTP传输错误 ({type(e).__name__})"

            if attempt < MAX_RETRIES - 1:
                delay = min(RETRY_BASE_DELAY * (2 ** attempt) + random.uniform(0, 0.5), RETRY_MAX_DELAY)
                logger.warning(f"[LLM] 第{attempt+1}次调用失败: {reason}, {delay:.1f}s后重试...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"[LLM] 重试{MAX_RETRIES}次后仍然失败: {reason}")

        raise last_exception

    def _parse_json_from_content(self, content: str) -> dict:
        content = content.strip()
        if content.startswith('\ufeff'):
            content = content[1:].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        if "```" in content:
            import re
            matches = re.findall(r'```(?:json)?\s*\n?(.*?)```', content, re.DOTALL)
            for match in matches:
                candidate = match.strip()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

        brace_start = content.find('{')
        if brace_start == -1:
            raise json.JSONDecodeError("未找到JSON对象", content, 0)
        content = content[brace_start:]
        last_brace = content.rfind('}')
        if last_brace != -1:
            content = content[:last_brace + 1]
        return json.loads(content)

    async def analyze_structure(self, markdown: str) -> dict:
        chunks = _split_by_headings(markdown)
        if not chunks:
            return {"skills": [], "error": "文档内容为空"}

        all_skills = []
        errors = []

        if len(chunks) == 1:
            try:
                content = await self._call_llm_with_retry(
                    EXTRACTION_PROMPT,
                    f"请分析以下编程指南并生成Skills规划：\n\n{chunks[0]}"
                )
                plan = self._parse_json_from_content(content)
                return plan
            except json.JSONDecodeError as e:
                logger.error(f"[LLM] JSON解析失败: {e}, 原始内容: {content[:500] if content else 'None'}")
                return {"skills": [], "error": f"LLM输出JSON解析失败: {e}"}
            except Exception as e:
                return {"skills": [], "error": f"LLM分析超时或失败: {str(e)}"}

        for i, chunk in enumerate(chunks):
            if i > 0:
                await asyncio.sleep(INTER_CHUNK_DELAY)
            try:
                content = await self._call_llm_with_retry(
                    EXTRACTION_PROMPT,
                    f"这是文档第{i+1}/{len(chunks)}段，请分析并生成Skills规划：\n\n{chunk}"
                )
                plan = self._parse_json_from_content(content)
                skills = plan.get("skills", [])
                all_skills.extend(skills)
            except Exception as e:
                logger.error(f"[LLM] 第{i+1}段分析失败: {e}")
                errors.append(f"第{i+1}段分析失败: {str(e)}")

        if not all_skills and errors:
            return {"skills": [], "error": "; ".join(errors)}

        all_skills = _deduplicate_skills(all_skills)
        return {"skills": all_skills}

    def plan_skills(self, plan: dict) -> list[dict]:
        return plan.get("skills", [])

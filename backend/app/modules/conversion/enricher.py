import json
import re
import logging
import asyncio
from pathlib import Path

from app.modules.conversion.planner import LlmPlanner

logger = logging.getLogger(__name__)

ENRICH_INSTRUCTIONS_PROMPT = """你是一个技术文档精炼专家。给定一个已生成的Agent Skill和原始文档的相关片段，请完善这个Skill的内容。

要求：
1. 检查当前instructions是否遗漏了原始文档中的关键步骤、参数说明或注意事项
2. 如果有遗漏，请补充到instructions中，保持步骤式结构
3. 如果当前instructions已经完整，返回原内容即可
4. instructions必须包含：前置条件、核心步骤（每步一个编号）、预期结果
5. 保持语言简洁专业

当前Skill内容（JSON格式）：
{current_skill}

原始文档相关片段：
{relevant_doc}

请输出完善后的Skill JSON（与输入格式一致）：
{{
  "name": "skill-name",
  "description": "一句话描述",
  "instructions": "完善后的详细步骤式操作指令",
  "tags": ["标签"]
}}
"""

ENRICH_REFERENCES_PROMPT = """你是一个文档摘要专家。给定一个参考资源的内容，请为其生成一个简短的描述摘要。

要求：
1. 摘要不超过50个中文字符
2. 准确概括参考资源的核心内容
3. 如果内容是API签名，注明函数名；如果是代码示例，注明示例用途
4. 只输出摘要文本，不要输出其他内容

参考资源内容：
{ref_content}

摘要："""


def _extract_relevant_chunks(markdown: str, skill_name: str, skill_description: str, max_chars: int = 20000) -> str:
    keywords = set()
    for token in re.split(r'[-_\s]+', skill_name.lower()):
        if len(token) >= 2:
            keywords.add(token)
    for token in re.split(r'[,，\s]+', skill_description.lower()):
        if len(token) >= 2:
            keywords.add(token)

    headings = list(re.finditer(r'^(#{1,3})\s+(.+)$', markdown, re.MULTILINE))
    if not headings:
        return markdown[:max_chars]

    scored_sections = []
    for i, m in enumerate(headings):
        start = m.start()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(markdown)
        section_text = markdown[start:end]
        heading_text = m.group(2).lower()

        score = sum(1 for kw in keywords if kw in heading_text)
        for kw in keywords:
            score += section_text.lower().count(kw) * 0.1
        scored_sections.append((score, section_text))

    scored_sections.sort(key=lambda x: x[0], reverse=True)

    result_parts = []
    total_len = 0
    for score, text in scored_sections:
        if total_len >= max_chars:
            break
        if score > 0:
            result_parts.append(text)
            total_len += len(text)

    if not result_parts:
        return markdown[:max_chars]

    return "\n\n".join(result_parts)[:max_chars]


class SkillEnricher:
    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 model_id: str | None = None):
        self.planner = LlmPlanner(base_url=base_url, api_key=api_key, model_id=model_id)

    async def enrich_skill_dir(self, skill_dir: Path, markdown: str) -> bool:
        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            logger.warning(f"[Enricher] SKILL.md 不存在: {skill_dir}")
            return False

        skill_name = skill_dir.name
        current_content = skill_md_path.read_text(encoding="utf-8")

        description = ""
        instructions = ""
        if current_content.startswith("---"):
            end = current_content.find("---", 3)
            if end != -1:
                import yaml
                try:
                    fm = yaml.safe_load(current_content[3:end])
                    description = fm.get("description", "")
                except yaml.YAMLError:
                    pass
                body = current_content[end + 3:].strip()
                m = re.search(r'##\s*核心指令\s*\n+(.+)', body, re.DOTALL)
                if m:
                    instructions = m.group(1).strip()
                if not instructions:
                    instructions = body

        if not instructions or len(instructions) < 100:
            relevant_doc = _extract_relevant_chunks(markdown, skill_name, description)
            try:
                enriched = await self._enrich_instructions(skill_name, description, instructions, relevant_doc)
                if enriched and enriched.get("instructions") and len(enriched["instructions"]) > len(instructions):
                    instructions = enriched["instructions"]
                    if enriched.get("description") and len(enriched.get("description", "")) > len(description):
                        description = enriched["description"]
            except Exception as e:
                logger.warning(f"[Enricher] instructions完善失败: {skill_name}, {e}")

        ref_map = self._load_reference_map(skill_dir)
        if ref_map:
            enriched_ref_map = {}
            for filename, content in ref_map.items():
                try:
                    summary = await self._generate_ref_summary(content)
                    enriched_ref_map[filename] = summary
                except Exception as e:
                    logger.warning(f"[Enricher] reference摘要生成失败: {filename}, {e}")
                    enriched_ref_map[filename] = ""
            ref_map = enriched_ref_map

        self._rewrite_skill_md(skill_md_path, skill_name, description, instructions, ref_map)
        logger.info(f"[Enricher] 完成: {skill_name}")
        return True

    async def _enrich_instructions(self, name: str, description: str, instructions: str, relevant_doc: str) -> dict:
        current_skill = json.dumps({
            "name": name,
            "description": description,
            "instructions": instructions,
        }, ensure_ascii=False, indent=2)

        prompt = ENRICH_INSTRUCTIONS_PROMPT.format(
            current_skill=current_skill,
            relevant_doc=relevant_doc,
        )

        response = await self.planner._call_llm_with_retry(
            "你是一个技术文档精炼专家。",
            prompt,
        )

        try:
            parsed = self.planner._parse_json_from_content(response)
            return parsed
        except json.JSONDecodeError:
            logger.warning(f"[Enricher] LLM响应JSON解析失败，使用原始instructions")
            return {"instructions": instructions}

    async def _generate_ref_summary(self, content: str) -> str:
        if len(content) < 20:
            return ""

        prompt = ENRICH_REFERENCES_PROMPT.format(ref_content=content[:3000])

        response = await self.planner._call_llm_with_retry(
            "你是一个文档摘要专家。",
            prompt,
        )
        summary = response.strip().strip('"\'').strip()
        if len(summary) > 80:
            summary = summary[:80]
        return summary

    def _load_reference_map(self, skill_dir: Path) -> dict[str, str]:
        refs_dir = skill_dir / "references"
        if not refs_dir.exists():
            return {}

        ref_map = {}
        for ref_file in sorted(refs_dir.glob("*.md")):
            content = ref_file.read_text(encoding="utf-8")
            ref_map[ref_file.name] = content
        return ref_map

    def _rewrite_skill_md(self, skill_md_path: Path, name: str, description: str,
                          instructions: str, ref_map: dict[str, str]):
        import yaml

        frontmatter = {
            "name": name,
            "description": description,
        }

        content = f"---\n{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)}---\n\n"
        content += f"# {name}\n\n"
        content += f"## 核心指令\n\n{instructions}\n"

        if ref_map:
            content += "\n## 参考资源\n\n"
            for filename, summary in sorted(ref_map.items()):
                content += f"- [{filename}](references/{filename})"
                if summary:
                    content += f": {summary}"
                content += "\n"

        skill_md_path.write_text(content, encoding="utf-8")


async def enrich_all_skills(skill_dirs: list[Path], markdown: str,
                            base_url: str | None = None,
                            api_key: str | None = None,
                            model_id: str | None = None) -> int:
    enricher = SkillEnricher(base_url=base_url, api_key=api_key, model_id=model_id)
    enriched_count = 0

    for sd in skill_dirs:
        try:
            success = await enricher.enrich_skill_dir(sd, markdown)
            if success:
                enriched_count += 1
        except Exception as e:
            logger.error(f"[Enricher] 处理失败: {sd.name}, {e}")

    logger.info(f"[Enricher] 完成: {enriched_count}/{len(skill_dirs)} 个Skills已完善")
    return enriched_count
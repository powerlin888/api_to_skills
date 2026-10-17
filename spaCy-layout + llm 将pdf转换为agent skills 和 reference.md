spaCy-layout + LLM 的组合，是实现从 PDF 到 Agent Skills 转化最高效、灵活的方案——它既发挥了专用解析库 spaCy-layout 的精确性，又利用 LLM 的大范围语义理解与生成能力，能够将文档转化为高度结构化的可执行技能。

spaCy-layout 负责“读懂”文档的物理结构，而 LLM 则负责“理解”其语义，再将理解后的内容按规范“重组”为 Agent Skills。这是一种在工程实践中经过验证的经典流程。整个流水线可以概括为以下三个核心步骤：

解析（Parse）：用 spaCy-layout 将 PDF 精准转换为结构化数据（如 Markdown、JSON）。

提炼（Distill）：将结构化数据输入 LLM，通过精心设计的 Prompt，提炼出技能的三要素：

SKILL.md (YAML Frontmatter)：自动生成技能的 name 和 description，让 AI 学会“何时”调用它。

SKILL.md (Body)：利用 LLM 的概括能力，将冗长的原始文档精炼为清晰的指令或工作流。

/references/ 目录：将文档中的核心内容、API 参考、代码示例等存入 references 子目录，确保 AI 在需要时能获取原始细节。

生成（Generate）：按照标准的 Agent Skills 文件夹结构进行组装，生成一个即插即用的技能包。

🛠️ 为什么要用 spaCy-layout + LLM 组合？
你可能已经知道市场上存在像 any2skill 或 prd-to-skill 这类工具，它们也在做类似的事。相比之下，spaCy-layout + LLM 的组合是放弃了“黑箱”带来的便利，换取了近乎无限的灵活性。这种选择意味着你将承担集成 LLM API 的额外工作（这需要用到 API Key），但能换来以下关键收益：

功能维度	spaCy-layout + LLM (自主构建)	any2skill / prd-to-skill (现成工具)
解析精度	高。spaCy-layout 可深度调优，尤其擅长处理复杂、专业的文档布局。	中。通常采用通用解析模型，复杂文档可能出错。
定制能力	极高。你可以完全自定义提炼逻辑、输出格式和技能结构。	低。生成逻辑固定，用户只能接受其输出格式。
内容处理	上下文感知。LLM 能理解段落间的内在联系，而非机械地切分。	多为机械分割。缺乏对文档深层结构（如“注意事项”与“代码示例”的关联）的理解。
💎 核心流程与实现蓝图
建议实现方案如下：

环境准备：安装 spaCy，spaCy-layout 和 openai等SDK。

spaCy-layout 解析：编写 parse_pdf_to_markdown.py 脚本，提取文档的结构化 Markdown。

编写 LLM Prompt 模板：针对 SKILL.md 的不同部分（YAML 元数据、Body 主体）和 references/ 目录的构建，设计不同的 Prompt。

编写主控制脚本：实现步骤2和步骤3，并将 LLM 生成的内容写入到正确的文件夹中。

结果验证与优化：在 IDE 中加载生成的技能并进行测试。

基于你的技术文档，以下是“提炼”环节的 Prompt 参考：

用于生成 YAML 元数据的 Prompt 模板

text
You are an expert at converting technical documentation into AI Agent Skills.

Analyze the following Markdown content extracted from a PDF.
You must generate a SKILL.md file with the following YAML frontmatter:

- `name`: A concise, hyphenated identifier for the skill (e.g., `qmt-api-helper`).
- `description`: A one-sentence string **MUST** be in natural language (e.g., "A skill for querying the QMT platform API."). It is used by the LLM for skill selection, so it must clearly describe when to use this skill.

Here is the Markdown content:
---
{MARKDOWN_CONTENT}
---
用于生成 SKILL.md Body 与 /references/ 目录的 Prompt 模板

text
Your task is to organize the provided technical document into an Agent Skill.

First, create a concise `SKILL.md` body. This file acts as an index and a guide, containing the workflow, best practices, and quickstart instructions. Keep it under 500 lines. Mention that detailed API references, data models, and code examples are stored in separate files under the `./references/` directory.

Second, extract detailed content and save it as separate `.md` files under the `./references/` directory. These files should contain the comprehensive information, code examples, and specifics that are too lengthy for the main `SKILL.md`.

Please ensure the final file structure is as follows:

skill-name/
├── SKILL.md
└── references/
    ├── api_reference.md
    ├── data_models.md
    └── code_examples.md

Based on the provided document, propose the content for:
1. The `SKILL.md` file.
2. The files that should be placed in the `references/` directory.
现在，你可以结合 spaCy-layout 和精心设计的 Prompt，构建出最适合你专业文档的 Agent Skills 了。你需要我针对 QMT 或 GR 文档，为你编写具体的 spaCy-layout 解析代码示例吗？


下面是一个完整的代码示例，演示如何使用 spaCy-layout 解析 PDF，然后调用 LLM (以 OpenAI 为例) 生成符合 Agent Skills 规范的文件结构。你可以根据需要修改 Prompt 或替换为其他 LLM 服务（如 Anthropic、本地模型）。

环境准备
首先安装依赖：

bash
pip install spacy-layout openai
python -m spacy download en_core_web_sm   # spaCy-layout 需要英文模型作为基础
注意：spaCy-layout 要求 Python ≥ 3.10。

代码示例：pdf_to_agent_skill.py
python
import os
import json
from pathlib import Path
from typing import Dict, List, Tuple

import spacy
from spacy_layout import spaCyLayout
from openai import OpenAI

# ==================== 配置区 ====================
# 初始化 OpenAI 客户端（需设置环境变量 OPENAI_API_KEY）
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 可选：指定模型名称，例如 "gpt-4-turbo-preview" 或 "gpt-3.5-turbo"
LLM_MODEL = "gpt-3.5-turbo"

# 输出 Skill 的根目录
OUTPUT_BASE = "./generated_skills"
# ===============================================

def parse_pdf_to_markdown(pdf_path: str) -> str:
    """使用 spaCy-layout 将 PDF 转换为 Markdown 字符串"""
    # 加载 spaCy 模型（只需一个基础英文模型）
    nlp = spacy.blank("en")
    layout = spaCyLayout(nlp)

    # 解析 PDF，得到 Doc 对象
    doc = layout(pdf_path)

    # 获取 Markdown 格式的内容（包含推断的标题层级）
    markdown_content = doc._.markdown
    if not markdown_content or len(markdown_content.strip()) < 50:
        raise ValueError("PDF 解析内容过少，请检查文档是否为文本型 PDF")
    return markdown_content


def call_llm(prompt: str) -> str:
    """调用 OpenAI API 生成内容"""
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert at converting technical documents into AI Agent Skills."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def generate_skill_structure(markdown_content: str) -> Tuple[str, Dict[str, str]]:
    """
    使用 LLM 生成 SKILL.md 主体内容 和 references 文件字典。
    返回: (skill_md_body, {"references/filename.md": "file content", ...})
    """

    # Prompt 1：生成 YAML Frontmatter + 简短的主体
    prompt_frontmatter = f"""
    You are converting a technical PDF into an Agent Skill.

    First, generate the YAML frontmatter for SKILL.md. The file must start with:
    ---
    name: <hyphenated-name>
    description: <one-sentence description of when to use this skill>
    ---

    Then, write the main body of SKILL.md (max 500 lines). This body should act as a guide:
    - Explain the purpose of the skill.
    - Provide a quick start / typical workflow.
    - Mention that detailed references (API docs, examples, data models) are stored in the `./references/` directory.

    Base your output on the following Markdown extracted from the PDF:

    {markdown_content[:30000]}   # 限制长度，避免 token 爆炸
    """

    response_frontmatter = call_llm(prompt_frontmatter)

    # Prompt 2：生成 references 下的文件内容
    prompt_references = f"""
    Based on the same document, extract detailed information and split it into separate Markdown files under the `references/` directory.

    You must output a JSON dictionary where:
    - Keys are file paths relative to the skill root (e.g., "references/api_reference.md", "references/data_models.md").
    - Values are the full Markdown content for that file.

    Do not include any additional text outside the JSON object. The JSON must be valid.

    Document content:
    {markdown_content[:30000]}
    """

    raw_json = call_llm(prompt_references)
    # 尝试解析 JSON，如果失败则返回空字典
    try:
        references_dict = json.loads(raw_json)
    except json.JSONDecodeError:
        print("LLM 返回的不是有效 JSON，尝试提取 JSON 片段...")
        # 简单处理：找到第一个 { 和最后一个 }
        start = raw_json.find("{")
        end = raw_json.rfind("}") + 1
        if start != -1 and end != 0:
            references_dict = json.loads(raw_json[start:end])
        else:
            references_dict = {}
    return response_frontmatter, references_dict


def write_skill(skill_name: str, skill_md_content: str, references: Dict[str, str], base_dir: Path):
    """将生成的技能写入文件系统"""
    skill_dir = base_dir / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)

    # 写入 SKILL.md
    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

    # 写入 references 下的文件
    ref_dir = skill_dir / "references"
    if references:
        ref_dir.mkdir(exist_ok=True)
        for rel_path, content in references.items():
            # 确保路径安全（防止目录遍历）
            safe_path = ref_dir / Path(rel_path).name
            safe_path.write_text(content, encoding="utf-8")

    print(f"✅ Skill 已生成: {skill_dir}")


def main(pdf_path: str):
    # 1. 解析 PDF 为 Markdown
    print("📄 使用 spaCy-layout 解析 PDF...")
    markdown = parse_pdf_to_markdown(pdf_path)

    # 2. 调用 LLM 生成技能结构
    print("🤖 调用 LLM 生成 SKILL.md 和 references...")
    skill_md, references_dict = generate_skill_structure(markdown)

    # 3. 从 SKILL.md 中提取 skill name（从 YAML 的 name 字段）
    # 简单正则提取，也可用 yaml 库
    import re
    match = re.search(r"^---\s*\nname:\s*(\S+)\s*\n---", skill_md, re.MULTILINE)
    if match:
        skill_name = match.group(1)
    else:
        skill_name = "unknown_skill"

    # 4. 写入文件
    write_skill(skill_name, skill_md, references_dict, Path(OUTPUT_BASE))


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("用法: python pdf_to_agent_skill.py <pdf_file_path>")
        sys.exit(1)
    main(sys.argv[1])
使用说明
设置 OpenAI API Key

bash
export OPENAI_API_KEY="sk-..."
运行脚本

bash
python pdf_to_agent_skill.py "国金QMT极速策略交易系统_模型资料_Python_API_说明文档_Python3.pdf"
输出结果
脚本会在 ./generated_skills/ 目录下创建一个以技能命名的文件夹，内部结构类似：

text
generated_skills/
└── qmt-api-helper/
    ├── SKILL.md
    └── references/
        ├── api_reference.md
        ├── data_models.md
        └── code_examples.md
注意事项
spaCy-layout 对中文支持：虽然我们使用了英文模型 en_core_web_sm，但它仍然可以处理中文文本，只是布局分析可能不如中文模型精确。如果你主要处理中文 PDF，可以考虑改用 zh_core_web_sm，但需要确认 spaCy-layout 对该模型的支持（通常可以，但部分布局标签可能仍为英文）。

Token 限制：代码中截取了文档的前 30000 个字符。如果你的 PDF 非常大，可能需要分块处理或使用支持更长上下文的模型（如 GPT-4 Turbo 128K）。

LLM 输出稳定性：generate_skill_structure 中的第二个 Prompt 要求 LLM 输出 JSON，有时可能格式不完美。你可以增加更严格的格式指令，或者使用函数调用（function calling）来保证结构化输出。

替代 LLM：你可以轻松替换 call_llm 函数，例如使用 anthropic SDK、ollama 本地模型等。

进阶：结合 pymupdf-layout 提高速度
如果你觉得 spaCy-layout 较慢，可以在第一步改用 pymupdf-layout 提取 Markdown，后续 LLM 部分完全一样。例如：

python
from pymupdf4llm import to_markdown

markdown = to_markdown(pdf_path)   # 直接返回 Markdown 字符串
这样可以减少对 spaCy 和 spaCy-layout 的依赖，且速度更快。但牺牲了 spaCy 的 Doc 对象带来的丰富元信息（如布局 span 标签）。对于生成 Skill 而言，纯粹的 Markdown 通常已经足够。

这个示例为你提供了一个完整的端到端实现。你可以根据实际文档的特点（中英混合、表格、代码块）调整 Prompt，以获得更高质量的技能输出。
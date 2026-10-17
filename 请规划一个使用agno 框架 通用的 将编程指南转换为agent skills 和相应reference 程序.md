请规划一个使用agno 框架 通用的 将编程指南转换为agent skills 和相应reference 程序

GLM 5.1

The user is asking me to plan a general-purpose program using the Agno framework that converts programming guides into agent skills and corresponding references. This is a design/architecture question that requires understanding of Agno's core concepts - agents, knowledge bases, tools, and how they interact.
文档搜索完成
agent skills knowledge base RAG tools
文档搜索完成
agent core class structure

Now let me look deeper into the Skills system and Knowledge system to understand how to design this program.
文档搜索完成
skills system loadable agent capabilities validation
结构获取完成
libs/agno/agno/skills
结构获取完成
libs/agno/agno/knowledge

Now let me look at the Skills system in detail - the skill.py, agent_skills.py, and loaders to understand the skill data structure.
文件查看完成
libs/agno/agno/skills/skill.py
文件查看完成
libs/agno/agno/skills/agent_skills.py

Let me also look at the skill loader to understand how skills are loaded from the filesystem.
文件查看完成
libs/agno/agno/skills/loaders/local.py
文件查看完成
libs/agno/agno/skills/validator.py

Now I have a solid understanding of the Agno Skills system. Let me also look at the Knowledge system briefly to understand how RAG works, and then I'll also check the document/content processing capabilities.
文件查看完成
libs/agno/agno/knowledge/knowledge.py
文件查看完成
libs/agno/agno/knowledge/reader/markdown_reader.py

Now I have enough understanding to design the program. Let me construct a comprehensive answer.
编程指南 → Agent Skills 转换系统设计
基于 Agno 的 Skills 系统和 Knowledge/RAG 管线，以下是完整的程序架构规划。

核心思路
Agno 的 
SkillL6-L34 是一个结构化的目录单元，包含 SKILL.md（指令+元数据）、scripts/（可执行脚本）和 references/（参考文档）。我们需要一个 Agent 驱动的管线，将任意编程指南自动拆解并生成符合此规范的结构。

架构总览
┌─────────────────────────────────────────────────────┐
│                 输入层 (Input Layer)                  │
│  Markdown / PDF / HTML / 代码仓库 / API 文档          │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│           解析与分块 (Parse & Chunk)                   │
│  MarkdownReader / PDFReader / WebsiteReader          │
│  + DocumentChunking / MarkdownChunking               │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│          Skill 提取 Agent (Extraction Agent)          │
│  分析指南 → 识别独立技能 → 生成 Skill 定义              │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│          Skill 生成器 (Skill Generator)               │
│  SKILL.md (frontmatter + instructions)               │
│  references/ (参考文档)                                │
│  scripts/ (可选的可执行模板)                            │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│          验证与索引 (Validate & Index)                 │
│  validate_skill_directory() → Knowledge RAG          │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│          运行时消费 (Runtime Consumption)              │
│  LocalSkills → Agent(skills=Skills(loaders=[...]))   │
└─────────────────────────────────────────────────────┘
详细实现规划
1. 输入层 — 多源读取
利用 Agno 已有的 Reader 生态（见 knowledge/reader/），支持多种指南格式：

from agno.knowledge.reader import ReaderFactory
from agno.knowledge.reader.markdown_reader import MarkdownReader
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.reader.website_reader import WebsiteReader
 
# 根据输入源类型选择 Reader
def get_reader(source_type: str) -> Reader:
    readers = {
        "markdown": MarkdownReader(chunk_size=3000),
        "pdf": PDFReader(),
        "web": WebsiteReader(),
    }
    return readers.get(source_type, MarkdownReader())
2. Skill 提取 Agent — 核心转换引擎
这是整个系统的关键：一个专门的 Agent，负责分析指南内容、识别可独立执行的技能单元，并输出结构化定义。

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel
from typing import List
 
class SkillDefinition(BaseModel):
    """单个 Skill 的结构化定义"""
    name: str                     # 小写、连字符分隔，如 "react-hooks-patterns"
    description: str              # ≤1024 字符
    instructions: str             # SKILL.md 主体内容，Agent 执行时的指导
    references: List[str]         # 参考文档片段列表
    scripts: List[str]            # 可选的脚本模板名
    allowed_tools: List[str]      # 该 skill 需要的工具
    compatibility: str            # 兼容性说明
 
class GuideAnalysis(BaseModel):
    """指南分析结果"""
    skills: List[SkillDefinition]
 
EXTRACTION_PROMPT = """你是一个编程指南分析专家。你的任务是将编程指南拆解为独立的、可复用的 Agent Skills。
 
拆解原则：
1. **原子性**: 每个 Skill 应该对应一个独立的、完整的能力单元
2. **可执行性**: instructions 必须包含足够的步骤性指导，使 Agent 能据此行动
3. **参考分离**: 背景知识、API 参考、示例代码归入 references；操作步骤归入 instructions
4. **命名规范**: name 必须小写、连字符分隔，如 "fastapi-error-handling"
 
对于每个 Skill：
- instructions: 写成清晰的步骤式指令，包含何时使用、如何执行、注意事项
- references: 提取相关的 API 签名、配置项、代码示例等参考材料
- scripts: 如果指南包含可模板化的代码，生成脚本模板
"""
 
extraction_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions=EXTRACTION_PROMPT,
    response_model=GuideAnalysis,
)
3. Skill 生成器 — 文件系统输出
将 SkillDefinition 转为 Agno Skills 规范的目录结构：

from pathlib import Path
import yaml
 
class SkillGenerator:
    """将 SkillDefinition 写入符合 Agno Skills 规范的目录结构"""
 
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
 
    def generate(self, analysis: GuideAnalysis) -> List[Path]:
        skill_dirs = []
        for skill_def in analysis.skills:
            skill_dir = self.output_dir / skill_def.name
            skill_dir.mkdir(parents=True, exist_ok=True)
 
            # 1. 生成 SKILL.md
            self._write_skill_md(skill_dir, skill_def)
 
            # 2. 生成 references/
            if skill_def.references:
                self._write_references(skill_dir, skill_def)
 
            # 3. 生成 scripts/
            if skill_def.scripts:
                self._write_scripts(skill_dir, skill_def)
 
            skill_dirs.append(skill_dir)
 
        return skill_dirs
 
    def _write_skill_md(self, skill_dir: Path, skill_def: SkillDefinition):
        frontmatter = {
            "name": skill_def.name,
            "description": skill_def.description,
        }
        if skill_def.allowed_tools:
            frontmatter["allowed-tools"] = skill_def.allowed_tools
        if skill_def.compatibility:
            frontmatter["compatibility"] = skill_def.compatibility
 
        content = f"---\n{yaml.dump(frontmatter, allow_unicode=True)}---\n\n{skill_def.instructions}"
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
 
    def _write_references(self, skill_dir: Path, skill_def: SkillDefinition):
        refs_dir = skill_dir / "references"
        refs_dir.mkdir(exist_ok=True)
        for i, ref in enumerate(skill_def.references):
            (refs_dir / f"ref_{i+1}.md").write_text(ref, encoding="utf-8")
 
    def _write_scripts(self, skill_dir: Path, skill_def: SkillDefinition):
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        for i, script in enumerate(skill_def.scripts):
            (scripts_dir / f"script_{i+1}.sh").write_text(script, encoding="utf-8")
4. 验证与索引 — 质量保证
使用 Agno 内置的 validate_skill_directory 进行校验，然后可选地将 references 索引进 Knowledge RAG：

from agno.skills.validator import validate_skill_directory
from agno.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.knowledge.embedder.openai import OpenAIEmbedder
 
class SkillValidator:
    """验证并索引生成的 Skills"""
 
    def validate(self, skill_dir: Path) -> List[str]:
        """返回验证错误列表，空列表=通过"""
        return validate_skill_directory(skill_dir)
 
    def build_knowledge_index(self, skills_dir: Path) -> Knowledge:
        """为所有 references 构建 RAG 索引"""
        knowledge = Knowledge(
            vector_db=LanceDb(
                embedder=OpenAIEmbedder(id="text-embedding-3-small"),
                table_name="guide_skills",
                search_type=SearchType.vector,
            ),
        )
        # 索引所有 references
        for skill_dir in skills_dir.iterdir():
            refs_dir = skill_dir / "references"
            if refs_dir.exists():
                for ref_file in refs_dir.glob("*.md"):
                    knowledge.insert(path=str(ref_file))
        return knowledge
5. 主管线 — 串联一切
from agno.skills import Skills
from agno.skills.loaders.local import LocalSkills
 
class GuideToSkillPipeline:
    """编程指南 → Agent Skills 转换管线"""
 
    def __init__(self, output_dir: str = "./generated_skills"):
        self.reader_factory = ReaderFactory()
        self.extraction_agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            instructions=EXTRACTION_PROMPT,
            response_model=GuideAnalysis,
        )
        self.generator = SkillGenerator(output_dir)
        self.validator = SkillValidator()
 
    def convert(self, source_path: str, source_type: str = "markdown") -> Skills:
        # Step 1: 读取 & 分块
        reader = get_reader(source_type)
        documents = reader.read(Path(source_path))
 
        # Step 2: 提取 Skill 定义
        combined_content = "\n\n".join([doc.content for doc in documents])
        analysis = self.extraction_agent.run(combined_content).content
 
        # Step 3: 生成文件结构
        skill_dirs = self.generator.generate(analysis)
 
        # Step 4: 验证
        for skill_dir in skill_dirs:
            errors = self.validator.validate(skill_dir)
            if errors:
                print(f"⚠️ Skill '{skill_dir.name}' 验证失败: {errors}")
 
        # Step 5: 加载为 Agno Skills 对象
        return Skills(loaders=[LocalSkills(path=self.generator.output_dir)])
 
    def build_agent_with_skills(self, source_path: str) -> Agent:
        """一键生成：指南 → Skills → Agent"""
        skills = self.convert(source_path)
        return Agent(
            model=OpenAIChat(id="gpt-4o"),
            skills=skills,
            knowledge=self.validator.build_knowledge_index(
                Path(self.generator.output_dir)
            ),
            search_knowledge=True,
        )
使用示例
# 从 React 编程指南生成 Skills
pipeline = GuideToSkillPipeline(output_dir="./react_skills")
agent = pipeline.build_agent_with_skills("./react-programming-guide.md")
 
# Agent 现在具备了指南中的所有技能
agent.print_response("帮我创建一个使用 useEffect 的自定义 Hook")
# Agent 会自动：浏览 skills → 加载 instructions → 查阅 references → 生成代码
关键设计决策
决策	理由
用 Agent 提取而非规则解析	编程指南结构千差万别，LLM 理解语义比正则可靠
references 与 instructions 分离	符合 Agno Skills 的渐进式发现模式（
agent_skills.py#L109-L125L109-L125）
内置 validate_skill_directory	生成后立即校验，避免运行时才发现格式错误
可选 Knowledge RAG 索引	references 内容可通过语义搜索按需加载，避免 prompt 膨胀
遵循 Agno Skills 目录规范	直接兼容 LocalSkills loader，无需自定义加载逻辑
下一步
Agent 核心类 — 深入理解 Agent 的 Skills 注入机制
知识库与 RAG — 掌握 references 的语义索引与检索
工具包系统 — 为 Skill 配套生成专用工具
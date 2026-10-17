agno 配置带不同agent skills 和reference的编程智能体 同时能具备统计模型调用次数的功能

GLM 4.7

用户在阅读概述页面，选中了一段文本，然后问了一个关于配置 agno 的问题。
我需要看看代码库中是否有关于配置 agent skills、reference 和模型调用统计的示例。让我检查一下 cookbook 中的相关示例。

结构获取完成
cookbook/02_agents
结构获取完成
cookbook/00_quickstart
结构获取完成
libs/agno

好的，我看到了一些有用的信息：
文件查看完成
cookbook/02_agents/16_skills/basic_skills.py
文件查看完成
cookbook/02_agents/07_knowledge/references_format.py
文件查看完成
cookbook/02_agents/14_advanced/metrics.py

很好！现在我看到了一些关键信息：
文件查看完成
cookbook/02_agents/14_advanced/multi_model_metrics.py
已查看文件大纲
libs/agno/agent/agent.py

路径不对，让我查看正确的路径。
结构获取完成
libs/agno/agno/agent

现在我可以查看 agent.py 了。让我先看看 sample_skills 目录的结构，了解 skills 的组织方式。
结构获取完成
cookbook/02_agents/16_skills/sample_skills
已查看文件大纲
libs/agno/agno/agent/agent.py

太好了！现在我有了足够的信息来回答用户的问题。让我查看一下 sample_skills 目录中具体的内容，了解 skills 的结构。
文件查看完成
cookbook/02_agents/16_skills/sample_skills/code-review/SKILL.md
文件查看完成
cookbook/02_agents/16_skills/sample_skills/git-workflow/SKILL.md

太好了！现在我已经收集了足够的信息。让我总结一下用户的需求以及如何实现：
好的，我来帮你配置一个带不同 skills 和 references 的编程智能体，并且具备统计模型调用次数的功能。

核心配置
在 agno 中，你需要组合三个部分：Skills（技能）、Knowledge References（知识引用）和 Metrics（指标统计）。

1. Skills 配置
Skills 是目录结构的组织方式，每个 skill 包含说明文档和可执行脚本：

SKILL.md - 技能说明
references/ - 参考文档
scripts/ - 辅助脚本
2. References 配置
通过 references_format 控制知识库引用的格式（JSON 或 YAML）

3. Metrics 统计
通过 db 配置数据库持久化，然后获取 run_response.metrics 和 agent.get_session_metrics()

示例代码
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.skills import LocalSkills, Skills
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector, SearchType
from agno.db.postgres import PostgresDb
from rich.pretty import pprint
 
# 数据库配置（用于持久化会话和 metrics）
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
 
# 创建编程智能体，配置多个 skills
skills_dir = Path(__file__).parent / "sample_skills"
 
agent = Agent(
    name="Programming Assistant",
    model=OpenAIResponses(id="gpt-5.2"),
    
    # 1. 配置多个 Skills（code-review 和 git-workflow）
    skills=Skills(loaders=[LocalSkills(str(skills_dir))]),
    
    # 2. 配置 Knowledge 和 References 格式
    knowledge=Knowledge(
        vector_db=PgVector(
            table_name="programming_knowledge",
            db_url=db_url,
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        ),
    ),
    references_format="yaml",  # 或 "json"
    
    # 3. 配置数据库以启用 Metrics 统计
    db=PostgresDb(db_url=db_url),
    session_id="prog-assist-session-1",
    
    instructions=[
        "You are an expert programming assistant with access to code review and Git workflow skills.",
        "Use the skills to provide comprehensive assistance.",
    ],
    markdown=True,
)
 
# 使用智能体并统计指标
if __name__ == "__main__":
    # 添加知识文档（示例）
    agent.knowledge.insert(url="https://example.com/python-best-practices.pdf")
    
    # 运行并获取响应
    run_response = agent.run(
        "Review this code and help me write a proper commit message:\n\n"
        "```python\n"
        "def process_data(data):\n"
        "    return [x * 2 for x in data]\n"
        "```"
    )
    
    # 统计本次运行的指标
    print("\n=== Run Metrics ===")
    if run_response.metrics:
        pprint(run_response.metrics)
    
    # 统计整个会话的指标
    print("\n=== Session Metrics ===")
    session_metrics = agent.get_session_metrics()
    if session_metrics:
        pprint(session_metrics)
Metrics 包含的信息
Metrics 会跟踪以下关键指标：

模型调用次数（model calls）
Token 使用量（input/output tokens）
工具调用次数（tool calls）
运行时间（latency）
成本估算（cost，如果模型提供）
文件结构参考
Copy code
sample_skills/
├── code-review/
│   ├── SKILL.md              # 技能说明
│   ├── references/           # 参考文档
│   │   └── style-guide.md
│   └── scripts/              # 辅助脚本
│       └── check_style.py
└── git-workflow/
    ├── SKILL.md
    ├── references/
    └── scripts/
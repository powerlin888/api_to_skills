Agno怎样为agent 配置 agent skills 和reference

GLM 4.7

用户询问的是：Agno 怎样为 agent 配置 agent skills 和 reference。
我需要查看一下代码库来准确回答这个问题。让我先探索一下 Agno 的代码结构。

结构获取完成
libs/agno

好的，我看到有一个 skills 目录。让我查看一下 skills 目录的结构，以及 agent 目录的结构，了解如何配置 skills。
结构获取完成
libs/agno/agno/skills
结构获取完成
libs/agno/agno/agent

很好，现在我需要查看 agent.py 和相关的 skills 文件，了解如何配置 skills 和 reference。让我先查看 agent.py 的结构。
已查看文件大纲
libs/agno/agno/agent/agent.py
已查看文件大纲
libs/agno/agno/skills/agent_skills.py

很好，我现在看到了 Agent 类的技能配置方式。从代码中可以看到：
文件查看完成
libs/agno/agno/skills/agent_skills.py

很好，我现在已经看到了 Skills 类的初始化方法，它接收一个 SkillLoader 列表。现在让我查看 Skill 类和 LocalLoader 来了解技能的具体结构和如何加载技能。
已查看文件大纲
libs/agno/agno/skills/skill.py
已查看文件大纲
libs/agno/agno/skills/loaders/local.py

很好，现在我需要看看 LocalSkills 的具体实现，以及如何使用它。让我查看更多的实现细节。
文件查看完成
libs/agno/agno/skills/loaders/local.py

用户问的是 Agno 怎样为 agent 配置 agent skills 和 reference。让我根据我刚才查看的代码来回答这个问题。
在 Agno 中为 Agent 配置 Skills 和 References 需要两个步骤：创建 Skill 文件夹结构，然后在 Agent 初始化时加载它们。

配置 Agent Skills
1. 创建 Skill 文件夹结构
每个 Skill 需要以下结构：

my_skill/
├── SKILL.md              # 技能定义（必需）
├── scripts/              # 可执行脚本（可选）
│   └── script.py
└── references/           # 参考文档（可选）
    └── doc.md
SKILL.md 格式（frontmatter + 指令）：

---
name: my_skill
description: 技能描述
license: MIT
tags: [tag1, tag2]
---
 
这里是详细的技能指令，告诉 Agent 如何使用这个技能...
2. 在 Agent 中加载 Skills
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.skills import Skills
from agno.skills.loaders import LocalSkills
 
# 方法1: 从本地目录加载多个 skills
skills = Skills(loaders=[
    LocalSkills(path="./skills/my_skills_folder")
])
 
agent = Agent(
    model=OpenAIChat(id="gpt-4"),
    skills=skills,  # 配置 skills
    name="我的Agent"
)
 
# 方法2: 加载单个 skill 文件夹
skills = Skills(loaders=[
    LocalSkills(path="./skills/my_single_skill")
])
References 配置
References 作为 Skill 的一部分，放在 Skill 文件夹的 references/ 子目录中：

my_skill/
├── SKILL.md
└── references/
    ├── api_documentation.md
    ├── best_practices.md
    └── examples.txt
Agent 可以通过以下方式访问 references：

自动发现：LocalSkills 会自动扫描 references 文件夹并加载所有文件
动态访问：Agent 运行时可以通过工具访问 reference 内容
系统集成：References 会被加载到 Skill 对象的 references 列表中（见 
skill.pyL30）
完整示例
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.skills import Skills
from agno.skills.loaders import LocalSkills
 
# 创建 skills 加载器
skills = Skills(loaders=[
    LocalSkills(path="./skills/code_analysis"),  # 包含 references 的 skill
    LocalSkills(path="./skills/testing"),
])
 
# 创建 Agent 并配置 skills
agent = Agent(
    model=OpenAIChat(id="gpt-4"),
    name="代码分析助手",
    skills=skills,  # 配置 skills
    description="帮助分析和改进代码"
)
 
# 运行
response = agent.run("分析这段代码的质量")
关键要点
Agent 通过 skills 参数接收 Skills 对象（见 
agent.py#L155L155）
Skills 通过 LocalSkills 从文件系统加载（见 
local.py#L29L29）
References 自动从 references/ 子目录加载（见 
local.py#L198L198）
每个 Skill 提供instructions、scripts 和 references 三种资源（见 
skill.py#L6-L23L6-L23）
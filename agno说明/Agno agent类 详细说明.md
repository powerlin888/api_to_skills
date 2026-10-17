Agno agent类 详细说明

GLM 4.7

用户想了解 Agno agent 类的详细说明。根据文档目录，我可以看到有一个专门关于 Agent 类的页面：[Agent 类](8-agent-class)。
我需要查看一下代码仓库结构，找到 Agent 类的具体实现位置。

结构获取完成
libs/agno

好的，我看到有 `libs/agno/agno/agent/` 目录，这里应该包含 Agent 类的实现。让我继续深入查看这个目录的结构。
结构获取完成
libs/agno/agno/agent

完美！找到了 `agent.py` 文件。现在让我查看这个文件的结构，了解 Agent 类的组成部分。
已查看文件大纲
libs/agno/agno/agent/agent.py

非常好！我现在已经获得了 Agent 类的完整结构。这是一个非常庞大的类，包含了很多配置和方法。现在让我为用户提供一个全面的 Agent 类说明。
Agno 的 Agent 类是整个框架的核心，它是一个功能极其丰富的智能体类。让我为你详细解析这个类。

Agent 类概览
Agent 类位于 
libs/agno/agno/agent/agent.pyL68-L1690，是一个基于 Python dataclass 的复杂类，包含了超过 1700 行代码。

核心架构组件
1. 基础配置
model: 指定 Agent 使用的模型（OpenAI、Claude 等）
name: Agent 名称
id: Agent 的唯一标识符（可自动生成）
description: Agent 的描述，用于系统消息
2. 会话管理
session_id: Optional[str] = None
session_state: Optional[Dict[str, Any]] = None
add_session_state_to_context: bool = False
enable_agentic_state: bool = False
cache_session: bool = False
支持持久化会话、会话状态管理、历史会话搜索等。

3. 记忆系统
memory_manager: Optional[MemoryManager] = None
enable_agentic_memory: bool = False
update_memory_on_run: bool = False
add_memories_to_context: Optional[bool] = None
允许 Agent 管理用户记忆，并在运行时自动更新。

4. 知识集成（RAG）
knowledge: Optional[KnowledgeProtocol] = None
knowledge_filters: Optional[Union[Dict[str, Any], List[FilterExpr]]] = None
enable_agentic_knowledge_filters: Optional[bool] = False
add_knowledge_to_context: bool = False
支持向量化知识库、智能过滤、Agentic RAG（让 Agent 自己决定搜索什么）。

5. 工具系统
tools: Optional[Union[List[Union[Toolkit, Callable, Function, Dict]], Callable[..., List]]] = None
tool_call_limit: Optional[int] = None
tool_choice: Optional[Union[str, Dict[str, Any]]] = None
tool_hooks: Optional[List[Callable]] = None
支持函数调用、工具包、工具调用限制和钩子函数。

6. 推理能力
reasoning: bool = False
reasoning_model: Optional[Model] = None
reasoning_min_steps: int = 1
reasoning_max_steps: int = 10
启用后，Agent 会分步骤推理复杂问题。

7. 响应控制
output_schema: Optional[Union[Type[BaseModel], Dict[str, Any]]] = None
parse_response: bool = True
structured_outputs: Optional[bool] = None
支持结构化输出（Pydantic 模型）、JSON 模式等。

8. 钩子系统
pre_hooks: Optional[List[Union[Callable[..., Any], BaseGuardrail, BaseEval]]] = None
post_hooks: Optional[List[Union[Callable[..., Any], BaseGuardrail, BaseEval]]] = None
在处理前后执行自定义逻辑，如防护栏、评估等。

主要方法
运行方法
run(): 同步运行 Agent，返回 RunOutput
arun(): 异步运行 Agent
continue_run(): 继续之前的运行（处理审批、人工介入等）
acontinue_run(): 异步继续运行
流式处理
agent.run("Hello", stream=True)  # 流式响应
agent.run("Hello", stream_events=True)  # 流式事件
存储和持久化
agent.save(db=db, stage="published")  # 保存到数据库
Agent.load(id="agent_id", db=db)  # 从数据库加载
agent.delete(db=db)  # 删除
会话管理
agent.get_session(session_id="xxx")  # 获取会话
agent.get_session_state(session_id="xxx")  # 获取会话状态
agent.update_session_state({"key": "value"}, session_id="xxx")  # 更新状态
CLI 交互
agent.print_response("Hello")  # 打印响应到控制台
agent.cli_app()  # 启动交互式 CLI
使用示例
基础 Agent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
 
agent = Agent(
    name="Assistant",
    model=OpenAIChat(id="gpt-4"),
    description="你是一个乐于助人的助手",
    instructions=["请用中文回答", "保持简洁"],
    tools=[my_tool1, my_tool2]
)
 
response = agent.run("你好！")
print(response.content)
带知识库的 Agent
from agno.agent import Agent
from agno.knowledge.pdf import PdfKnowledgeBase
 
agent = Agent(
    name="RAG Assistant",
    model=OpenAIChat(id="gpt-4"),
    knowledge=PdfKnowledgeBase(path="docs/"),
    add_knowledge_to_context=True
)
带记忆的 Agent
from agno.agent import Agent
from agno.memory.agent import AgentMemory
 
agent = Agent(
    name="Personal Assistant",
    model=OpenAIChat(id="gpt-4"),
    memory_manager=AgentMemory(),
    enable_agentic_memory=True,
    update_memory_on_run=True
)
流式运行
for event in agent.run("写一首诗", stream=True):
    print(event.content, end="", flush=True)
关键特性总结
模块化设计: 使用多个 _ 模块（_run.py, _messages.py, _storage.py 等）委托职责
全异步支持: 所有方法都有对应的异步版本（a 前缀）
数据库集成: 原生支持 SQLite、PostgreSQL、MySQL 等多种数据库
生产就绪: 包含防护栏、评估、监控、遥测等企业级功能
高度可配置: 超过 100 个配置参数，适应各种场景
这个 Agent 类的设计非常强大，适合从简单的聊天机器人到复杂的多智能体系统等各种应用场景。

想深入了解特定功能吗？比如工具集成、知识库、或者会话管理？
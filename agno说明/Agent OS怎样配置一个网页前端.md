Agent OS怎样配置一个网页前端

GLM 4.7

用户问的是"Agent OS怎样配置一个网页前端"。这是一个关于如何配置网页前端的问题，具体是关于Agent OS的。
我来帮你查一下Agent OS的网页前端配置。让我先看看相关文档。

文档搜索完成
Agent OS FastAPI 前端配置
结构获取完成
cookbook/05_agent_os

好的，现在我看到了一些关于Agent OS的信息。从文档搜索结果来看：
文件查看完成
cookbook/05_agent_os/basic.py
文件查看完成
cookbook/05_agent_os/interfaces/agui/basic.py
文件查看完成
cookbook/05_agent_os/interfaces/agui/README.md

很好，我现在看到了基本的配置方式。从这些文件中可以看出：
已查看文件大纲
libs/agno/agno/os/interfaces/agui/agui.py

好的，看到了 AGUI 的基本构造函数。让我查看一下 AGUI 类的完整实现，看看有哪些配置选项。
文件查看完成
libs/agno/agno/os/interfaces/agui/agui.py

很好，现在我看到了 AGUI 的配置选项。让我再看看 BaseInterface 类，可能还有更多配置选项。另外，我应该看看是否有自定义 FastAPI 应用的例子。
文件查看完成
cookbook/05_agent_os/customize/custom_fastapi_app.py

很好，现在我有足够的信息来回答用户的问题了。让我总结一下：
已查看文件大纲
libs/agno/agno/os/os.py

文件不存在，让我找一下正确的文件路径。
结构获取完成
libs/agno/agno/os

好的，AgentOS 的定义应该在 `__init__.py` 或者 `app.py` 中。让我查看一下。
已查看文件大纲
libs/agno/agno/os/__init__.py

用户想知道如何为 Agent OS 配置一个网页前端。让我整理一下我所了解到的信息：
Agent OS 配置网页前端主要有两种方式：

方式一：使用内置 AG-UI 接口（推荐）
这是最简单的方式，Agent OS 自带 AG-UI 接口，可以直接暴露聊天界面：

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.os.interfaces.agui import AGUI
 
# 创建你的 Agent
chat_agent = Agent(
    name="Assistant",
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful AI assistant.",
    add_datetime_to_context=True,
    markdown=True,
)
 
# 配置 AgentOS，添加 AGUI 接口
agent_os = AgentOS(
    agents=[chat_agent],
    interfaces=[AGUI(agent=chat_agent)],  # ← 这是关键
)
app = agent_os.get_app()
 
if __name__ == "__main__":
    agent_os.serve(app="basic:app", reload=True, port=9001)
启动后，AG-UI 接口会暴露 POST /agui 端点，前端可以通过这个端点与 Agent 交互。

方式二：使用自定义 FastAPI 应用
如果你需要更多控制，可以传入自己的 FastAPI 实例：

from agno.agent import Agent
from agno.os import AgentOS
from fastapi import FastAPI
 
# 创建自定义 FastAPI 应用
app = FastAPI(title="My Agent App", version="1.0.0")
 
# 添加自定义路由
@app.get("/")
async def home():
    return {"message": "Welcome to my Agent!"}
 
# 创建 Agent
my_agent = Agent(name="My Agent")
 
# 使用 base_app 参数传入你的 FastAPI 实例
agent_os = AgentOS(
    agents=[my_agent],
    base_app=app,  # ← 传入自定义应用
)
app = agent_os.get_app()
 
if __name__ == "__main__":
    agent_os.serve(app="custom:app", reload=True)
AG-UI 接口配置选项
AGUI 接口支持以下参数：

agent: 要暴露的 Agent
team: 要暴露的 Team（与 agent 二选一）
prefix: 路由前缀（默认空字符串 ""）
tags: 路由标签（默认 ["AGUI"]）
例如，指定自定义前缀：

AGUI(agent=chat_agent, prefix="/chat/v1", tags=["Chat"])
关于前端
AG-UI 是一个前端聊天组件协议，它期望端点位于特定路径。你可以使用任何前端框架来调用 POST /agui 端点，传入 RunAgentInput 负载，并接收编码后的 BaseEvent 对象流。

查看更多示例：
AgentOS FastAPI 运行时 - 了解运行时架构
通道接口 - 了解 AG-UI 协议详情
AGUI 示例集合 - cookbook 中的实战案例
agno怎样 使用ModelScope API

GLM 4.7

用户问的是"agno怎样使用ModelScope API"。这是一个关于如何在agno框架中使用ModelScope（魔搭社区）API的具体问题。
我需要查找一下agno框架中关于ModelScope API的使用方法。让我先搜索相关文档和代码实现。

文档搜索完成
ModelScope API 使用配置
网络搜索完成
agno ModelScope API integration
apipie.ai
mintlify.com
docs.agentops.ai
docs.agno.com
github.com
www.klavis.ai
结构获取完成
cookbook/92_integrations

从搜索结果来看，我没有找到关于ModelScope API的直接使用说明。让我进一步搜索：
网络搜索完成
ModelScope OpenAI兼容API endpoint
modelscope.cn
mastra.ai
github.com
lobehub.com
api.ncloud-docs.com
modelscope.cn
结构获取完成
libs/agno
已查看文件大纲
libs/agno/agno/models/openai.py

看来我需要找到正确的文件路径。让我重新查找OpenAI相关的模型文件。
结构获取完成
libs/agno/agno/models

很好，现在我找到了OpenAI相关的文件。让我查看一下OpenAI的chat.py文件，看看如何配置自定义的base_url和api_key，这样就可以了解如何配置ModelScope API了。
已查看文件大纲
libs/agno/agno/models/openai/chat.py

太好了！现在我找到了OpenAIChat类的详细信息。从代码中我可以看到：
结构获取完成
cookbook/90_models

用户问的是"agno怎样使用ModelScope API"。
在 agno 中使用 ModelScope API 非常简单，因为它提供了 OpenAI 兼容的接口。你只需要使用 OpenAIChat 模型类并配置正确的参数即可。

基本用法
import os
from agno.agent import Agent
from agno.models.openai import OpenAIChat
 
# 方法1：直接配置
agent = Agent(
    model=OpenAIChat(
        id="Qwen/Qwen2.5-Coder-32B-Instruct",  # ModelScope 模型 ID
        api_key="your-modelscope-api-token",  # 你的 ModelScope token
        base_url="https://api-inference.modelscope.cn/v1/"  # ModelScope API 端点
    ),
    markdown=True
)
 
# 方法2：使用环境变量
os.environ["OPENAI_API_KEY"] = "your-modelscope-api-token"
os.environ["OPENAI_API_BASE"] = "https://api-inference.modelscope.cn/v1/"
 
agent = Agent(
    model=OpenAIChat(id="Qwen/Qwen2.5-Coder-32B-Instruct"),
    markdown=True
)
 
# 使用 agent
agent.print_response("你好，请介绍一下你自己", stream=True)
关键配置参数
查看 
OpenAIChat 类L33-L80 的实现，这些参数是核心：

参数	说明	ModelScope 对应值
id	模型 ID	如 Qwen/Qwen2.5-Coder-32B-Instruct
api_key	API 密钥	从 ModelScope 控制台 获取
base_url	API 端点	https://api-inference.modelscope.cn/v1/
前置条件
在使用前需要：

注册 ModelScope 账号：访问 ModelScope
绑定阿里云账号并完成实名认证（必须步骤）
获取 API Token：在 Access Token 页面 生成
完整示例
import os
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
 
# 配置环境变量（推荐做法）
os.environ["OPENAI_API_KEY"] = "your-modelscope-api-token"
os.environ["OPENAI_API_BASE"] = "https://api-inference.modelscope.cn/v1/"
 
# 创建带搜索功能的 Agent
agent = Agent(
    model=OpenAIChat(id="Qwen/Qwen2.5-Coder-32B-Instruct"),
    description="你是一个乐于助人的 AI 助手",
    tools=[DuckDuckGoTools()],  # 添加网络搜索工具
    show_tool_calls=True,
    markdown=True
)
 
# 运行 Agent
agent.print_response("今天有什么科技新闻？", stream=True)
常见问题
401 错误：检查 API token 是否正确，是否绑定了阿里云账号
模型不可用：确认模型 ID 格式正确，使用完整的 namespace/model-name 格式
响应为中文：某些模型默认返回中文，这是正常现象
更多模型提供方的配置方法，可以参考 模型提供方系统 文档。
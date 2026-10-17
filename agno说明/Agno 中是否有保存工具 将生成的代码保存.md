Agno 中是否有保存工具 将生成的代码保存

GLM 5.1

The user is asking whether Agno has a tool for saving generated code. They want to know if there's a "save" or "file write" tool in Agno's toolkit system that can save generated code to files.
结构获取完成
libs/agno/agno/tools

I can see there are several relevant files:
文件查看完成
libs/agno/agno/tools/file_generation.py
文件查看完成
libs/agno/agno/tools/local_file_system.py
文件查看完成
libs/agno/agno/tools/file.py

Now I have a good understanding of the available tools. Let me also quickly check the `FileTools` class for write capabilities.
文件查看完成
libs/agno/agno/tools/file.py

Now I have a clear picture. Agno provides multiple tools for saving generated code. Let me summarize:
有的。Agno 提供了多个工具可以将生成的代码保存到文件，根据你的使用场景选择合适的：

1. FileTools — 最推荐，功能最全
这是最完整的文件操作工具包，支持在指定目录下保存、读取、替换文件内容：

from agno.tools.file import FileTools
 
agent = Agent(
    tools=[FileTools(base_dir=Path("./output"))],
)
核心能力：

save_file — 将内容保存到指定路径（默认启用）
replace_file_chunk — 替换文件中的部分内容（精确修改代码）
read_file / list_files / search_files / search_content — 读取和搜索
详见 
file.pyL59-L126

2. LocalFileSystemTools — 轻量写入
更简洁的方案，专注于将内容写入本地文件：

from agno.tools.local_file_system import LocalFileSystemTools
 
agent = Agent(
    tools=[LocalFileSystemTools(target_directory="./output", default_extension="py")],
)
只有一个 write_file 方法，接受 content、filename、directory、extension 参数。详见 
local_file_system.pyL9-L76

3. FileGenerationTools — 结构化文件生成
适合生成 JSON、CSV、PDF、TXT 等结构化文件，支持指定输出目录：

from agno.tools.file_generation import FileGenerationTools
 
agent = Agent(
    tools=[FileGenerationTools(output_directory="./output")],
)
详见 
file_generation.pyL27-L63

如果你的场景是"Agent 生成了代码，想保存成 .py 文件"，推荐使用 FileTools，它既能保存完整文件，又能做增量替换——对代码迭代场景非常友好。

想进一步了解工具包系统的全貌，可以看看：

工具包系统
Agent 核心类



AgentOS支持传统中间件方式拦截响应吗

支持，但以 FastAPI 原生中间件机制为主，而非自创的中间件抽象。

当前内置中间件
AgentOS 基于 FastAPI 构建，内置了两个 BaseHTTPMiddleware 子类，它们构成标准中间件管道：

中间件	位置	职责
JWTMiddleware	
jwt.pyL1-L80	认证 + RBAC 范围检查，可拦截请求并直接返回 401/403 响应
TrailingSlashMiddleware	
trailing_slash.pyL6-L27	归一化路径尾部斜杠，修改 request.scope 后透传
管道组装在 
app.pyL848-L881 的 _build_fastapi_app() 中，执行顺序为 CORS → JWT → TrailingSlash。

如何拦截响应
由于底层是标准 Starlette BaseHTTPMiddleware，你完全可以通过 call_next 获取响应并改写：

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
 
class MyResponseInterceptor(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        # 在这里读取/修改响应体、添加头部等
        response.headers["X-Custom"] = "intercepted"
        return response
将其注入 AgentOS 有两种方式：

方式一：通过 base_app 参数传入已配置中间件的 FastAPI 实例

from fastapi import FastAPI
from agno.os import AgentOS
 
base_app = FastAPI()
base_app.add_middleware(MyResponseInterceptor)
 
app = AgentOS(base_app=base_app, ...)
方式二：直接在 AgentOS 创建后追加

app = AgentOS(...)
app.fastapi_app.add_middleware(MyResponseInterceptor)
需要注意的局限
BaseHTTPMiddleware 的流式响应问题：Starlette 的 BaseHTTPMiddleware 在处理 SSE/WebSocket 流式响应时存在已知限制——call_next 会缓冲整个响应体。如果你的 Agent 使用流式输出（streaming），中间件拦截响应体可能会导致延迟或中断。对于流式场景，建议使用原生 ASGI 中间件。

Agent 层面另有拦截机制：如果你想在 Agent 生成响应的层面做拦截（而非 HTTP 层面），Agno 提供了 Guardrails 和 Hooks 系统，可以拦截/改写 Agent 的输入输出，语义上更贴近"业务中间件"。

总结：AgentOS 没有发明自己的中间件抽象，而是直接依赖 FastAPI/Starlette 的标准中间件机制。这既是优点（标准、可组合），也是需要注意的地方（流式场景需谨慎）。如果你的拦截目标是 Agent 的逻辑输出而非 HTTP 响应，Guardrails/Hooks 是更合适的选择。
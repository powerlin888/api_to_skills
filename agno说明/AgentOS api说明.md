AgentOS api说明

GLM 4.7

用户遇到了 AgentOS 应用入口的问题，配置 http://localhost:9001 报错，需要 AgentOS API 说明。
我需要先了解一下项目中 AgentOS 的具体实现，以便准确回答你的问题。让我查看一下相关代码。

结构获取完成
libs/agno

我看到有 `agno/os/` 目录，这应该就是 AgentOS 的实现。让我查看这个目录的结构。
结构获取完成
libs/agno/agno/os

很好，我看到了 AgentOS 的核心文件。让我查看 `app.py` 和 `router.py` 来了解 API 接口。
已查看文件大纲
libs/agno/agno/os/app.py

好的，现在我看到了 AgentOS 的核心类。让我看看 router.py 来了解 API 路由的结构。
已查看文件大纲
libs/agno/agno/os/router.py

现在让我看看 agents router 来了解具体的 API 接口。
已查看文件大纲
libs/agno/agno/os/routers/agents/router.py

让我查看一下具体的路由定义，看看有哪些 API 端点。
文件查看完成
libs/agno/agno/os/routers/agents/router.py

好的，我看到了一个关键的 API 端点 `/agents/{agent_id}/runs`。让我继续查看更多的路由定义。
文件查看完成
libs/agno/agno/os/router.py

现在我需要先查看 settings.py 文件，了解 AgentOS 的配置选项和端口设置。这将有助于诊断用户遇到的端口配置问题。
文件查看完成
libs/agno/agno/os/settings.py

现在我有了足够的信息来回答用户的问题。让我搜索一下文档中关于 AgentOS FastAPI 运行时的内容。
文档搜索完成
AgentOS FastAPI 运行时 API

用户在问 AgentOS 的 API 说明，因为他们在访问 http://localhost:9001 时遇到了各种报错。让我分析一下我看到的代码信息：
AgentOS API 使用指南
你的问题很明确 - 访问 http://localhost:9001 时报错。AgentOS 默认会自动生成 Swagger 文档，你只需要访问正确的路径。

核心问题诊断
首先确认基础端点：

Swagger UI（交互式文档）：http://localhost:9001/docs
ReDoc（静态文档）：http://localhost:9001/redoc
配置信息：http://localhost:9001/config
健康检查：http://localhost:9001/health
如果这些都无法访问，通常是认证或配置问题。

主要 API 端点结构
根据 AgentOS FastAPI 运行时 和代码实现，核心端点如下：

1. 系统配置类（Core）

GET /config         - 获取完整系统配置
GET /health         - 健康检查
2. Agent 操作类（Agents）

POST /agents/{agent_id}/runs    - 创建 Agent 运行
  参数：
    - message (str, 必填): 输入消息
    - stream (bool, 默认 true): 是否流式输出
    - session_id (str, 可选): 会话 ID
    - user_id (str, 可选): 用户 ID
    - files (UploadFile[], 可选): 文件上传（图片、音频、视频、文档）
    - version (str, 可选): Agent 版本
    - background (bool, 可选): 后台运行
 
POST /agents/{agent_id}/continue  - 继续 Agent 运行
GET  /agents/{agent_id}/runs     - 获取 Agent 运行历史
3. Team 协作类

POST /teams/{team_id}/runs    - 创建 Team 运行
GET  /teams                   - 列出所有 Teams
4. Workflow 工作流类

POST /workflows/{workflow_id}/runs    - 执行工作流
GET  /workflows                       - 列出所有工作流
5. 知识库管理

GET    /knowledge           - 列出知识库
POST   /knowledge/{id}/search   - 搜索知识
6. 会话与记忆

GET    /sessions            - 获取会话列表
DELETE /sessions/{id}       - 删除会话
认证配置（关键）
从 
settings.pyL26-L27 可知，你需要配置以下环境变量之一：

方式 1：API Key 认证

os.environ["OS_SECURITY_KEY"] = "your-secret-key"
方式 2：JWT 认证

from agno.os import AgentOS, AuthorizationConfig
 
agent_os = AgentOS(
    agent=agent,
    authorization=True,
    authorization_config=AuthorizationConfig(
        # JWT 配置
    )
)
设置后，所有请求需要携带认证头：

# API Key 方式
curl -H "Authorization: Bearer your-secret-key" http://localhost:9001/config
 
# JWT 方式  
curl -H "Authorization: Bearer <jwt_token>" http://localhost:9001/config
快速诊断步骤
访问文档页

# 打开浏览器访问
http://localhost:9001/docs
检查健康状态

curl http://localhost:9001/health
查看配置信息

curl http://localhost:9001/config
禁用文档（如果需要）

from agno.os import AgentOS
 
agent_os = AgentOS(
    agent=agent,
    settings=AgnoAPISettings(docs_enabled=False)
)
CORS 配置
如果从其他域名访问，需要配置 CORS：
settings.py#L33-L41L33-L41

os.environ["CORS_ORIGIN_LIST"] = "http://localhost:3000,https://yourdomain.com"
你的代码调整建议
from agno.os import AgentOS, AgnoAPISettings
 
# 设置认证密钥
os.environ["OS_SECURITY_KEY"] = "your-secret-key"
 
# 或禁用认证用于测试
agent_os = AgentOS(
    agent=agent,
    settings=AgnoAPISettings(
        docs_enabled=True,
        os_security_key=None  # 测试时禁用认证
    )
)
 
app = agent_os.get_app()
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
下一步建议
先访问 AgentOS FastAPI 运行时 了解完整架构
查看 认证与中间件 配置正确的认证方式
使用 /docs 页面交互式测试 API
如果还有问题，检查 
app.pyL657-L667 中的 get_app() 方法配置
你的问题很可能是因为没有配置认证或者直接访问了根路径而不是文档端点。先试试 http://localhost:9001/docs 吧。




提出后续问题...

GLM 4.7
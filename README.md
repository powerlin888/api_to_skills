# 无代码编程智能体平台

专门解决各种专用编程环境（工业机器人、数控机床、PLC等）编程问题的无代码平台。用户上传编程指南PDF，平台自动生成Claude Code体系的Skills和Reference，并基于agno框架配置编程智能体进行对话。

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│  前端 (Vue3 + TypeScript + Pinia)                        │
│  首页│论坛│登录│PDF上传│智能体配置│对话│模型配置        │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP/REST + SSE
┌──────────────────────┴───────────────────────────────────┐
│  后端 (Python + FastAPI + uvicorn)                       │
│  ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌─────────┐ │
│  │ 转换引擎   │ │ 智能体管理 │ │ 用户社区 │ │ Skills  │ │
│  └──────┬─────┘ └──────┬─────┘ └────┬─────┘ │ 注册    │ │
│         │              │            │        │         │ │
│  ┌──────┴──────────────┴────────────┴────────┴─────────┐ │
│  │  数据访问层 (SQLAlchemy + asyncpg)                   │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
         │                    │                │
    PostgreSQL           agno框架         LanceDB/PgVector
    (用户/智能体/        (Agent/Skills    (向量检索/
     论坛数据)           /Knowledge)      RAG)
```

## 核心功能

### 1. PDF编程指南转换引擎
- 上传PDF → spaCy-layout版面解析(基于IBM Docling) → LLM结构分析 → Skills/Reference生成 → 验证
- **分段处理**：大文档按Markdown标题自动分段，逐段LLM分析后合并去重
- **LLM调用重试**：指数退避(1s→2s→4s)+随机抖动，最多3次重试，覆盖网络错误/服务端错误/解码错误
- **去重机制**：SHA-256哈希精确匹配 + Jaccard相似度检查（阈值95%）
- 完全重复自动关联已有Skills群，相似重复提示用户确认
- 转换管道状态机：PENDING → PARSING → DEDUP_CHECK → ANALYZING → GENERATING → VALIDATING → COMPLETED/FAILED/DUPLICATE

### 2. 编程智能体配置与管理
- 基于agno框架创建Agent，加载LocalSkills从文件系统读取Skills
- 支持三种模型提供商：魔搭社区(ModelScope)、OpenAI兼容API、本地模型
- SSE流式对话，实时Token推送
- 模型调用次数、Token用量、延迟等指标统计

### 3. 用户界面
- **首页/论坛**：无需登录即可浏览
- **PDF上传页**：拖拽/点击上传，5阶段转换进度展示，去重确认弹窗
- **智能体配置页**：Skills群多选 + 模型配置 + 创建智能体
- **对话页**：SSE流式对话 + Markdown渲染 + 指标展示
- **模型配置页**：配置各类型模型的API Key/Base URL
- **社区页**：签到 + 发帖 + 点赞 + 评论

### 4. 用户社区
- 注册/登录（JWT认证，access 2h + refresh 7d）
- 密码错误5次锁定15分钟
- 每日签到+10积分
- 论坛发帖/点赞(toggle)/评论

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue3 + TypeScript + Vite + Pinia + Axios |
| 后端 | Python 3.12+ + FastAPI + uvicorn |
| 智能体 | agno (Agent/Skills/Knowledge) |
| 数据库 | PostgreSQL 15 |
| 向量库 | LanceDB / PgVector |
| PDF转MD | spaCy-layout (IBM Docling + 版面分析) |
| LLM调用 | openai SDK (兼容ModelScope/OpenAI/DeepSeek) |
| 认证 | JWT (python-jose) + bcrypt + AES-256 |

## 项目结构

```
backend/
├── app/
│   ├── core/                    # 核心模块
│   │   ├── config.py            # pydantic-settings全局配置(绝对路径)
│   │   ├── database.py          # SQLAlchemy异步引擎
│   │   ├── security.py          # 密码/JWT/AES安全
│   │   └── auth.py              # 认证中间件
│   ├── shared/
│   │   └── dao/
│   │       ├── models.py        # 11张表ORM模型
│   │       ├── dao.py           # CRUD DAO
│   │       └── init_db.py       # 数据库初始化+种子数据
│   ├── modules/
│   │   ├── conversion/          # PDF转换引擎
│   │   │   ├── parser.py        # PDF解析(spaCy-layout/Docling)
│   │   │   ├── dedup_checker.py # 去重检查(SHA-256+Jaccard)
│   │   │   ├── planner.py       # LLM规划(openai SDK+分段处理)
│   │   │   ├── generator.py     # Skills文件生成
│   │   │   ├── validator.py     # Skills验证
│   │   │   ├── service.py       # 转换引擎总服务(独立db session后台任务)
│   │   │   └── router.py        # API路由
│   │   ├── agent_mgmt/          # 智能体管理
│   │   ├── community/           # 用户社区
│   │   └── skills_registry/     # Skills注册与检索
│   └── main.py                  # FastAPI主入口
├── test_conversion.py           # 独立转换测试脚本
├── data/
│   ├── pdfs/                    # PDF和MD文件存储
│   └── skills/                  # Skills文件输出
├── pyproject.toml
└── .env                         # 环境配置

frontend/
├── src/
│   ├── api/                     # API封装
│   ├── stores/                  # Pinia状态管理
│   ├── views/                   # 页面组件
│   ├── layouts/                 # 布局组件
│   └── router/                  # 路由(首页/论坛公开,其他需登录)
├── package.json
└── vite.config.ts
```

## 快速开始

### 前置条件
- Python 3.12+ + Miniconda
- Node.js 20+
- PostgreSQL 15

### 本地开发

```bash
# 1. 创建conda环境并安装依赖
conda create -n api_to_skills python=3.12
conda activate api_to_skills
cd backend
pip install -e .
pip install "bcrypt<4.1"  # passlib兼容性

# 2. 配置环境
cp .env.example .env
# 编辑 .env，填入 LLM_DEFAULT_API_KEY

# 3. 初始化数据库(确保PostgreSQL已启动)
python -m app.shared.dao.init_db

# 4. 启动后端(注意：不要用--reload，后台任务会丢失)
uvicorn app.main:app --port 8000 --log-level info

# 5. 启动前端
cd frontend
npm install
npm run dev
```

### 访问地址
- 前端：http://localhost:5173
- 后端API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 公开与需认证页面
| 页面 | 是否需要登录 |
|------|-------------|
| 首页 | 否 |
| 论坛 | 否 |
| 登录/注册 | 否 |
| PDF上传 | 是 |
| 智能体配置 | 是 |
| 对话 | 是 |
| 模型配置 | 是 |

## 独立模块测试

### PDF→MD 解析和 MD→Skills 生成

```bash
conda activate api_to_skills
cd backend

# 列出已上传的PDF文件
python test_conversion.py list

# 只测试PDF→MD解析
python test_conversion.py parse data/pdfs/xxx.pdf

# 只测试MD→Skills规划(需要LLM API Key)
python test_conversion.py plan data/pdfs/xxx.md

# 完整流程: PDF→MD→Skills
python test_conversion.py full data/pdfs/xxx.pdf

# 完整流程但跳过LLM(只到MD)
python test_conversion.py full data/pdfs/xxx.pdf --no-llm
```

**注意**：大PDF文件(>5MB)解析可能需要较长时间，脚本无超时限制。解析产物保存在同目录下同名`.md`文件。

## 数据库

### 11张核心表

| 表 | 用途 |
|----|------|
| users | 用户信息（邮箱/密码/角色/积分） |
| pdf_guides | 上传的编程指南（含content_hash去重） |
| skill_groups | Skills群（一对多关联Skills） |
| skills | 单个Skill元数据 |
| agents | 智能体配置（模型/Skills群/API Key加密） |
| agent_metrics | 模型调用指标统计 |
| conversion_tasks | 转换任务（含去重状态dedup_pending_info） |
| check_ins | 签到记录 |
| posts | 论坛帖子 |
| comments | 评论 |
| post_likes | 点赞 |

## API接口

### 认证
- `POST /api/auth/register` — 注册
- `POST /api/auth/login` — 登录
- `POST /api/auth/refresh` — 刷新Token
- `GET /api/auth/me` — 当前用户

### PDF转换
- `POST /api/pdf/upload` — 上传PDF（multipart）
- `GET /api/pdf/tasks/{id}` — 查询转换状态
- `GET /api/pdf/tasks` — 任务列表
- `POST /api/pdf/tasks/{id}/confirm-dedup` — 确认去重（continue/cancel）
- `GET /api/pdf/guides/{id}/skills` — 获取指南的Skills群

### 智能体
- `POST /api/agent/create` — 创建智能体
- `GET /api/agent/{id}` — 获取智能体
- `PUT /api/agent/{id}` — 更新智能体
- `DELETE /api/agent/{id}` — 删除智能体
- `GET /api/agent/list` — 智能体列表
- `GET /api/agent/skill-groups` — 可用Skills群
- `POST /api/chat/{id}` — SSE流式对话
- `GET /api/chat/{id}/metrics` — 对话指标

### 社区(浏览无需登录,写操作需登录)
- `GET /api/community/posts` — 帖子列表
- `POST /api/community/check-in` — 签到
- `POST /api/community/posts` — 发帖
- `POST /api/community/posts/{id}/like` — 点赞(toggle)
- `POST /api/community/posts/{id}/comments` — 评论

### Skills(浏览无需登录)
- `GET /api/skills/groups` — Skills群列表
- `GET /api/skills/groups/{id}` — Skills群详情
- `GET /api/skills/search?keyword=` — 搜索Skills
- `POST /api/skills/scan` — 扫描同步(需登录)

### 模型配置
- `GET /api/model/providers` — 可用提供商
- `POST /api/model/config` — 保存配置

## 去重机制

转换管道在PDF解析后、LLM分析前插入去重检查阶段：

1. **SHA-256精确匹配**：计算Markdown内容哈希，与同用户已有指南比对
2. **Jaccard相似度**：哈希不匹配时，与候选集（最多50个）比较文本相似度
3. **完全重复**（哈希匹配）→ 自动标记DUPLICATE，关联已有Skills群
4. **相似重复**（相似度≥95%）→ 暂停管道，弹窗让用户选择继续生成或使用已有
5. **降级策略**：相似度计算超时(10s)或异常时，跳过去重直接继续生成

## LLM分段处理与重试机制

大文档按Markdown标题(#/##/###)自动分段：
- 每段不超过80K字符(适配DeepSeek-V4-Flash 1M上下文)
- 相邻小节自动合并减少LLM调用次数
- 各段独立调用LLM生成Skills规划
- 多段结果>5个Skills时，再调LLM合并去重
- 单段文档直接一次调用

LLM调用具备自动重试能力：
- **最大重试**：3次
- **退避策略**：指数退避(1.0s → 2.0s → 4.0s) + 随机抖动(0~0.5s)
- **覆盖异常**：网络错误(APIConnectionError/APITimeoutError)、服务端错误(HTTP 500+)、频率限制(RateLimit)、响应解码错误(UnicodeDecodeError)、HTTP传输异常

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DATABASE_URL | postgresql+asyncpg://ai:ai@localhost:5432/ai | 数据库连接 |
| JWT_SECRET | change-me-in-production | JWT签名密钥 |
| AES_KEY | 0123456789abcdef... | API Key加密密钥(32字节) |
| LLM_DEFAULT_BASE_URL | https://api-inference.modelscope.cn/v1/ | 默认LLM端点 |
| LLM_DEFAULT_API_KEY | | 默认LLM API Key(必填) |
| LLM_DEFAULT_MODEL_ID | deepseek-ai/DeepSeek-V4-Flash | 默认模型 |
| LLM_TIMEOUT_SECONDS | 60 | LLM调用超时 |
| MAX_PDF_SIZE_MB | 100 | PDF最大大小 |
| CORS_ORIGINS | http://localhost:5173,... | CORS允许源 |
| HF_ENDPOINT | https://hf-mirror.com | HuggingFace镜像(国内必填,Docling下载模型用) |

## 已知问题与注意事项

1. **uvicorn --reload 模式下后台任务丢失**：`asyncio.create_task` 创建的后台任务在reload时会丢失，生产/调试环境请使用 `uvicorn app.main:app --port 8000`（不加--reload）
2. **passlib + bcrypt>=4.2 不兼容**：需安装 `bcrypt<4.1`
3. **PDF存储路径**：config.py 基于 `__file__` 计算绝对路径，不受 cwd 影响
4. **后台任务db session**：pipeline 使用独立 db session 并手动 commit，不依赖请求的 session

## License

本项目基于 [MIT License](./LICENSE) 开源。

```
MIT License

Copyright (c) 2026 powerlin888

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

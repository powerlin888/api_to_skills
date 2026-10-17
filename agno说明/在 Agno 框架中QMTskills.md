在 Agno 框架中，Agent Skills 和 Knowledge Reference 是两个互补的概念，共同构成 Agent 的能力体系。前者提供可执行的原子能力，后者提供可检索的参考知识。根据 QMT Python API 的文档特点，可以从以下维度进行规划设计。

一、整体架构
text
qmt-agent/
├── skills/                      # Agent Skills 目录（按能力域分组）
│   ├── qmt-knowledge/           # 知识检索 Skill
│   ├── qmt-trading/             # 交易执行 Skill
│   ├── qmt-data/                # 数据获取 Skill
│   ├── qmt-options/             # 期权交易 Skill
│   ├── qmt-analysis/            # 策略分析 Skill
│   └── qmt-risk/                # 风控管理 Skill
├── references/                  # Reference 文档（供 skills 引用 + 向量库）
│   ├── api/                     # API 详细参考
│   ├── concepts/                # 重要概念说明
│   └── examples/                # 代码示例集合
└── agent.py                     # Agent 入口代码
Skill 是一个独立的文件夹，核心是 SKILL.md 文件，配合 scripts/ 脚本和 references/ 参考文档，Agent 通过渐进式加载按需获取能力。

二、规划 Agent Skills（按能力域分组）
2.1 Skill 1：知识检索 Skill（qmt-knowledge/）
元素	内容
Skill 名称	qmt-knowledge
触发词	"如何获取"、"怎样使用"、"XX API 怎么调用"、"参数含义"
用途	当用户询问 API 用法或概念时，从 Reference 知识库中检索并提供准确解答
SKILL.md 核心内容：

markdown
---
name: qmt-knowledge
description: 检索 QMT Python API 的参考文档、API 说明、参数定义和用法示例。
---

## 触发条件
用户询问以下类型问题时激活此 Skill：
- "如何获取XX数据"
- "XX函数怎么用"
- "参数XX是什么意思"
- "ContextInfo 对象有哪些方法"

## 执行流程
1. 使用 `get_skill_reference()` 工具，根据关键词在 references/ 目录下检索相关 API 文档
2. 如果检索到结果，提取对应的 API 说明、参数列表和示例代码
3. 返回格式化的回答，包含 API 签名、参数说明、返回值、示例代码
4. 如果未检索到结果，提示用户补充关键词或查阅官方文档

## 可用脚本
- `scripts/search_api.py`：根据关键词在 API 文档中模糊搜索
- `scripts/get_api_doc.py`：获取指定 API 的完整文档
2.2 Skill 2：交易执行 Skill（qmt-trading/）
元素	内容
Skill 名称	qmt-trading
触发词	"下单"、"买入"、"卖出"、"撤单"、"passorder"
用途	当 Agent 需要生成交易执行代码时调用，提供标准化的交易 API 调用模板
SKILL.md 核心内容：

markdown
---
name: qmt-trading
description: 生成 QMT 综合交易下单（passorder）的代码片段，支持股票、期货、期权等多种交易类型。
---

## 触发条件
用户请求中包含以下关键词时激活：
- "买入"、"卖出"、"下单"、"交易"
- "opType"、"orderType"、"passorder"

## 执行流程
1. 确认用户的交易方向（买入/卖出）和品种类型（股票/期货/期权）
2. 根据 OpType 映射表确定 opType 参数值
3. 根据用户指定的下单方式（股数/金额/比例）确定 orderType 参数
4. 调用 scripts/passorder_template.py 生成代码
5. 在 handlebar 上下文中展示完整示例

## 交易类型映射表
| 交易意图 | opType |
|----------|--------|
| 股票买入 | 23 |
| 股票卖出 | 24 |
| 期货开多 | 0 |
| 期货开空 | 3 |
| 期权买入开仓 | 50 |
| 期权卖出平仓 | 51 |

## 下单类型映射表
| 下单方式 | orderType |
|----------|-----------|
| 按股数/手数 | 1101 |
| 按金额 | 1102 |
| 按比例 | 1113 |

## 可用脚本
- `scripts/get_optype.py`：根据交易意图查询对应的 opType 数值
- `scripts/passorder_template.py`：生成完整的 passorder 调用代码
2.3 Skill 3：数据获取 Skill（qmt-data/）
元素	内容
Skill 名称	qmt-data
触发词	"获取行情"、"历史数据"、"财务数据"、"K线"、"分笔"
用途	当 Agent 需要生成数据获取代码时调用，提供 get_market_data、get_history_data 等函数的正确用法
SKILL.md 核心内容：

markdown
---
name: qmt-data
description: 生成 QMT 行情数据和财务数据获取的代码片段，支持 K 线、分笔、财务数据等多种数据源。
---

## 触发条件
用户请求中包含以下关键词时激活：
- "获取数据"、"行情"、"K线"、"分笔"
- "get_market_data"、"get_history_data"、"get_financial_data"

## 执行流程
1. 确认数据类型（行情/财务/历史）
2. 确认数据周期（tick/1d/1m/5m 等）
3. 确认复权方式（none/front/back 等）
4. 调用 scripts/get_data_template.py 生成代码

## 周期类型映射表
| 周期 | period 参数值 |
|------|---------------|
| 分笔 | 'tick' |
| 日线 | '1d' |
| 1分钟线 | '1m' |
| 5分钟线 | '5m' |

## 复权方式映射表
| 复权方式 | dividend_type |
|----------|---------------|
| 不复权 | 'none' |
| 前复权 | 'front' |
| 后复权 | 'back' |

## 注意事项
- get_market_data() 和 get_history_data() 的区别：前者更灵活，返回 DataFrame；后者简化，返回 dict
- 使用财务数据前必须通过数据管理补充本地数据

## 可用脚本
- `scripts/get_market_data_template.py`：生成 get_market_data 调用代码
- `scripts/get_financial_data_template.py`：生成财务数据调用代码
- `scripts/parse_period.py`：解析用户输入的数据周期
2.4 Skill 4：期权交易 Skill（qmt-options/）
元素	内容
Skill 名称	qmt-options
触发词	"期权"、"隐含波动率"、"BS模型"、"组合策略"、"行权"
用途	当 Agent 需要生成期权相关的交易或定价代码时调用
2.5 Skill 5：策略分析 Skill（qmt-analysis/）
元素	内容
Skill 名称	qmt-analysis
触发词	"回测"、"净值"、"持仓分析"、"性能指标"
用途	当 Agent 需要分析策略绩效或生成回测代码时调用
2.6 Skill 6：风控管理 Skill（qmt-risk/）
元素	内容
Skill 名称	qmt-risk
触发词	"止损"、"止盈"、"风控"、"仓位管理"
用途	当 Agent 需要生成止损/止盈代码或管理仓位时调用
三、规划 Reference 文档（供 Skills 引用 + 向量库）
3.1 Reference 目录结构
text
references/
├── api/                                  # API 详细参考
│   ├── passorder.md                      # passorder 函数完整文档
│   ├── get_market_data.md                # get_market_data 函数文档
│   ├── get_market_data_ex.md             # 第二版行情数据获取
│   ├── get_history_data.md               # 历史行情数据获取
│   ├── get_financial_data.md             # 财务数据获取
│   ├── order_functions.md                # 交易简化函数（order_*）
│   ├── futures_functions.md              # 期货专用函数
│   ├── options_functions.md              # 期权专用函数
│   ├── algo_passorder.md                 # 算法交易下单
│   └── smart_algo_passorder.md           # 智能算法交易
├── concepts/                             # 重要概念说明
│   ├── bar_concept.md                    # Bar 和 K 线概念
│   ├── init_handlebar.md                 # init 和 handlebar 运行机制
│   ├── quick_trade.md                    # 快速交易与非快速交易的区别
│   ├── contextinfo_object.md             # ContextInfo 对象详解
│   ├── trading_mechanism.md              # 交易函数运行机制
│   ├── dividend_types.md                 # 复权方式详解
│   └── period_types.md                   # 周期类型枚举
├── examples/                             # 代码示例集合
│   ├── basic_strategy.py                 # 基础策略示例
│   ├── moving_average.py                 # 均线策略示例
│   ├── options_strategy.py               # 期权策略示例
│   └── data_retrieval.py                 # 数据获取示例
└── appendix/                             # 附录内容
    ├── operation_types.md                # OpType 完整枚举表（23/24/50/51等）
    ├── order_types.md                    # OrderType 完整枚举表
    ├── price_types.md                    # PrType 报价类型枚举表
    ├── market_codes.md                   # 市场代码（SH/SZ/IF 等）
    ├── status_codes.md                   # 委托状态/成交状态枚举
    └── financial_fields.md               # 财务数据字段对照表
3.2 Reference 文档的两种用途
作为 Skills 的引用文档：Skill 在执行时可以通过 get_skill_reference() 工具按需加载指定的参考文档。例如 qmt-trading Skill 执行时，可以引用 api/passorder.md 获取参数详细说明，Agent 只在需要时才读取完整文档。

构建向量知识库（RAG）：将所有 reference 文档向量化存储到 Agno 的 Knowledge 系统中，Agno 支持 ChromaDB、LanceDB、PgVector、Milvus 等 20+ 种向量数据库集成。当用户提问时，Agent 可以在 Knowledge 中检索相关参考内容，增强回答的准确性。

3.3 Reference 文档格式示例（以 api/passorder.md 为例）
markdown
# passorder 综合交易下单

## 函数签名
```python
passorder(opType, orderType, accountid, orderCode, prType, modelprice, volume[, strategyName, quickTrade, userOrderId], ContextInfo)
参数列表
参数	类型	必填	说明
opType	int	是	操作类型：23=股票买入，24=股票卖出，0=期货开多...
orderType	int	是	下单方式：1101=股/手，1102=金额...
accountid	string	是	资金账号
orderCode	string	是	合约代码，如 '000001.SZ'
prType	int	是	报价类型：5=最新价，11=指定价
modelprice	float	是	指定价（prType=11 时有效）
volume	int	是	数量或金额
strategyName	string	否	自定义策略名
quickTrade	int	否	快速交易：0/1/2
userOrderId	string	否	用户自定义委托ID
ContextInfo	object	是	Python 策略上下文
示例
python
def handlebar(ContextInfo):
    # 股票买入：最新价买入 100 股
    passorder(23, 1101, 'test', '000001.SZ', 5, -1, 100, ContextInfo)
    # 期货开多：指定价 3000 买入 10 手
    passorder(0, 1101, 'test', 'IF2003.IF', 11, 3000, 10, ContextInfo)
相关文档
交易类型枚举表

下单类型枚举表
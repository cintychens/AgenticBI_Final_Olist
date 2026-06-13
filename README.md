# Agentic BI Final Olist

Agentic BI-Driven Multi-Table E-Commerce Operations Analysis and Decision Intelligence System.

## 项目背景

随着电商平台交易规模不断扩大，运营团队每天都会面对订单、支付、物流、商品、卖家、客户评价等多来源数据。传统 BI 系统通常依赖固定报表和人工 SQL 查询，非技术业务人员很难快速完成跨表分析，也难以及时把销售趋势、配送异常、差评原因和运营策略联系起来。

本项目基于 Brazilian E-Commerce Public Dataset by Olist 构建，模拟巴西跨境电商平台 Olist 的真实运营分析场景。数据集中包含订单、商品、卖家、客户、支付、配送、评论和地理位置等多张业务表，适合用于验证多表查询、预聚合视图优化、自然语言分析、预测建模、评论洞察和决策智能等 Agentic BI 能力。

## 项目动机

本项目的目标不是只做一个静态 Dashboard，而是构建一个面向业务人员的智能分析系统：用户可以直接用自然语言提问，系统自动判断分析意图，选择合适的数据表或预聚合视图，生成 SQL 查询结果、可视化图表、预测结果和可执行的商业建议。

项目重点解决以下问题：

- 降低业务分析门槛：让没有 SQL 背景的用户也能完成 GMV、配送、支付、品类、卖家和评论分析。
- 提升多表分析效率：通过 MySQL 预聚合视图减少高频 JOIN 和聚合查询的重复计算。
- 强化分析深度：覆盖描述性分析、诊断性分析、预测性分析和规范性分析四类业务需求。
- 引入多智能体协作：由数据分析 Agent、可视化 Agent、NLP 评论洞察 Agent、预测 Agent、决策智能 Agent 和协调器 Agent 分工协作。
- 支持业务决策闭环：不仅展示“发生了什么”，还进一步解释“为什么发生”，预测“接下来可能怎样”，并给出“应该怎么做”的运营建议。

本项目基于 Brazilian E-Commerce Public Dataset by Olist 构建一个多智能体协作的电商运营分析系统。系统支持自然语言提问，自动完成多表查询、预聚合视图调度、销售预测、评论洞察、可视化生成、What-if 模拟和决策建议输出，面向非技术业务人员提供完整的 Agentic BI 体验。

## 1. 项目功能

- 自然语言业务问答
- MySQL 多表查询与预聚合视图优先查询
- 描述性分析：GMV、订单量、客单价、州销售、品类销售、支付方式
- 诊断性分析：配送延迟、低评分卖家、差评品类原因、重量/尺寸与运费关系
- 预测性分析：基于 Prophet 预测未来 6 周销售趋势，并展示置信区间
- 规范性分析：结合销售、物流、评论、预测和 What-if 结果生成运营建议
- NLP 评论洞察：情感分析、关键词、正负面词云、差评主题
- What-if 模拟：Top 20 高差评卖家移除后的平台评分变化
- 异常检测：月度 GMV 异常、州订单骤降、差评率突升
- 图表保存：可视化 Agent 自动生成并保存图表文件
- Streamlit 仪表板：左侧对话区 + 右侧 KPI 和图表展示区
- 多轮上下文记忆：通过 Memory Agent 保存最近会话上下文

## 2. 项目目录结构

```text
AgenticBI_Final_Olist/
├── agents/                         # 多 Agent 定义
│   ├── coordinator_agent.py         # 协调器 Agent
│   ├── data_analysis_agent.py       # 数据分析 Agent，负责 SQL 与视图调度
│   ├── visualization_agent.py       # 可视化 Agent，负责图表生成与保存
│   ├── review_insight_agent.py      # 评论洞察 Agent
│   ├── decision_agent.py            # 决策智能 Agent
│   ├── what_if_agent.py             # What-if 模拟 Agent
│   ├── memory_agent.py              # 会话记忆 Agent
│   ├── narrative_agent.py           # 最终中文回答生成 Agent
│   └── llm_agent.py                 # LLM 调用与问题分类
├── config/
│   ├── data_dictionary.py           # 数据字典：基础表 + 预聚合视图
│   └── settings.py                  # LLM 配置
├── dashboard/
│   └── dashboard_app.py             # Streamlit Web 页面
├── data/                            # Olist 原始 CSV 数据
├── models/
│   └── forecast_model.py            # Prophet 预测模型
├── outputs/
│   └── charts/                      # 自动保存的图表文件
├── utils/
│   ├── db.py                        # MySQL 连接与查询工具
│   ├── import_all_data.py           # CSV 导入 MySQL
│   ├── preaggregation_views.sql     # 预聚合视图创建 SQL
│   ├── refresh_preaggregations.py   # 一键刷新预聚合视图
│   └── performance_test.py          # 原始 JOIN vs 预聚合视图性能对比
├── app.py                           # 项目入口
├── requirements.txt
└── README.md
```

## 3. 数据集

指定数据集：Brazilian E-Commerce Public Dataset by Olist。

项目使用 9 张基础表：

- `orders`
- `order_items`
- `products`
- `customers`
- `sellers`
- `payments`
- `order_reviews`
- `geolocation`
- `product_category_name_translation`

数据覆盖订单、支付、物流、商品、卖家、客户地理位置和评论文本，适合进行多表关联分析、NLP 评论分析和运营决策支持。

## 4. 预聚合视图

为提升高频查询性能，项目在 MySQL 中创建以下预聚合视图：

| 视图 | 粒度 | 主要用途 |
|---|---|---|
| `mv_monthly_sales` | 年月 | 月度 GMV、订单量、客单价、销售趋势 |
| `mv_state_sales` | 年月 + 州 | 各州销售额、订单量、区域市场分析 |
| `mv_category_sales` | 年月 + 品类 | Top 品类销售额、品类表现 |
| `mv_delivery_perf` | 年月 + 州 | 平均配送时长、准时交付率、延迟订单 |
| `mv_seller_perf` | 年月 + 卖家 | 卖家 GMV、订单量、平均评分 |
| `mv_payment_dist` | 年月 + 支付方式 | 支付方式频率、平均分期数、支付金额 |

创建脚本：

```text
utils/preaggregation_views.sql
```

刷新脚本：

```bash
python utils/refresh_preaggregations.py
```

Data Analysis Agent 会优先使用这些 `mv_*` 视图；当问题维度无法被预聚合视图覆盖时，系统会回退到基础表进行查询，例如评论文本、重量运费散点、支付分期矩阵和异常检测等。

## 5. 多 Agent 架构

系统采用轻量级多 Agent 编排方式，由 Coordinator Agent 统一调度。各 Agent 通过共享 `state` 字典传递中间结果，并由 Memory Agent 维护多轮会话上下文。

```text
User Question
    ↓
Coordinator Agent
    ↓
Memory Agent
    ↓
Data Analysis Agent
    ↓
Forecast Agent / NLP Agent / What-if Agent
    ↓
Visualization Agent
    ↓
Decision Intelligence Agent
    ↓
Narrative Answer Agent
    ↓
Streamlit Dashboard
```

说明：项目没有直接引入 LangGraph，而是使用自定义 Coordinator + shared state dictionary + Memory Agent 实现有状态多智能体任务流。

## 6. 可视化能力

系统自动生成并展示不少于 6 类图表：

| 类型 | 当前实现 |
|---|---|
| 时间序列折线图 | 月度 GMV 趋势、Prophet 未来 6 周预测、置信区间 |
| 地理热力图 / 气泡图 | 基于 `mv_state_sales` 和 `geolocation` 的巴西州销售分布 |
| 柱状图 / 条形图 | 州销售排名、州客单价、Top 品类销售额、支付方式频率 |
| 热力图 / 矩阵图 | 支付方式 × 分期数矩阵 |
| 散点图 / 气泡图 | 商品重量 vs 运费，气泡大小表示订单量，颜色区分订单状态 |
| 词云 / 文本主题图 | 好评词云、差评词云 |
| 异常检测图 | 月度 GMV 异常、州订单骤降、差评率突升 |

图表文件会保存到：

```text
outputs/charts/
```

## 7. 支持的问题示例

系统至少支持以下问题：

- 2017 年 GMV 是多少？按月和各州排名的趋势怎样？
- 平台整体准时交付率是多少？哪些州延迟最严重？
- 哪种支付方式最受欢迎？平均分期数是多少？
- 产品的重量、尺寸与运费之间有什么关系？
- Top 10 差评品类及其主要差评原因是什么？
- 根据历史订单趋势，预测未来 6 周的销售额，并给出趋势解读。
- 基于全部分析结果，给出平台 3 个月内的三大优先改进策略。
- 2017 年哪个州的销售额最高？交付准时率是多少？哪种支付方式最受欢迎？
- 为什么某些州的平均配送时长显著高于全国均值？哪些卖家的差评率最高？
- 如何降低巴西东北部地区的高退货率？请给出具体的运营改进方案。
- 请自动扫描近期数据并预警异常，包括某州订单量骤降和差评率突升。

## 8. 环境要求

建议使用 Python 3.10 或 3.11。

安装依赖：

```bash
pip install -r requirements.txt
```

主要依赖：

- Streamlit
- Pandas / NumPy
- SQLAlchemy / PyMySQL
- Plotly
- Prophet
- OpenAI SDK
- WordCloud
- TextBlob / NLTK
- scikit-learn
- Kaleido

## 9. 配置说明

### 9.1 MySQL 配置

数据库连接在 `utils/db.py` 中读取环境变量：

```text
MYSQL_HOST
MYSQL_PORT
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
```

默认配置：

```text
host     = localhost
port     = 3306
user     = root
password = 123456
database = agentic_bi_olist
```

建议在本地设置环境变量，而不是把真实密码写入代码。

### 9.2 LLM 配置

LLM 配置位于：

```text
config/settings.py
```

需要配置：

```python
VECTOR_API_KEY = "your-api-key"
VECTOR_BASE_URL = "your-openai-compatible-base-url"
MODEL_NAME = "gpt-4o-mini"
```


## 10. 数据导入与视图刷新

### 10.1 导入 Olist CSV

将 Kaggle 下载的 CSV 文件放入 `data/` 目录，然后执行：

```bash
python utils/import_all_data.py --replace
```

如果只是预览文件映射：

```bash
python utils/import_all_data.py
```

### 10.2 创建或刷新预聚合视图

```bash
python utils/refresh_preaggregations.py
```

### 10.3 运行性能对比

```bash
python utils/performance_test.py
```

也可以在 Streamlit 前端中通过“运行性能对比测试”快捷工具触发。

## 11. 启动项目

在项目根目录运行：

```bash
streamlit run app.py
```

默认访问：

```text
http://localhost:8501
```

## 12. Dashboard 使用方式

1. 在左侧 Conversation 面板输入业务问题。
2. 点击“发送并分析”。
3. 系统会自动完成：
   - 意图识别
   - SQL 查询
   - 预聚合视图命中或基础表回退
   - NLP 评论洞察
   - 预测分析
   - 图表生成
   - What-if 模拟
   - 决策建议
4. 右侧展示 KPI、图表和分析结果。
5. Sidebar 会显示历史问题，用于回顾最近会话。

## 13. 项目亮点

- 真实 9 表电商数据建模
- 预聚合视图优先查询策略
- 多 Agent 协作完成异构任务
- LLM 生成中文业务结论与运营建议
- Prophet 未来 6 周销售预测
- NLP 情感分析与正负面词云
- What-if 卖家下架模拟
- 异常检测与风险预警
- 支持多轮上下文问答
- 图表自动生成并保存文件


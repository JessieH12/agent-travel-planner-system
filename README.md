# 多Agent智能旅游行程规划系统

> **从零到面试** —— 企业级多Agent系统，Python + Java + Go 三语言实现，含八股文、STAR法则、面试QA全套资料。

---

## 这个项目是什么？

这是一个 **6个AI Agent协作** 的智能旅游行程规划系统。你输入预算、出发城市、日期、旅行风格，系统自动帮你规划完整行程——包括目的地推荐、航班比价、酒店匹配、每日活动安排，并且自动控制预算。

**核心亮点**:
- 6个Agent各司其职，通过 Pipeline + 并行 + 预算循环 协作
- 航班/酒店/活动 **三Agent并行搜索**，延迟降低67%
- 超预算自动触发 **渐进式降级循环**（最多3轮调整）
- **Python + Java + Go** 三语言完整实现
- 配套 **面试全套资料**（八股文 + STAR法则 + 面试QA + 架构讲解）

---

## 目录导航

| 内容 | 链接 | 说明 |
|------|------|------|
| **Python 实现** | [python/](python/) | 主力版本，FastAPI + Streamlit |
| **Java 实现** | [java/](java/) | Spring Boot 3.3 版本 |
| **Go 实现** | [golang/](golang/) | Gin + goroutine 版本 |
| **八股文** | [docs/01-八股文.md](docs/01-八股文.md) | 15个核心知识点 |
| **简历模板** | [docs/02-简历模板.md](docs/02-简历模板.md) | STAR法则 + 3种岗位模板 |
| **面试QA** | [docs/03-面试QA.md](docs/03-面试QA.md) | 34道常见面试题 |
| **架构设计** | [docs/04-架构设计详解.md](docs/04-架构设计详解.md) | 架构图 + 设计决策 |
| **代码讲解** | [docs/05-代码讲解.md](docs/05-代码讲解.md) | 逐模块代码详解 |

---

## 系统架构

```
用户输入
  │
  ▼
┌────────────────┐
│ Preference     │  收集用户偏好（预算/风格/时间/禁忌）
│ Agent          │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Destination    │  推荐目的地（季节/签证/安全/性价比评分）
│ Agent          │
└───────┬────────┘
        │
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Flight Agent │  │ Hotel Agent  │  │ Activity     │  ← 三个Agent并行执行
│ (航班搜索)    │  │ (酒店搜索)    │  │ Agent(活动)  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
               ┌────────────────┐
               │ Budget Agent   │  预算校验
               └───────┬────────┘
                       │
                ┌──────┴──────┐
                │             │
             通过？         超预算？
                │             │
                ▼             ▼
            输出行程     调整方案 → 回到并行搜索
                        (最多3轮)
```

**编排模式**: Pipeline（串行）+ 并行（asyncio.gather）+ 预算循环（while loop）

---

## 快速开始（5分钟上手）

### 前置条件

- Python 3.10+（运行 Python 版本）
- Java 21+（运行 Java 版本，可选）
- Go 1.22+（运行 Go 版本，可选）

### Python 版本（推荐先跑这个）

```bash
# 1. 克隆项目
git clone https://github.com/bcefghj/multi-agent-travel-planner.git
cd multi-agent-travel-planner

# 2. 安装依赖
cd python
pip install -r requirements.txt

# 3. 运行 CLI 演示（不需要任何 API Key！）
python main.py

# 4. 自定义参数
python main.py --budget 15000 --departure 上海 --start 2026-06-01 --end 2026-06-07 --style luxury --travelers 2

# 5. 启动 API 服务
python -m api.app

# 6. 启动 Streamlit 前端
streamlit run ui/streamlit_app.py

# 7. 运行测试
python -m pytest tests/ -v
```

### Java 版本

```bash
cd java
# 如果有 Maven Wrapper
./mvnw spring-boot:run
# 或者用系统 Maven
mvn spring-boot:run

# 测试 API
curl -X POST http://localhost:8080/api/plan \
  -H "Content-Type: application/json" \
  -d '{"budget": 10000, "departureCity": "北京", "startDate": "2026-05-01", "endDate": "2026-05-05"}'
```

### Go 版本

```bash
cd golang
go mod tidy
go run ./cmd/server

# 测试 API
curl -X POST http://localhost:8080/api/plan \
  -H "Content-Type: application/json" \
  -d '{"origin_city": "上海", "duration_days": 5, "budget_cny": 12000, "travel_style": "comfort"}'
```

---

## 运行效果展示

### CLI 输出示例

```
============================================================
📋 行程规划结果
============================================================

🌍 目的地: 首尔, 韩国
   潮流时尚与历史文化交汇
   亮点: 景福宫, 明洞, 北村韩屋村, 南山塔

✈️  去程: 东方航空 MU1903 ¥1578
✈️  返程: 南方航空 CZ6372 ¥1703

🏨 酒店: 首尔精品设计酒店 (4.0星)
   ¥395/晚 × 4 晚
   设施: WiFi, 早餐, 酒吧

📅 每日行程:

  2026-05-01 (日花费: ¥730)
    [morning  ] 博物馆参观 (3.0h) ¥80
    [afternoon] 温泉/SPA体验 (2.0h) ¥350
    [evening  ] 文化演出 (2.0h) ¥300

  2026-05-02 (日花费: ¥530)
    [morning  ] 博物馆参观 (3.0h) ¥80
    [afternoon] 特色午餐 (1.5h) ¥150
    [evening  ] 文化演出 (2.0h) ¥300

💰 预算明细:
   航班: ¥3281
   酒店: ¥1580
   活动: ¥2270
   ─────────────
   总计: ¥7131 / 预算: ¥10000
   ✅ 预算内
```

---

## 项目结构

```
.
├── README.md                    ← 你正在看的文件
│
├── docs/                        ← 面试准备资料（重点看！）
│   ├── 01-八股文.md              ← 15个核心知识点
│   ├── 02-简历模板.md            ← STAR法则 + 简历模板
│   ├── 03-面试QA.md             ← 34道面试题 + 参考答案
│   ├── 04-架构设计详解.md        ← 架构图 + 设计决策详解
│   └── 05-代码讲解.md            ← 逐模块代码讲解
│
├── python/                      ← Python 实现（主力版本）
│   ├── main.py                  ← CLI 入口
│   ├── requirements.txt
│   ├── config/settings.py       ← 配置管理
│   ├── models/schemas.py        ← Pydantic 数据模型
│   ├── agents/                  ← 6个 Agent
│   │   ├── base_agent.py        ← Agent 基类（模板方法模式）
│   │   ├── preference_agent.py  ← 偏好收集
│   │   ├── destination_agent.py ← 目的地推荐
│   │   ├── flight_agent.py      ← 航班搜索
│   │   ├── hotel_agent.py       ← 酒店搜索
│   │   ├── activity_agent.py    ← 活动推荐
│   │   └── budget_agent.py      ← 预算校验
│   ├── orchestrator/            ← 编排层
│   │   ├── pipeline.py          ← Pipeline 编排器
│   │   ├── parallel.py          ← 并行执行器
│   │   └── budget_loop.py       ← 预算循环控制
│   ├── tools/                   ← Mock 搜索工具
│   ├── api/app.py               ← FastAPI 后端
│   ├── ui/streamlit_app.py      ← Streamlit 前端
│   └── tests/test_agents.py     ← 10个单元测试
│
├── java/                        ← Java Spring Boot 实现
│   ├── pom.xml
│   ├── README.md
│   └── src/main/java/com/travel/
│       ├── agent/               ← 6个 Agent
│       ├── orchestrator/        ← CompletableFuture 并行
│       ├── model/               ← 数据模型
│       ├── controller/          ← REST API
│       └── service/             ← 业务服务
│
└── golang/                      ← Go 实现
    ├── go.mod
    ├── README.md
    ├── cmd/server/main.go       ← 入口
    ├── internal/
    │   ├── agent/               ← 6个 Agent
    │   ├── orchestrator/        ← goroutine 并行
    │   ├── model/               ← 数据结构
    │   └── handler/             ← HTTP 处理器
    └── pkg/llm/                 ← LLM 客户端
```

---

## 6个Agent详解

| # | Agent | 职责 | 输入 | 输出 | 面试重点 |
|---|-------|------|------|------|---------|
| 1 | **Preference** | 收集/补充用户偏好 | UserPreferences | enriched UserPreferences | 为什么需要单独的偏好Agent？ |
| 2 | **Destination** | 推荐目的地 | UserPreferences | Top3 城市 + 推荐理由 | 多维度评分算法设计 |
| 3 | **Flight** | 航班搜索比价 | 出发城市+目的地+日期 | 航班列表 + 推荐航班 | 并行执行、评分函数 |
| 4 | **Hotel** | 酒店匹配 | 目的地+入住日期+风格 | 酒店列表 + 推荐酒店 | 风格匹配、房间数计算 |
| 5 | **Activity** | 生成每日行程 | 目的地+天数+兴趣 | 每日活动计划 | 时间槽分配算法 |
| 6 | **Budget** | 预算校验与调整 | 所有费用汇总 | 预算明细 + 调整建议 | **渐进式降级循环** |

---

## 面试准备路线图

如果你正在准备面试，建议按以下顺序学习：

### 第一步：理解架构（1天）

1. 阅读 [架构设计详解](docs/04-架构设计详解.md)
2. 运行 Python 版本，观察日志输出
3. 画出架构图，能口述整个流程

### 第二步：读懂代码（1-2天）

1. 阅读 [代码讲解](docs/05-代码讲解.md)
2. 从 `main.py` 开始，F12 跳转阅读每个模块
3. 重点理解：并行执行器 + 预算循环

### 第三步：背八股文（2-3天）

1. 阅读 [八股文](docs/01-八股文.md) 全部15个知识点
2. 重点掌握：Agent vs Workflow、Pipeline vs DAG、LangGraph vs CrewAI
3. 能用自己的话解释每个概念

### 第四步：准备面试（1-2天）

1. 阅读 [面试QA](docs/03-面试QA.md) 全部34道题
2. 用 [STAR法则](docs/02-简历模板.md) 写好简历
3. 对着镜子练习口述项目（控制在3分钟内）

### 第五步：扩展加分（可选）

1. 把 Mock 替换为真实 API（如 MiniMax M2.7）
2. 添加新的 Agent（如 WeatherAgent）
3. 接入 Langfuse 实现可观测性

---

## 技术栈对比

| 维度 | Python | Java | Go |
|------|--------|------|----|
| **框架** | FastAPI + asyncio | Spring Boot 3.3 | Gin |
| **并行** | asyncio.gather | CompletableFuture.allOf | goroutine + WaitGroup |
| **数据模型** | Pydantic v2 | Record / POJO | Struct |
| **状态安全** | 不同字段无冲突 | synchronized | sync.Mutex |
| **测试** | pytest | JUnit 5 | go test |
| **部署** | uvicorn | JAR | 单二进制 |
| **适合岗位** | AI工程师 | Java后端 | Go后端 |

---

## API 接口文档

### POST /api/plan

**请求**:
```json
{
  "budget": 10000,
  "departure_city": "北京",
  "start_date": "2026-05-01",
  "end_date": "2026-05-05",
  "travel_style": "comfort",
  "num_travelers": 1,
  "interests": ["美食", "历史"],
  "notes": ""
}
```

**响应**:
```json
{
  "destination": "首尔",
  "country": "韩国",
  "flight_cost": 3281,
  "hotel_cost": 1580,
  "activity_cost": 2270,
  "total_cost": 7131,
  "budget": 10000,
  "within_budget": true,
  "adjustment_rounds": 0,
  "hotel_name": "首尔精品设计酒店",
  "days": 4,
  "highlights": ["景福宫", "明洞", "北村韩屋村", "南山塔"]
}
```

### GET /api/health

```json
{"status": "ok", "service": "travel-planner", "agents": 6}
```

---

## 常见问题

### Q: 需要 API Key 吗？

**不需要！** 系统默认使用 Mock 模式，所有数据都是模拟生成的，可以零成本完整运行。
如果你想接入真实 LLM，设置环境变量即可：

```bash
export LLM_PROVIDER=minimax
export LLM_API_KEY=your-api-key
```

### Q: 数据是真实的吗？

Mock 模式下的航班/酒店/活动数据是模拟的，但数据结构和业务逻辑与真实场景一致。
在面试中可以说："系统架构支持接入真实 API（Amadeus/Booking/Google Places），
当前使用 Mock 数据方便演示和测试。"

### Q: 这个项目能直接写进简历吗？

当然可以！详见 [简历模板](docs/02-简历模板.md)。建议根据自己应聘的岗位选择合适的模板。

### Q: 三种语言都要学吗？

不需要。选择你面试使用的语言深入学习即可：
- 面 AI 工程师 → 重点 Python
- 面 Java 后端 → 重点 Java
- 面 Go 后端 → 重点 Go

---

## 参考的企业级项目

本项目的架构设计参考了以下优秀开源项目：

| 项目 | 框架 | 特点 |
|------|------|------|
| [Y-66/Traveler](https://github.com/Y-66/Traveler) | Agno | MCP + RAG + Memory，最完整 |
| [agno-langfuse-travel-planner](https://github.com/mcikalmerdeka/agno-langfuse-travel-planner) | Agno + Langfuse | 可观测性标杆 |
| [langgraph_travel_planner](https://github.com/sergio11/langgraph_travel_planner_assistant) | LangGraph | Supervisor 架构 |
| [Ninja-Navigator-AI](https://github.com/happyrao78/Ninja-Navigator-AI) | LangChain | FastAPI + Streamlit |
| [tripsage-ai](https://github.com/BjornMelin/tripsage-ai) | LangGraph | 70% 复杂度降低案例 |

---

## 学术参考

- [HiMAP-Travel](https://arxiv.org/html/2603.04750v1) - 分层多Agent旅行规划，52.78% 验证通过率
- [ATLAS](https://arxiv.org/html/2509.25586v1) - 约束感知多Agent协作，84% 最终通过率

---

## License

MIT License - 自由使用、修改、分发。

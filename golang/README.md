# 多智能体旅行规划服务（Go）

本项目演示一个**多智能体（Multi-Agent）旅行规划**后端：采用 **Pipeline（串行阶段）+ Parallel（`goroutine` + `sync.WaitGroup`）+ Budget Loop（最多 3 轮预算反馈）** 的架构，全部数据为 **Mock**，不调用真实机票/酒店 API，也不进行外网 LLM 请求（`pkg/llm` 为占位实现）。

## 智能体一览

| Agent | 职责 |
|--------|------|
| PreferenceAgent | 校验并补全用户偏好（流水线首站，失败短路） |
| DestinationAgent | 从 Mock 城市池中选择目的地 |
| FlightAgent | Mock 往返报价（随预算轮次渐进降价） |
| HotelAgent | Mock 酒店（随风格与轮次调整） |
| ActivityAgent | Mock 活动与日程聚合 |
| BudgetAgent | 费用汇总与是否达标判定 |

## 目录结构

- `cmd/server`：程序入口，启动 Gin
- `internal/model`：领域类型与共享状态 `TravelPlanState`
- `internal/agent`：六个 Agent + `Agent` 接口
- `internal/orchestrator`：`parallel.go`（并发与互斥）、`budget_loop.go`（预算循环）、`pipeline.go`（总编排）
- `internal/handler`：HTTP 层
- `internal/config`：环境变量配置
- `pkg/llm`：LLM 客户端占位（Mock）

## 环境要求

- Go **1.22+**

## 构建

```bash
cd golang
go mod tidy
go build -o bin/server ./cmd/server
```

## 运行

```bash
cd golang
go run ./cmd/server
```

默认监听 **`:8080`**。可通过环境变量调整：

| 变量 | 含义 | 默认 |
|------|------|------|
| `PORT` | 监听端口 | `8080` |
| `GIN_MODE` | `debug` / `release` / `test` | `release` |
| `LLM_MOCK` | 是否使用 Mock LLM（预留开关） | `true` |

## API 示例

### 健康检查

```bash
curl -s http://localhost:8080/api/health
```

### 生成行程（POST `/api/plan`）

```bash
curl -s http://localhost:8080/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "origin_city": "上海",
    "duration_days": 5,
    "budget_cny": 12000,
    "travel_style": "comfort",
    "interests": ["美食","购物"]
  }'
```

成功时返回完整 `TravelPlanState` JSON（含目的地、航班/酒店/活动、预算分解、`state` 终态等）。若偏好不合法（如缺少 `origin_city`），返回 **400**。

## 架构说明（面试可讲）

1. **黑板架构（Blackboard）**：各 Agent 读写同一份 `TravelPlanState`，由编排层控制执行顺序与并发边界。
2. **流水线（Pipeline）**：Preference → Destination →（并行检索 + 预算循环）。
3. **并行（Parallel）**：航班/酒店/活动互不阻塞地启动 goroutine，`WaitGroup` 等待收束；对共享 `state` 的写入用 `sync.Mutex` 保护，避免 data race（`go test -race` 友好）。
4. **预算循环（Budget Loop）**：`BudgetAgent` 作为「裁判」，未达标则在最多 3 轮内提高「压价强度」（由各 Agent 读取 `BudgetLoopRound` 实现 Mock 渐进调整）。

## 许可证

示例项目，按需自用。

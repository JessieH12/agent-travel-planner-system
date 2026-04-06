# 智能旅游行程规划系统（Java / Spring Boot）

多智能体（Multi-Agent）演示项目：**顺序流水线（偏好 → 目的地）** + **并行检索（航班 / 酒店 / 活动，`CompletableFuture.allOf`）** + **预算反馈循环（最多 3 轮）**。所有 Agent 使用 **Mock 数据**，不调用外部真实 API。

## 环境要求

- JDK **21**（`pom.xml` 中 `java.version` 为 21）
- Maven **3.9+**，或直接使用项目内的 **Maven Wrapper**（`./mvnw`）

### macOS（Homebrew 已安装 `openjdk@21` 但未 link）

若默认 `java` 仍是 17，编译前指定：

```bash
export JAVA_HOME="/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
```

## 构建

```bash
cd java
./mvnw -q clean package -DskipTests
```

（若已全局安装 Maven，也可使用 `mvn -q clean package -DskipTests`。）

## 运行

```bash
cd java
export JAVA_HOME="/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"   # 按需
./mvnw spring-boot:run
```

启动后默认端口：**8080**（见 `src/main/resources/application.yml`）。

## API 说明

### 健康检查

```http
GET http://localhost:8080/api/health
```

### 生成行程（JSON 体）

```http
POST http://localhost:8080/api/plan
Content-Type: application/json
```

示例请求体：

```json
{
  "budget": 15000,
  "style": "BUDGET_FRIENDLY",
  "startDate": "2026-05-01",
  "endDate": "2026-05-05",
  "departureCity": "上海",
  "travelers": 2,
  "interests": ["美食", "博物馆"]
}
```

- `style` 可选：`RELAXED`、`ADVENTURE`、`CULTURE`、`LUXURY`、`BUDGET_FRIENDLY`
- 校验失败时返回 **HTTP 400**，响应体中带 `planningState: FAILED` 与 `errorMessage`

## 模块与包结构（面试可讲）

| 包 | 职责 |
|----|------|
| `com.travel.agent` | 各智能体：模板方法基类 + 具体 Agent |
| `com.travel.orchestrator` | `ParallelExecutor`、`BudgetLoopController`、`TravelPlanningPipeline` |
| `com.travel.model` | 领域 / 传输模型 |
| `com.travel.service` | 应用服务，封装用例 |
| `com.travel.controller` | REST 入口 |
| `com.travel.config` | 线程池等基础设施配置 |

## 架构一句话

**Pipeline 串行前置依赖，CompletableFuture 并行缩短检索时间，Budget 循环在超支时抬高「预算压力等级」驱动 Mock 侧降价与减配。**

// Package agent 实现六个领域智能体，遵循「单一职责 + 接口多态」。
//
// 面试要点：
//   - Agent 接口将「可替换的执行单元」抽象出来，Orchestrator 只依赖接口不依赖具体实现（依赖倒置）；
//   - Run 接收 context 支持超时与取消（生产环境对接上游 HTTP deadline）；
//   - 所有实现均为 Mock，便于单元测试与离线演示，未来可无缝替换为真实 LLM/API 调用。
package agent

import (
	"context"

	"travel-planner/internal/model"
)

// Agent 智能体统一契约：输入输出均为共享状态 TravelPlanState（黑板架构 Blackboard）。
type Agent interface {
	// Name 用于日志、指标与调试追踪。
	Name() string
	// Run 读取并更新 state；实现应保证在单 goroutine 调用下对 state 的写入是明确的（并行由 orchestrator 加锁）。
	Run(ctx context.Context, state *model.TravelPlanState) error
}

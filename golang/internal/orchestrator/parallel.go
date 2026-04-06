// Package orchestrator 编排多智能体的串行流水线、并行子阶段与预算反馈循环。
//
// 面试要点：
//   - 「编排层」与「领域 Agent」分离：编排只负责时序与并发原语，业务规则在 Agent 内；
//   - 并行阶段使用 sync.WaitGroup 等待全部完成，sync.Mutex 保护对 TravelPlanState 的写入（避免 data race）；
//   - 说明：本示例将整段 Run 放在互斥区内，便于通过 -race；生产环境更常见的写法是「锁外调用外部 API，锁内仅合并结果指针」以获得真实并行度。
package orchestrator

import (
	"context"
	"sync"

	"travel-planner/internal/agent"
	"travel-planner/internal/model"
)

// RunParallel 使用 goroutine + WaitGroup 并发执行多个 Agent，并用 Mutex 序列化对 state 的更新。
//
// 若某个 Agent 返回错误，会记录第一个错误并在全部 goroutine 结束后返回（部分失败策略可按产品需求改为 fast-fail）。
func RunParallel(ctx context.Context, state *model.TravelPlanState, agents []agent.Agent) error {
	state.State = model.PlanningStateParallelSearch

	var wg sync.WaitGroup
	var mu sync.Mutex
	// errCh 用于收集各 goroutine 的 error（带缓冲，避免发送方阻塞；体现 channel 协调模式）。
	errCh := make(chan error, len(agents))

	for _, ag := range agents {
		a := ag
		wg.Add(1)
		go func() {
			defer wg.Done()
			// 关键区：共享黑板 TravelPlanState 的写入必须互斥。
			// 真实系统可改为「锁外 IO、锁内仅合并指针」，或各 Agent 通过只读快照 + 结果 chan 汇总。
			mu.Lock()
			err := a.Run(ctx, state)
			mu.Unlock()
			errCh <- err
		}()
	}

	wg.Wait()
	close(errCh)

	var firstErr error
	for err := range errCh {
		if err != nil && firstErr == nil {
			firstErr = err
		}
	}
	return firstErr
}

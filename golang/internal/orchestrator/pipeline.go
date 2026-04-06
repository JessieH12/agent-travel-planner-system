package orchestrator

import (
	"context"
	"fmt"

	"travel-planner/internal/agent"
	"travel-planner/internal/model"
)

// TravelPipeline 完整主流程：Preference → Destination → BudgetLoop（内含并行 + 预算循环）。
//
// 面试总结（可背诵版）：
//   1) 前半段串行：先规范化用户输入，再确定目的地，保证后续并行任务依赖就绪；
//   2) 中段并行：航班/酒店/活动相互独立，用 WaitGroup 聚合；
//   3) 后段循环：BudgetAgent 作为 gate，不通过则递增轮次触发各 Agent 的 Mock 降价策略。
type TravelPipeline struct {
	prefAgent      *agent.PreferenceAgent
	destAgent      *agent.DestinationAgent
	budgetLoop     *BudgetLoopController
}

// NewTravelPipeline 构造默认流水线（也可改为依赖注入以便测试替换 Mock）。
func NewTravelPipeline() *TravelPipeline {
	return &TravelPipeline{
		prefAgent:  agent.NewPreferenceAgent(),
		destAgent:  agent.NewDestinationAgent(),
		budgetLoop: NewBudgetLoopController(),
	}
}

// Run 执行整条流水线，最终 state.State 为 Completed 或 BudgetExceeded（或其它错误）。
func (p *TravelPipeline) Run(ctx context.Context, state *model.TravelPlanState) error {
	if state == nil {
		return fmt.Errorf("TravelPipeline: state 不能为空")
	}

	if err := p.prefAgent.Run(ctx, state); err != nil {
		return fmt.Errorf("preference: %w", err)
	}

	if err := p.destAgent.Run(ctx, state); err != nil {
		return fmt.Errorf("destination: %w", err)
	}

	if err := p.budgetLoop.Run(ctx, state); err != nil {
		return fmt.Errorf("budget loop: %w", err)
	}

	return nil
}

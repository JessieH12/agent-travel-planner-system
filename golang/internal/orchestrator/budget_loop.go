package orchestrator

import (
	"context"
	"fmt"

	"travel-planner/internal/agent"
	"travel-planner/internal/model"
)

// MaxBudgetRounds 预算反馈循环最大轮数（含首轮），与需求「最多 3 轮」一致。
const MaxBudgetRounds = 3

// BudgetLoopController 封装「并行检索 → 预算评估 → 未通过则进入下一轮」的控制逻辑。
//
// 设计模式：迭代式改进（Iterative Refinement），类似 ReAct/Reflexion 的简化工程版——
// 预算 Agent 充当 critic，其它 Agent 根据 BudgetLoopRound 与历史结果自我调节 Mock 报价。
type BudgetLoopController struct {
	ParallelAgents []agent.Agent
	BudgetAgent    agent.Agent
}

// NewBudgetLoopController 组装航班/酒店/活动并行组与预算裁判。
func NewBudgetLoopController() *BudgetLoopController {
	return &BudgetLoopController{
		ParallelAgents: []agent.Agent{
			agent.NewFlightAgent(),
			agent.NewHotelAgent(),
			agent.NewActivityAgent(),
		},
		BudgetAgent: agent.NewBudgetAgent(),
	}
}

// Run 执行最多 MaxBudgetRounds 轮；任意一轮预算通过则置 Completed 并返回。
func (c *BudgetLoopController) Run(ctx context.Context, state *model.TravelPlanState) error {
	if c.BudgetAgent == nil {
		return fmt.Errorf("BudgetLoopController: BudgetAgent 未设置")
	}
	if len(c.ParallelAgents) == 0 {
		return fmt.Errorf("BudgetLoopController: ParallelAgents 为空")
	}

	for round := 0; round < MaxBudgetRounds; round++ {
		state.BudgetLoopRound = round

		if err := RunParallel(ctx, state, c.ParallelAgents); err != nil {
			return fmt.Errorf("budget loop round %d parallel: %w", round, err)
		}

		if err := c.BudgetAgent.Run(ctx, state); err != nil {
			return fmt.Errorf("budget loop round %d budget: %w", round, err)
		}

		if state.Budget != nil && state.Budget.WithinBudget {
			state.State = model.PlanningStateCompleted
			return nil
		}

		// 未通过且还有下一轮：标记调整中，由下一轮 ParallelAgents 读取 BudgetLoopRound 做渐进压价。
		if round < MaxBudgetRounds-1 {
			state.State = model.PlanningStateAdjusting
		}
	}

	state.State = model.PlanningStateBudgetExceeded
	return nil
}

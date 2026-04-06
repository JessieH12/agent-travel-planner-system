package agent

import (
	"context"
	"fmt"

	"travel-planner/internal/model"
)

// PreferenceAgent 负责校验与补全用户偏好（流水线第一站：串行前置条件）。
//
// 设计说明：
//   - 「管道过滤器」模式：不合法则短路并记录 Errors，避免后续 Agent 做无意义计算；
//   - 默认值策略集中在此，避免各 Agent 重复猜测用户意图。
type PreferenceAgent struct{}

func NewPreferenceAgent() *PreferenceAgent {
	return &PreferenceAgent{}
}

func (a *PreferenceAgent) Name() string {
	return "PreferenceAgent"
}

func (a *PreferenceAgent) Run(ctx context.Context, state *model.TravelPlanState) error {
	_ = ctx
	p := &state.Preferences

	if p.OriginCity == "" {
		state.Errors = append(state.Errors, "origin_city 不能为空")
		return fmt.Errorf("invalid preferences: missing origin_city")
	}
	if p.DurationDays <= 0 {
		p.DurationDays = 5
	}
	if p.DurationDays > 30 {
		state.Errors = append(state.Errors, "行程天数过长，已限制为 30 天")
		p.DurationDays = 30
	}
	if p.BudgetCNY <= 0 {
		p.BudgetCNY = 8000
	}
	if p.TravelStyle == "" {
		p.TravelStyle = model.TravelStyleComfort
	}
	if len(p.Interests) == 0 {
		p.Interests = []string{"美食", "城市观光"}
	}

	state.State = model.PlanningStatePreferencesDone
	return nil
}

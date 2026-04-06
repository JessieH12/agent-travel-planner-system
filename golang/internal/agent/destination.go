package agent

import (
	"context"
	"fmt"
	"strings"

	"travel-planner/internal/model"
)

// mockDestinations 固定 Mock 池（面试可说：真实系统可接向量检索 / LLM 重排）。
var mockDestinations = []model.Destination{
	{Name: "东京", Country: "日本", Description: "都市、购物与美食"},
	{Name: "曼谷", Country: "泰国", Description: "热带风情与夜市"},
	{Name: "巴黎", Country: "法国", Description: "艺术、博物馆与浪漫街区"},
	{Name: "清迈", Country: "泰国", Description: "古城、咖啡与自然"},
	{Name: "首尔", Country: "韩国", Description: "潮流、美妆与韩餐"},
	{Name: "大阪", Country: "日本", Description: "关西美食与环球影城"},
}

// DestinationAgent 根据用户兴趣从 Mock 城市中选择一个目的地（规则引擎简化版）。
type DestinationAgent struct{}

func NewDestinationAgent() *DestinationAgent {
	return &DestinationAgent{}
}

func (a *DestinationAgent) Name() string {
	return "DestinationAgent"
}

func (a *DestinationAgent) Run(ctx context.Context, state *model.TravelPlanState) error {
	_ = ctx
	if state.State != model.PlanningStatePreferencesDone {
		return fmt.Errorf("DestinationAgent: 期望状态 preferences_done，当前 %s", state.State)
	}

	joined := strings.Join(state.Preferences.Interests, "")
	pick := mockDestinations[0]

	switch {
	case strings.Contains(joined, "购物") || strings.Contains(joined, "都市"):
		pick = findDest("东京")
	case strings.Contains(joined, "夜") || strings.Contains(joined, "海"):
		pick = findDest("曼谷")
	case strings.Contains(joined, "艺术") || strings.Contains(joined, "博物"):
		pick = findDest("巴黎")
	case strings.Contains(joined, "慢") || strings.Contains(joined, "咖啡"):
		pick = findDest("清迈")
	case strings.Contains(joined, "美") || strings.Contains(joined, "韩"):
		pick = findDest("首尔")
	case strings.Contains(joined, "美食") || strings.Contains(joined, "吃"):
		pick = findDest("大阪")
	default:
		// 按预算粗分：高预算偏向巴黎/东京
		if state.Preferences.BudgetCNY >= 15000 {
			pick = findDest("巴黎")
		} else if state.Preferences.BudgetCNY >= 10000 {
			pick = findDest("东京")
		}
	}

	state.Destination = &pick
	state.State = model.PlanningStateDestinationDone
	return nil
}

func findDest(name string) model.Destination {
	for _, d := range mockDestinations {
		if d.Name == name {
			return d
		}
	}
	return mockDestinations[0]
}

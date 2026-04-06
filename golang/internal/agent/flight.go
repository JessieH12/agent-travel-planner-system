package agent

import (
	"context"
	"fmt"
	"math"

	"travel-planner/internal/model"
)

// FlightAgent Mock 航班检索：根据目的地、出行风格与预算轮次渐进「降价」。
//
// 面试要点：
//   - 与真实供应商对接时，可将 Run 内改为调用 pkg/llm 或 HTTP Client，并保持接口不变；
//   - BudgetLoopRound 体现「反馈循环」：预算 Agent 未通过后，同一 Agent 再次执行时输出更便宜方案。
type FlightAgent struct{}

func NewFlightAgent() *FlightAgent {
	return &FlightAgent{}
}

func (a *FlightAgent) Name() string {
	return "FlightAgent"
}

func (a *FlightAgent) Run(ctx context.Context, state *model.TravelPlanState) error {
	_ = ctx
	if state.Destination == nil {
		return fmt.Errorf("FlightAgent: destination 未设置")
	}

	origin := state.Preferences.OriginCity
	dest := state.Destination.Name

	base := 2200.0
	switch dest {
	case "曼谷", "清迈":
		base = 1600
	case "首尔", "大阪", "东京":
		base = 2400
	case "巴黎":
		base = 5200
	}

	styleMul := 1.0
	switch state.Preferences.TravelStyle {
	case model.TravelStyleBudget:
		styleMul = 0.85
	case model.TravelStyleLuxury:
		styleMul = 1.35
	}

	// 每一轮预算循环压价约 12%（Mock 收敛策略）
	roundDiscount := math.Pow(0.88, float64(state.BudgetLoopRound))
	price := math.Round(base*styleMul*roundDiscount*100) / 100

	cabin := "经济舱"
	if state.Preferences.TravelStyle == model.TravelStyleLuxury {
		cabin = "商务舱"
	}

	flight := model.Flight{
		Airline:    "Mock Airways",
		Route:      fmt.Sprintf("%s → %s 往返", origin, dest),
		DepartTime: "09:00",
		ReturnTime: "18:00",
		PriceCNY:   price,
		CabinClass: cabin,
	}

	state.FlightResult = &model.FlightSearchResult{
		Offers: []model.Flight{flight},
		Source: "mock",
	}
	state.SelectedFlight = &flight
	return nil
}

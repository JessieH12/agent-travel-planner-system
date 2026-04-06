package agent

import (
	"context"
	"fmt"
	"math"

	"travel-planner/internal/model"
)

// BudgetAgent 汇总费用、判断是否超支，并写入下一轮协调建议（「裁判」角色）。
//
// 设计说明：
//   - 不直接修改航班/酒店数据，而是通过 BudgetBreakdown.Suggestion + 外层 BudgetLoopRound++ 驱动其他 Agent 自我调整；
//   - 符合开闭原则：扩展预算规则只需改本 Agent，无需改并行执行器。
type BudgetAgent struct{}

func NewBudgetAgent() *BudgetAgent {
	return &BudgetAgent{}
}

func (a *BudgetAgent) Name() string {
	return "BudgetAgent"
}

func (a *BudgetAgent) Run(ctx context.Context, state *model.TravelPlanState) error {
	_ = ctx
	var flightTotal, hotelTotal, actTotal float64

	if state.SelectedFlight != nil {
		flightTotal = state.SelectedFlight.PriceCNY
	}
	if state.SelectedHotel != nil {
		hotelTotal = state.SelectedHotel.TotalCNY
	}
	for _, ac := range state.SelectedActivity {
		actTotal += ac.PriceCNY
	}

	grand := math.Round((flightTotal+hotelTotal+actTotal)*100) / 100
	budget := state.Preferences.BudgetCNY
	within := grand <= budget
	overBy := 0.0
	if !within {
		overBy = math.Round((grand-budget)*100) / 100
	}

	suggestion := "预算内，无需调整"
	if !within {
		switch state.BudgetLoopRound {
		case 0:
			suggestion = "优先压缩机票与酒店档位，并减少可选高价活动"
		case 1:
			suggestion = "继续下调住宿单价，剔除剩余最贵活动"
		default:
			suggestion = "已多轮压价，若仍超支请用户提高预算或缩短行程"
		}
	}

	state.Budget = &model.BudgetBreakdown{
		FlightTotal:   math.Round(flightTotal*100) / 100,
		HotelTotal:    math.Round(hotelTotal*100) / 100,
		ActivityTotal: math.Round(actTotal*100) / 100,
		GrandTotal:    grand,
		WithinBudget:  within,
		Round:         state.BudgetLoopRound,
		Suggestion:    suggestion,
		OverByCNY:     overBy,
	}
	state.State = model.PlanningStateBudgetEvaluating

	if state.SelectedFlight == nil || state.SelectedHotel == nil {
		return fmt.Errorf("BudgetAgent: 缺少航班或酒店明细")
	}
	return nil
}

package agent

import (
	"context"
	"fmt"
	"math"

	"travel-planner/internal/model"
)

// HotelAgent Mock 酒店：星级与每晚价格随 TravelStyle 与 BudgetLoopRound 变化。
type HotelAgent struct{}

func NewHotelAgent() *HotelAgent {
	return &HotelAgent{}
}

func (a *HotelAgent) Name() string {
	return "HotelAgent"
}

func (a *HotelAgent) Run(ctx context.Context, state *model.TravelPlanState) error {
	_ = ctx
	if state.Destination == nil {
		return fmt.Errorf("HotelAgent: destination 未设置")
	}

	nights := state.Preferences.DurationDays - 1
	if nights < 1 {
		nights = 1
	}

	perNight := 480.0
	stars := 3
	name := state.Destination.Name + " · 舒适型酒店"

	switch state.Preferences.TravelStyle {
	case model.TravelStyleBudget:
		perNight = 320
		stars = 2
		name = state.Destination.Name + " · 经济快捷"
	case model.TravelStyleLuxury:
		perNight = 980
		stars = 5
		name = state.Destination.Name + " · 五星级套房"
	}

	// 目的地系数（Mock）
	switch state.Destination.Name {
	case "巴黎":
		perNight *= 1.45
	case "东京", "首尔", "大阪":
		perNight *= 1.15
	}

	roundDiscount := math.Pow(0.9, float64(state.BudgetLoopRound))
	perNight = math.Round(perNight*roundDiscount*100) / 100
	total := math.Round(perNight*float64(nights)*100) / 100

	h := model.Hotel{
		Name:             name,
		Nights:           nights,
		PricePerNightCNY: perNight,
		TotalCNY:         total,
		StarRating:       stars,
	}

	state.HotelResult = &model.HotelSearchResult{
		Offers: []model.Hotel{h},
		Source: "mock",
	}
	state.SelectedHotel = &h
	return nil
}

// Package model 定义多智能体旅行规划系统的领域模型与状态载体。
//
// 面试要点：
//   - 将「共享状态」显式建模为 TravelPlanState，便于流水线各阶段读写与审计；
//   - 使用类型别名 TravelStyle / PlanningState + 常量，避免魔法字符串，利于重构与 OpenAPI 对齐；
//   - DTO 与运行态状态分离：HTTP 入参可映射到 UserPreferences，再由 Agent 逐步填充计划细节。
package model

// TravelStyle 出行风格，影响 Mock 酒店档位与活动推荐策略（策略模式在 Agent 中的体现）。
type TravelStyle string

const (
	TravelStyleBudget  TravelStyle = "budget"  // 经济
	TravelStyleComfort TravelStyle = "comfort" // 舒适
	TravelStyleLuxury  TravelStyle = "luxury"  // 奢华
)

// PlanningState 流水线阶段标记，用于可观测性与调试（状态机思想）。
type PlanningState string

const (
	PlanningStateInit              PlanningState = "init"
	PlanningStatePreferencesDone   PlanningState = "preferences_done"
	PlanningStateDestinationDone   PlanningState = "destination_done"
	PlanningStateParallelSearch    PlanningState = "parallel_search"    // 航班/酒店/活动并行检索中
	PlanningStateBudgetEvaluating  PlanningState = "budget_evaluating"  // 预算评估
	PlanningStateAdjusting         PlanningState = "adjusting"          // 预算超支，进入下一轮压价
	PlanningStateCompleted         PlanningState = "completed"
	PlanningStateBudgetExceeded    PlanningState = "budget_exceeded"    // 三轮仍无法满足预算
)

// UserPreferences 用户偏好，通常来自 HTTP 请求体。
type UserPreferences struct {
	OriginCity   string      `json:"origin_city"`
	DurationDays int         `json:"duration_days"`
	BudgetCNY    float64     `json:"budget_cny"`
	TravelStyle  TravelStyle `json:"travel_style"`
	Interests    []string    `json:"interests"`
}

// Destination 目的地信息（DestinationAgent 产出）。
type Destination struct {
	Name        string `json:"name"`
	Country     string `json:"country"`
	Description string `json:"description"`
}

// Flight 航班方案（FlightAgent 产出）。
type Flight struct {
	Airline     string  `json:"airline"`
	Route       string  `json:"route"`
	DepartTime  string  `json:"depart_time"`
	ReturnTime  string  `json:"return_time"`
	PriceCNY    float64 `json:"price_cny"`
	CabinClass  string  `json:"cabin_class"`
}

// Hotel 酒店方案（HotelAgent 产出）。
type Hotel struct {
	Name             string  `json:"name"`
	Nights           int     `json:"nights"`
	PricePerNightCNY float64 `json:"price_per_night_cny"`
	TotalCNY         float64 `json:"total_cny"`
	StarRating       int     `json:"star_rating"`
}

// Activity 单项活动（ActivityAgent 产出列表）。
type Activity struct {
	Name        string  `json:"name"`
	Day         int     `json:"day"`
	PriceCNY    float64 `json:"price_cny"`
	Duration    string  `json:"duration"`
	Description string  `json:"description"`
}

// DayPlan 按天聚合的活动视图（便于前端展示日程轴）。
type DayPlan struct {
	Day        int        `json:"day"`
	Activities []Activity `json:"activities"`
}

// FlightSearchResult 航班检索结果封装（可扩展为多候选、trace id 等）。
type FlightSearchResult struct {
	Offers []Flight `json:"offers"`
	Source string   `json:"source"` // mock / api
}

// HotelSearchResult 酒店检索结果封装。
type HotelSearchResult struct {
	Offers []Hotel `json:"offers"`
	Source string  `json:"source"`
}

// ActivitySearchResult 活动检索结果封装。
type ActivitySearchResult struct {
	Items  []Activity `json:"items"`
	Source string     `json:"source"`
}

// BudgetBreakdown 预算分解与是否达标（BudgetAgent 产出）。
type BudgetBreakdown struct {
	FlightTotal    float64 `json:"flight_total"`
	HotelTotal     float64 `json:"hotel_total"`
	ActivityTotal  float64 `json:"activity_total"`
	GrandTotal     float64 `json:"grand_total"`
	WithinBudget   bool    `json:"within_budget"`
	Round          int     `json:"round"`           // 第几轮评估（0-based）
	Suggestion     string  `json:"suggestion"`      // 给下一轮 Agent 的提示（协调信号）
	OverByCNY      float64 `json:"over_by_cny"`     // 超出金额，便于日志
}

// TravelPlanState 全链路共享状态：Pipeline + 并行子任务 + 预算循环均读写此结构体。
//
// 并发安全说明：并行阶段由 orchestrator 使用 sync.Mutex 包裹 Run，Agent 内部不应再启动未协调的 goroutine 写同一 state。
type TravelPlanState struct {
	State PlanningState `json:"state"`

	Preferences UserPreferences `json:"preferences"`
	Destination *Destination    `json:"destination,omitempty"`

	// 并行检索产物
	FlightResult    *FlightSearchResult    `json:"flight_result,omitempty"`
	HotelResult     *HotelSearchResult     `json:"hotel_result,omitempty"`
	ActivityResult  *ActivitySearchResult  `json:"activity_result,omitempty"`
	// 当前选中的单一方案（Budget 循环中可能被「压价」后更新）
	SelectedFlight   *Flight     `json:"selected_flight,omitempty"`
	SelectedHotel    *Hotel      `json:"selected_hotel,omitempty"`
	SelectedActivity []Activity  `json:"selected_activity,omitempty"`
	DayPlans         []DayPlan   `json:"day_plans,omitempty"`

	Budget *BudgetBreakdown `json:"budget,omitempty"`

	// BudgetLoopRound 当前预算循环轮次（0..2 共最多 3 轮），供各 Agent Mock 渐进降价。
	BudgetLoopRound int `json:"budget_loop_round"`

	Errors []string `json:"errors,omitempty"`
}

// NewTravelPlanState 构造初始状态，便于 handler 与测试复用。
func NewTravelPlanState(prefs UserPreferences) *TravelPlanState {
	return &TravelPlanState{
		State:       PlanningStateInit,
		Preferences: prefs,
		Errors:      nil,
	}
}

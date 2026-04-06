package agent

import (
	"context"
	"fmt"
	"math"
	"sort"

	"travel-planner/internal/model"
)

// activityCatalog 按目的地的 Mock 活动库（可视为静态配置或 CMS）。
var activityCatalog = map[string][]model.Activity{
	"东京": {
		{Name: "浅草寺与晴空塔", Day: 1, PriceCNY: 120, Duration: "半天", Description: "经典地标打卡"},
		{Name: "筑地场外市场美食", Day: 2, PriceCNY: 200, Duration: "2h", Description: "海鲜与日料小吃"},
		{Name: "银座购物漫步", Day: 3, PriceCNY: 0, Duration: "半天", Description: "橱窗与商圈"},
	},
	"曼谷": {
		{Name: "大皇宫与玉佛寺", Day: 1, PriceCNY: 150, Duration: "半天", Description: "文化与建筑"},
		{Name: "湄南河游船晚餐", Day: 2, PriceCNY: 280, Duration: "3h", Description: "夜景与泰餐"},
		{Name: "周末夜市扫街", Day: 3, PriceCNY: 100, Duration: "晚上", Description: "小吃与手作"},
	},
	"巴黎": {
		{Name: "卢浮宫精选路线", Day: 1, PriceCNY: 420, Duration: "半天", Description: "艺术珍品"},
		{Name: "塞纳河游船", Day: 2, PriceCNY: 180, Duration: "2h", Description: "河岸风光"},
		{Name: "蒙马特半日游", Day: 3, PriceCNY: 160, Duration: "半天", Description: "高地与画家广场"},
	},
	"清迈": {
		{Name: "古城寺庙徒步", Day: 1, PriceCNY: 80, Duration: "半天", Description: "兰纳建筑"},
		{Name: "丛林飞跃体验", Day: 2, PriceCNY: 360, Duration: "全天", Description: "户外刺激"},
		{Name: "宁曼路咖啡探店", Day: 3, PriceCNY: 120, Duration: "半天", Description: "文艺街区"},
	},
	"首尔": {
		{Name: "景福宫韩服体验", Day: 1, PriceCNY: 200, Duration: "半天", Description: "宫殿与拍照"},
		{Name: "明洞购物与小吃", Day: 2, PriceCNY: 150, Duration: "半天", Description: "潮流商圈"},
		{Name: "南山塔夜景", Day: 3, PriceCNY: 180, Duration: "晚上", Description: "城市天际线"},
	},
	"大阪": {
		{Name: "道顿堀美食巡礼", Day: 1, PriceCNY: 220, Duration: "晚上", Description: "章鱼烧与拉面"},
		{Name: "大阪城公园", Day: 2, PriceCNY: 90, Duration: "半天", Description: "历史与天守阁"},
		{Name: "环球影城（Mock 门票）", Day: 3, PriceCNY: 520, Duration: "全天", Description: "主题乐园"},
	},
}

// ActivityAgent 生成活动列表并按天聚合为 DayPlans；预算循环中可减少高价项。
type ActivityAgent struct{}

func NewActivityAgent() *ActivityAgent {
	return &ActivityAgent{}
}

func (a *ActivityAgent) Name() string {
	return "ActivityAgent"
}

func (a *ActivityAgent) Run(ctx context.Context, state *model.TravelPlanState) error {
	_ = ctx
	if state.Destination == nil {
		return fmt.Errorf("ActivityAgent: destination 未设置")
	}

	items, ok := activityCatalog[state.Destination.Name]
	if !ok {
		items = []model.Activity{
			{Name: "城市自由行", Day: 1, PriceCNY: 0, Duration: "自由", Description: "默认 Mock"},
		}
	}

	// 按行程天数裁剪：只保留 day <= DurationDays 的活动
	maxDay := state.Preferences.DurationDays
	filtered := make([]model.Activity, 0, len(items))
	for _, it := range items {
		if it.Day <= maxDay {
			filtered = append(filtered, it)
		}
	}
	if len(filtered) == 0 {
		filtered = items[:1]
	}

	// 预算循环：第 2 轮去掉最贵的一项；第 3 轮再去掉当前最贵（渐进收缩）
	if state.BudgetLoopRound >= 1 {
		filtered = dropMostExpensive(filtered, state.BudgetLoopRound)
	}

	// 全局 Mock 折扣（与航班/酒店一致的压价节奏）
	discount := math.Pow(0.92, float64(state.BudgetLoopRound))
	for i := range filtered {
		filtered[i].PriceCNY = math.Round(filtered[i].PriceCNY*discount*100) / 100
	}

	state.ActivityResult = &model.ActivitySearchResult{
		Items:  filtered,
		Source: "mock",
	}
	state.SelectedActivity = filtered
	state.DayPlans = buildDayPlans(filtered)
	return nil
}

func dropMostExpensive(items []model.Activity, round int) []model.Activity {
	if len(items) <= 1 {
		return items
	}
	// round 1 去掉 1 个最贵，round 2 再去掉 1 个...
	toDrop := round
	if toDrop > len(items)-1 {
		toDrop = len(items) - 1
	}
	out := make([]model.Activity, len(items))
	copy(out, items)
	for d := 0; d < toDrop; d++ {
		idx := -1
		var max float64 = -1
		for i := range out {
			if out[i].PriceCNY > max {
				max = out[i].PriceCNY
				idx = i
			}
		}
		if idx < 0 {
			break
		}
		out = append(out[:idx], out[idx+1:]...)
	}
	return out
}

func buildDayPlans(acts []model.Activity) []model.DayPlan {
	dayMap := map[int][]model.Activity{}
	for _, a := range acts {
		dayMap[a.Day] = append(dayMap[a.Day], a)
	}
	days := make([]int, 0, len(dayMap))
	for d := range dayMap {
		days = append(days, d)
	}
	sort.Ints(days)
	plans := make([]model.DayPlan, 0, len(days))
	for _, d := range days {
		plans = append(plans, model.DayPlan{Day: d, Activities: dayMap[d]})
	}
	return plans
}

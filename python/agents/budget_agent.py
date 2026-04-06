"""
Budget Agent —— 预算校验 Agent。

职责: 实时追踪总花费，确保不超预算，超预算时生成调整建议。
在 Pipeline 最后一个节点执行，决定是否触发调整循环。

面试考点（高频!!!）:
  - 预算循环如何避免无限循环？ → max_adjustments 限制（默认 3 轮）
  - 渐进式降级策略: 先降活动 → 再降酒店 → 最后换航班
  - 每轮调整的幅度: 按超预算比例动态计算
  - 状态机转换: BUDGET_CHECKING → COMPLETED / ADJUSTING
"""

from __future__ import annotations

from loguru import logger

from models.schemas import BudgetBreakdown, PlanningState, TravelPlanState

from .base_agent import BaseAgent


class BudgetAgent(BaseAgent):
    name = "BudgetAgent"

    async def execute(self, state: TravelPlanState) -> TravelPlanState:
        pref = state.preferences
        if pref is None:
            raise ValueError("缺少用户偏好")

        flight_cost = state.flight_result.total_flight_cost if state.flight_result else 0
        hotel_cost = state.hotel_result.total_hotel_cost if state.hotel_result else 0
        activity_cost = state.activity_result.total_activity_cost if state.activity_result else 0

        total = flight_cost + hotel_cost + activity_cost
        remaining = pref.budget - total
        within_budget = remaining >= 0
        over_amount = max(0, -remaining)

        suggestions: list[str] = []
        if not within_budget:
            suggestions = self._generate_suggestions(
                over_amount, flight_cost, hotel_cost, activity_cost, state.adjustment_round,
            )

        breakdown = BudgetBreakdown(
            flight_cost=flight_cost,
            hotel_cost=hotel_cost,
            activity_cost=activity_cost,
            total_cost=total,
            budget=pref.budget,
            remaining=remaining,
            is_within_budget=within_budget,
            over_budget_amount=over_amount,
            suggestions=suggestions,
        )
        state.budget_breakdown = breakdown

        if within_budget:
            state.state = PlanningState.COMPLETED
            logger.info(f"[{self.name}] 预算通过! 总费用 ¥{total:.0f}, 剩余 ¥{remaining:.0f}")
        elif state.adjustment_round < state.max_adjustments:
            state.state = PlanningState.ADJUSTING
            state.adjustment_round += 1
            self._apply_adjustments(state)
            logger.warning(
                f"[{self.name}] 超预算 ¥{over_amount:.0f}, "
                f"进入第 {state.adjustment_round} 轮调整"
            )
        else:
            state.state = PlanningState.COMPLETED
            state.error_messages.append(
                f"经过 {state.max_adjustments} 轮调整仍超预算 ¥{over_amount:.0f}，返回当前最优方案"
            )
            logger.warning(f"[{self.name}] 达到最大调整次数, 返回当前方案")

        return state

    @staticmethod
    def _generate_suggestions(
        over: float, flight: float, hotel: float, activity: float, round_num: int,
    ) -> list[str]:
        suggestions = []
        if round_num == 0:
            suggestions.append(f"减少活动开支约 ¥{min(over, activity * 0.3):.0f}（选择免费景点）")
            suggestions.append("选择评分略低但更实惠的餐厅")
        elif round_num == 1:
            suggestions.append(f"降低酒店等级，节省约 ¥{min(over, hotel * 0.3):.0f}")
            suggestions.append("考虑距离市中心稍远但性价比更高的酒店")
        else:
            suggestions.append(f"选择更经济的航班，节省约 ¥{min(over, flight * 0.2):.0f}")
            suggestions.append("考虑中转航班替代直飞")
            suggestions.append("缩短行程天数")
        return suggestions

    @staticmethod
    def _apply_adjustments(state: TravelPlanState) -> None:
        """根据当前调整轮次，渐进式降低花费。"""
        round_num = state.adjustment_round
        over = state.budget_breakdown.over_budget_amount if state.budget_breakdown else 0

        if round_num == 1 and state.activity_result:
            cut_ratio = min(0.4, over / max(state.activity_result.total_activity_cost, 1))
            for day in state.activity_result.day_plans:
                for act in day.activities:
                    act.price *= (1 - cut_ratio)
                day.day_cost *= (1 - cut_ratio)
            state.activity_result.total_activity_cost *= (1 - cut_ratio)

        elif round_num == 2 and state.hotel_result and state.hotel_result.recommended:
            cut_ratio = min(0.35, over / max(state.hotel_result.total_hotel_cost, 1))
            state.hotel_result.recommended.price_per_night *= (1 - cut_ratio)
            state.hotel_result.total_hotel_cost *= (1 - cut_ratio)

        elif round_num >= 3 and state.flight_result:
            cut_ratio = min(0.25, over / max(state.flight_result.total_flight_cost, 1))
            if state.flight_result.recommended_outbound:
                state.flight_result.recommended_outbound.price *= (1 - cut_ratio)
            if state.flight_result.recommended_return:
                state.flight_result.recommended_return.price *= (1 - cut_ratio)
            state.flight_result.total_flight_cost *= (1 - cut_ratio)

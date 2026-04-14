package com.travel.agent;

import com.travel.config.TravelProperties;
import com.travel.model.*;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;

/**
 * 预算智能体：聚合成本、对比预算、生成建议并驱动「渐进式降级」参数。
 * <p>
 * 设计说明：
 * <ul>
 *     <li>「检查」与「调整建议」集中在一处，避免散落在多个 Service；</li>
 *     <li>{@link #applyProgressiveAdjustment(TravelPlanState)} 只修改压力等级与状态，
 *     由下一轮并行检索重新生成 mock 结果——符合 Pipeline + Loop 架构；</li>
 *     <li>面试可延伸：真实场景用规则引擎/优化器替代简单 level++。</li>
 * </ul>
 * </p>
 */
@Component
public class BudgetAgent extends BaseAgent {

    private final int maxPressure;

    public BudgetAgent(TravelProperties travelProperties) {
        this.maxPressure = travelProperties.getBudget().getMaxPressure();
    }

    @Override
    protected void execute(TravelPlanState state) {
        evaluateAndAttach(state);
    }

    /**
     * 供预算循环显式调用：写入 {@link BudgetBreakdown} 并更新是否超预算。
     */
    public void evaluateAndAttach(TravelPlanState state) {
        if (state.getPlanningState() == PlanningState.FAILED) {
            return;
        }
        UserPreferences pref = state.getPreferences();
        if (pref == null) {
            return;
        }
        BigDecimal budget = pref.getBudget();
        BigDecimal flight = safe(state.getFlightSearchResult());
        BigDecimal hotel = safeHotel(state.getHotelSearchResult());
        BigDecimal act = safeAct(state.getActivitySearchResult());
        BigDecimal total = flight.add(hotel).add(act).setScale(2, RoundingMode.HALF_UP);
        boolean ok = total.compareTo(budget) <= 0;

        List<String> suggestions = new ArrayList<>();
        if (!ok) {
            suggestions.add("总费用 " + total + " 超出预算 " + budget + "，建议接受降级检索或缩短行程。");
            suggestions.add("可优先：更多经停航班、低星级酒店、减少付费门票与购物项。");
        }

        state.setBudgetBreakdown(BudgetBreakdown.builder()
                .flightCost(flight)
                .hotelCost(hotel)
                .activityCost(act)
                .total(total)
                .budget(budget)
                .withinBudget(ok)
                .suggestions(suggestions)
                .build());
        state.setPlanningState(PlanningState.BUDGET_EVALUATION);
        log.info("预算评估: total={} budget={} within={}", total, budget, ok);
    }

    private BigDecimal safe(FlightSearchResult r) {
        return r != null && r.getTotalCost() != null ? r.getTotalCost() : BigDecimal.ZERO;
    }

    private BigDecimal safeHotel(HotelSearchResult r) {
        return r != null && r.getTotalCost() != null ? r.getTotalCost() : BigDecimal.ZERO;
    }

    private BigDecimal safeAct(ActivitySearchResult r) {
        return r != null && r.getTotalCost() != null ? r.getTotalCost() : BigDecimal.ZERO;
    }

    /**
     * @return true 表示已应用调整且仍可继续下一轮检索；false 表示已达调整上限或已在预算内
     */
    public boolean applyProgressiveAdjustment(TravelPlanState state) {
        BudgetBreakdown bd = state.getBudgetBreakdown();
        if (bd != null && bd.isWithinBudget()) {
            return false;
        }
        int next = state.getBudgetPressureLevel() + 1;
        if (next > this.maxPressure) {
            log.warn("已达最大预算压力等级，停止继续降级");
            return false;
        }

        // --- 核心优化：基于旅行风格的靶向降级策略 ---
        TravelStyle style = state.getPreferences().getStyle();
        if (style == TravelStyle.LUXURY) {
            // 豪华游：坚决不降级酒店，优先削减活动开销
            state.setDowngradeTarget("ACTIVITY");
            log.info("触发智能降级 [豪华游]：优先削减活动项目，保护住宿体验");
        } else if (style == TravelStyle.BUDGET_FRIENDLY) {
            // 穷游：优先削减酒店和航班标准
            state.setDowngradeTarget("HOTEL");
            log.info("触发智能降级 [经济游]：优先降低住宿星级");
        } else {
            // 其他：均衡降级
            state.setDowngradeTarget("ALL");
            log.info("触发智能降级 [普通]：全局均衡降级");
        }

        state.setBudgetPressureLevel(next);
        state.setPlanningState(PlanningState.BUDGET_ADJUSTMENT);
        log.info("应用渐进式预算调整: budgetPressureLevel={}", next);
        return true;
    }
}

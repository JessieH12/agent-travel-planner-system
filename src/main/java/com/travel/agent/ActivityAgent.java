package com.travel.agent;

import com.travel.model.Activity;
import com.travel.model.ActivitySearchResult;
import com.travel.model.DayPlan;
import com.travel.model.Destination;
import com.travel.model.PlanningState;
import com.travel.model.TravelPlanState;
import com.travel.model.UserPreferences;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/**
 * 活动智能体：按行程日切片生成 {@link DayPlan}（mock）。
 * <p>
 * 预算压力升高时减少高价活动、增加免费/低价项，演示与 BudgetLoop 的闭环。
 * </p>
 */
@Component
public class ActivityAgent extends BaseAgent {

    @Override
    protected void execute(TravelPlanState state) {
        if (state.getPlanningState() == PlanningState.FAILED) {
            return;
        }
        UserPreferences pref = state.getPreferences();
        Destination dest = state.getSelectedDestination();
        if (pref == null || dest == null) {
            log.warn("ActivityAgent 跳过：缺少偏好或目的地");
            return;
        }

        int pressure = state.getBudgetPressureLevel();
        LocalDate start = pref.getStartDate();
        LocalDate end = pref.getEndDate();
        List<DayPlan> days = new ArrayList<>();
        BigDecimal total = BigDecimal.ZERO;

        for (LocalDate d = start; d.isBefore(end); d = d.plusDays(1)) {
            List<Activity> acts = buildDayActivities(dest, pref, d, pressure);
            BigDecimal dayCost = acts.stream()
                    .map(Activity::getPrice)
                    .reduce(BigDecimal.ZERO, BigDecimal::add)
                    .setScale(2, RoundingMode.HALF_UP);
            total = total.add(dayCost);
            days.add(DayPlan.builder().date(d).activities(acts).dayCost(dayCost).build());
        }

        if (days.isEmpty()) {
            // 单日行程：start 当天
            List<Activity> acts = buildDayActivities(dest, pref, start, pressure);
            BigDecimal dayCost = acts.stream().map(Activity::getPrice).reduce(BigDecimal.ZERO, BigDecimal::add);
            total = dayCost.setScale(2, RoundingMode.HALF_UP);
            days.add(DayPlan.builder().date(start).activities(acts).dayCost(total).build());
        }

        state.setActivitySearchResult(ActivitySearchResult.builder()
                .dayPlans(days)
                .totalCost(total.setScale(2, RoundingMode.HALF_UP))
                .build());

        log.info("活动规划: {} 天，活动总费用≈{}", days.size(), total);
    }

    private List<Activity> buildDayActivities(Destination dest, UserPreferences pref, LocalDate date, int pressure) {
        List<Activity> list = new ArrayList<>();
        String city = dest.getCity();
        list.add(Activity.builder()
                .name(city + "城市漫步")
                .category("观光")
                .price(BigDecimal.ZERO)
                .duration("2小时")
                .timeSlot("上午")
                .build());

        if (pressure < 2) {
            list.add(Activity.builder()
                    .name(city + "经典景点联票")
                    .category("门票")
                    .price(BigDecimal.valueOf(pressure == 0 ? 220 : 160))
                    .duration("3小时")
                    .timeSlot("下午")
                    .build());
        }

        list.add(Activity.builder()
                .name("当地特色餐饮体验")
                .category("美食")
                .price(BigDecimal.valueOf(pressure == 0 ? 180 : (pressure == 1 ? 120 : 80)))
                .duration("1.5小时")
                .timeSlot("晚间")
                .build());

        if (pressure == 0 && pref.getInterests() != null && pref.getInterests().stream().anyMatch(i -> i.contains("购物"))) {
            list.add(Activity.builder()
                    .name("商圈购物时间")
                    .category("购物")
                    .price(BigDecimal.valueOf(300))
                    .duration("2小时")
                    .timeSlot("下午")
                    .build());
        }

        return list;
    }
}

package com.travel.agent;

import com.travel.exception.TravelValidationException;
import com.travel.model.PlanningState;
import com.travel.model.TravelPlanState;
import com.travel.model.TravelStyle;
import com.travel.model.UserPreferences;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/**
 * 偏好智能体：校验 + 丰富默认值。
 * <p>
 * 职责单一（SRP）：不决定目的地，只保证后续 Agent 拿到一致、合法的偏好视图。
 * 使用「卫语句」提前返回错误，避免深层嵌套。
 * </p>
 */
@Component
public class PreferenceAgent extends BaseAgent {

    private static final Map<TravelStyle, List<String>> DEFAULT_INTERESTS = new EnumMap<>(TravelStyle.class);

    static {
        DEFAULT_INTERESTS.put(TravelStyle.RELAXED, List.of("海滩", "SPA", "美食"));
        DEFAULT_INTERESTS.put(TravelStyle.ADVENTURE, List.of("徒步", "潜水", "攀岩"));
        DEFAULT_INTERESTS.put(TravelStyle.CULTURE, List.of("博物馆", "历史建筑", "当地市集"));
        DEFAULT_INTERESTS.put(TravelStyle.LUXURY, List.of("米其林", "精品购物", "私人导览"));
        DEFAULT_INTERESTS.put(TravelStyle.BUDGET_FRIENDLY, List.of("免费景点", "公共交通", "街头小吃"));
    }

    @Override
    protected void execute(TravelPlanState state) {
        UserPreferences p = state.getPreferences();

        if (p.getStyle() == null) {
            p.setStyle(TravelStyle.RELAXED);
            log.warn("未指定旅行风格，默认 RELAXED");
        }

        if (p.getInterests().isEmpty()) {
            List<String> defs = DEFAULT_INTERESTS.getOrDefault(p.getStyle(), List.of("观光", "美食"));
            p.setInterests(new ArrayList<>(defs));
            log.warn("兴趣列表为空，已按风格 {} 填充默认兴趣", p.getStyle());
        }

        state.setPlanningState(PlanningState.PREFERENCES_READY);
    }

    private void fail(TravelPlanState state, String msg) {
        log.warn("PreferenceAgent 校验失败: {}", msg);
        state.setPlanningState(PlanningState.FAILED);
        state.setErrorMessage(msg);
    }
}

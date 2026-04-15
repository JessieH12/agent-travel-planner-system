package com.travel.agent;

import com.travel.exception.TravelValidationException;
import com.travel.model.*;
import com.travel.service.TravelPersonaService;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.converter.BeanOutputConverter;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.temporal.ChronoUnit;
import java.util.*;

/**
 * 偏好智能体：校验 + 丰富默认值。
 * <p>
 * 职责单一（SRP）：不决定目的地，只保证后续 Agent 拿到一致、合法的偏好视图。
 * 使用「卫语句」提前返回错误，避免深层嵌套。
 * </p>
 */
@Component
public class PreferenceAgent extends BaseAgent {

    private final TravelPersonaService travelPersonaService;

    private static final Map<TravelStyle, List<String>> DEFAULT_INTERESTS = new EnumMap<>(TravelStyle.class);

    static {
        DEFAULT_INTERESTS.put(TravelStyle.RELAXED, List.of("海滩", "SPA", "美食"));
        DEFAULT_INTERESTS.put(TravelStyle.ADVENTURE, List.of("徒步", "潜水", "攀岩"));
        DEFAULT_INTERESTS.put(TravelStyle.CULTURE, List.of("博物馆", "历史建筑", "当地市集"));
        DEFAULT_INTERESTS.put(TravelStyle.LUXURY, List.of("米其林", "精品购物", "私人导览"));
        DEFAULT_INTERESTS.put(TravelStyle.BUDGET_FRIENDLY, List.of("免费景点", "公共交通", "街头小吃"));
    }

    public PreferenceAgent(TravelPersonaService travelPersonaService) {
        this.travelPersonaService = travelPersonaService;
    }


    @Override
    protected void execute(TravelPlanState state) {
        if (state.getPlanningState() == PlanningState.FAILED) {
            return;
        }

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

        normalizeBasicPreferences(p);

        try {
            TravelPersona persona;
            if (hasMeaningfulNotes(p)) {
                persona = travelPersonaService.analyze(p);
                log.info("PreferenceAgent 已完成 LLM Persona 分析");
            } else {
                persona = travelPersonaService.buildHeuristicPersona(p);
                log.info("PreferenceAgent 未提供 userNotes，使用规则版 Persona");
            }

            state.setPersona(persona);
            mergePersonaTagsIntoInterests(p, persona);
            state.setPlanningState(PlanningState.PREFERENCES_READY);

            log.info(
                    "PreferenceAgent 完成：style={}, interests={}, pace={}, tags={}",
                    p.getStyle(),
                    p.getInterests(),
                    persona != null ? persona.getPace() : null,
                    persona != null ? persona.getExtractedTags() : null
            );

        } catch (Exception e) {
            log.error("PreferenceAgent 调用 LLM 失败，降级为规则 Persona", e);

            TravelPersona fallback = travelPersonaService.buildHeuristicPersona(p);
            state.setPersona(fallback);
            mergePersonaTagsIntoInterests(p, fallback);
            state.setPlanningState(PlanningState.PREFERENCES_READY);
        }


        // state.setPlanningState(PlanningState.PREFERENCES_READY);
    }

    private void normalizeBasicPreferences(UserPreferences p) {
        if (p.getStyle() == null) {
            p.setStyle(TravelStyle.RELAXED);
            log.warn("未指定旅行风格，默认 RELAXED");
        }

        if (p.getInterests() == null) {
            p.setInterests(new ArrayList<>());
        }

        if (p.getInterests().isEmpty()) {
            List<String> defs = DEFAULT_INTERESTS.getOrDefault(p.getStyle(), List.of("观光", "美食"));
            p.setInterests(new ArrayList<>(defs));
            log.warn("兴趣列表为空，已按风格 {} 填充默认兴趣", p.getStyle());
        }
    }

    private boolean hasMeaningfulNotes(UserPreferences p) {
        return p.getUserNotes() != null && !p.getUserNotes().isBlank();
    }

    private void mergePersonaTagsIntoInterests(UserPreferences p, TravelPersona persona) {
        if (persona == null || persona.getExtractedTags() == null || persona.getExtractedTags().isEmpty()) {
            return;
        }

        Set<String> merged = new LinkedHashSet<>();
        if (p.getInterests() != null) {
            merged.addAll(p.getInterests());
        }
        merged.addAll(persona.getExtractedTags());

        p.setInterests(new ArrayList<>(merged));
    }

    private void fail(TravelPlanState state, String msg) {
        log.warn("PreferenceAgent 校验失败: {}", msg);
        state.setPlanningState(PlanningState.FAILED);
        state.setErrorMessage(msg);
    }
}

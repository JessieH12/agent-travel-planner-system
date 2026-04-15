package com.travel.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.travel.config.TravelLlmProperties;
import com.travel.model.TravelPersona;
import com.travel.model.TravelStyle;
import com.travel.model.UserPreferences;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClient;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Service
public class TravelPersonaService {

    private final ObjectMapper objectMapper;
    private final TravelLlmProperties llmProperties;
    private final RestClient restClient;

    public TravelPersonaService(ObjectMapper objectMapper, TravelLlmProperties llmProperties) {
        this.objectMapper = objectMapper;
        this.llmProperties = llmProperties;
        this.restClient = RestClient.builder()
                .baseUrl(llmProperties.getBaseUrl())
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .build();
    }

    @Cacheable(
            value = "personaAnalysis",
            key = "T(String).valueOf(#preferences.style) + '|' + " +
                    "T(String).valueOf(#preferences.departureCity) + '|' + " +
                    "T(String).valueOf(#preferences.travelers) + '|' + " +
                    "T(String).valueOf(#preferences.budget) + '|' + " +
                    "T(String).valueOf(#preferences.userNotes)"
    )
    public TravelPersona analyze(UserPreferences preferences) {
        if (!llmProperties.isEnabled() || !StringUtils.hasText(llmProperties.getApiKey())) {
            return buildHeuristicPersona(preferences);
        }

        Map<String, Object> requestBody = Map.of(
                "model", llmProperties.getModel(),
                "temperature", 0.2,
                "messages", List.of(
                        Map.of("role", "system", "content", buildSystemPrompt()),
                        Map.of("role", "user", "content", buildUserPrompt(preferences))
                )
        );

        JsonNode response = restClient.post()
                .uri("/chat/completions")
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + llmProperties.getApiKey())
                .body(requestBody)
                .retrieve()
                .body(JsonNode.class);

        String content = response.at("/choices/0/message/content").asText(null);
        if (!StringUtils.hasText(content)) {
            throw new IllegalStateException("LLM 未返回 persona 内容");
        }

        TravelPersona persona = parsePersona(content);
        return sanitize(persona, preferences);
    }

    public TravelPersona buildHeuristicPersona(UserPreferences preferences) {
        TravelPersona persona = new TravelPersona();

        persona.setPace(inferPace(preferences));

        Set<String> tags = new LinkedHashSet<>();
        if (preferences.getInterests() != null) {
            tags.addAll(preferences.getInterests());
        }

        String notes = safeLower(preferences.getUserNotes());

        if (containsAny(notes, "海边", "海滩", "海岛", "看海")) {
            tags.add("海滨度假");
        }
        if (containsAny(notes, "海鲜", "生蚝", "刺身")) {
            tags.add("海鲜美食");
        }
        if (containsAny(notes, "老人", "长辈", "父母")) {
            tags.add("长辈友好");
        }
        if (containsAny(notes, "小孩", "孩子", "亲子")) {
            tags.add("亲子友好");
        }
        if (containsAny(notes, "不要爬山", "不想爬山", "不爬山", "不徒步")) {
            tags.add("低体力活动");
        }
        if (containsAny(notes, "预算别太高", "预算不高", "省钱", "性价比")) {
            tags.add("高性价比");
        }
        if (containsAny(notes, "休闲", "轻松", "慢一点", "慢节奏")) {
            tags.add("慢节奏");
        }

        persona.setExtractedTags(new ArrayList<>(tags));
        persona.setSpecialCare(buildSpecialCare(notes));
        persona.setSummary(buildSummary(preferences, persona));

        return persona;
    }

    private TravelPersona parsePersona(String rawContent) {
        try {
            String cleaned = stripMarkdownFence(rawContent).trim();
            String json = extractJsonObject(cleaned);
            return objectMapper.readValue(json, TravelPersona.class);
        } catch (Exception e) {
            throw new IllegalStateException("LLM Persona JSON 解析失败: " + rawContent, e);
        }
    }

    private TravelPersona sanitize(TravelPersona persona, UserPreferences preferences) {
        if (persona == null) {
            persona = new TravelPersona();
        }

        if (!StringUtils.hasText(persona.getPace())) {
            persona.setPace(inferPace(preferences));
        }

        Set<String> tags = new LinkedHashSet<>();
        if (preferences.getInterests() != null) {
            tags.addAll(preferences.getInterests());
        }
        if (persona.getExtractedTags() != null) {
            for (String tag : persona.getExtractedTags()) {
                if (StringUtils.hasText(tag)) {
                    tags.add(tag.trim());
                }
            }
        }
        persona.setExtractedTags(new ArrayList<>(tags));

        if (!StringUtils.hasText(persona.getSpecialCare())) {
            persona.setSpecialCare(buildSpecialCare(safeLower(preferences.getUserNotes())));
        }

        if (!StringUtils.hasText(persona.getSummary())) {
            persona.setSummary(buildSummary(preferences, persona));
        }

        return persona;
    }

    private String buildSystemPrompt() {
        return """
                你是一名资深旅游偏好分析师，也是一个擅长自然语言理解的旅行“心理分析师”。
                你的任务不是重复用户原话，而是提炼真正会影响行程推荐的深层画像。
                
                你必须严格输出 JSON，对应字段如下：
                {
                  "pace": "极度休闲/适中/紧凑特种兵 之一",
                  "extractedTags": ["标签1", "标签2"],
                  "specialCare": "特殊注意事项，没有则写 无",
                  "summary": "一句导游级总结"
                }
                
                要求：
                1. 只输出 JSON，不要输出解释、前后缀、Markdown。
                2. extractedTags 要尽量是下游可消费的旅游标签，例如：
                   长辈友好、亲子友好、海滨度假、海鲜美食、低体力活动、高性价比、夜生活、文化深度游、购物偏好、拍照出片。
                3. 若用户明确提到老人/小孩/过敏/不想爬山/节奏慢/预算敏感等，要体现在 specialCare 和 extractedTags 中。
                4. pace 结合用户风格、人数、备注综合判断。
                """;
    }

    private String buildUserPrompt(UserPreferences preferences) {
        try {
            Map<String, Object> compact = Map.of(
                    "budget", preferences.getBudget(),
                    "style", preferences.getStyle(),
                    "departureCity", preferences.getDepartureCity(),
                    "travelers", preferences.getTravelers(),
                    "interests", preferences.getInterests(),
                    "userNotes", preferences.getUserNotes(),
                    "startDate", preferences.getStartDate(),
                    "endDate", preferences.getEndDate()
            );

            return """
                    请根据以下用户旅行偏好，生成 TravelPersona JSON。
                    注意：你要挖掘隐藏约束，而不只是照抄原文。
                    
                    用户输入：
                    %s
                    """.formatted(objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(compact));
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("构造 LLM Prompt 失败", e);
        }
    }

    private String inferPace(UserPreferences preferences) {
        TravelStyle style = preferences.getStyle();
        String notes = safeLower(preferences.getUserNotes());

        if (containsAny(notes, "慢一点", "轻松", "休闲", "不要太赶", "老人")) {
            return "极度休闲";
        }
        if (style == TravelStyle.ADVENTURE) {
            return "紧凑特种兵";
        }
        if (style == TravelStyle.LUXURY || style == TravelStyle.RELAXED) {
            return "极度休闲";
        }
        return "适中";
    }

    private String buildSpecialCare(String notes) {
        List<String> cares = new ArrayList<>();

        if (containsAny(notes, "老人", "长辈", "父母")) {
            cares.add("优先无障碍、少换乘、少步行");
        }
        if (containsAny(notes, "小孩", "孩子", "亲子")) {
            cares.add("优先亲子友好和安全性高的活动");
        }
        if (containsAny(notes, "不要爬山", "不想爬山", "不爬山", "不徒步")) {
            cares.add("避开高强度徒步、爬山、长距离拉练");
        }
        if (containsAny(notes, "海鲜过敏", "过敏")) {
            cares.add("注意饮食过敏源");
        }
        if (containsAny(notes, "预算别太高", "预算不高", "省钱", "性价比")) {
            cares.add("优先控制餐饮、酒店与活动成本");
        }

        if (cares.isEmpty()) {
            return "无";
        }
        return String.join("；", cares);
    }

    private String buildSummary(UserPreferences preferences, TravelPersona persona) {
        String style = preferences.getStyle() != null ? preferences.getStyle().name() : "RELAXED";
        String pace = persona.getPace() != null ? persona.getPace() : "适中";
        int travelers = preferences.getTravelers();

        return "这是一个偏%s、%d人出行、整体节奏%s，并兼顾%s的旅行画像。"
                .formatted(
                        style,
                        travelers,
                        pace,
                        persona.getExtractedTags() == null || persona.getExtractedTags().isEmpty()
                                ? "基础观光需求"
                                : String.join("、", persona.getExtractedTags().stream().limit(3).toList())
                );
    }

    private String safeLower(String text) {
        return text == null ? "" : text.trim().toLowerCase();
    }

    private boolean containsAny(String text, String... patterns) {
        if (!StringUtils.hasText(text)) {
            return false;
        }
        for (String pattern : patterns) {
            if (text.contains(pattern.toLowerCase())) {
                return true;
            }
        }
        return false;
    }

    private String stripMarkdownFence(String text) {
        return text.replace("```json", "")
                .replace("```JSON", "")
                .replace("```", "")
                .trim();
    }

    private String extractJsonObject(String text) {
        int start = text.indexOf('{');
        int end = text.lastIndexOf('}');
        if (start >= 0 && end > start) {
            return text.substring(start, end + 1);
        }
        return text;
    }
}
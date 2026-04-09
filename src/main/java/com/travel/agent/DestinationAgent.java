package com.travel.agent;

import com.travel.model.Destination;
import com.travel.model.PlanningState;
import com.travel.model.TravelPlanState;
import com.travel.model.TravelStyle;
import com.travel.model.UserPreferences;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

/**
 * 目的地智能体：基于 mock 知识库的打分与推荐。
 * <p>
 * 城市集合与 Python 侧对齐：东京、曼谷、巴黎、清迈、首尔、大阪。
 * 面试点：真实系统可替换为 RAG/规则引擎/学习排序；此处用确定性规则便于单测与演示。
 * </p>
 */
@Component
public class DestinationAgent extends BaseAgent {

    @Override
    protected void execute(TravelPlanState state) {
        if (state.getPlanningState() == PlanningState.FAILED) {
            return;
        }
        UserPreferences pref = state.getPreferences();
        List<Destination> catalog = buildCatalog();
        Destination best = catalog.stream()
                .max(Comparator.comparingDouble(d -> score(d, pref)))
                .orElse(catalog.getFirst());
        state.setSelectedDestination(best);
        state.setPlanningState(PlanningState.DESTINATION_SELECTED);
        log.info("推荐目的地: {} ({})", best.getCity(), best.getCountry());
    }

    private double score(Destination d, UserPreferences pref) {
        double s = d.getSafetyScore() * 10;
        TravelStyle style = pref.getStyle();
        String city = d.getCity();

        // 风格加权（mock）
        switch (style) {
            case CULTURE -> {
                if (city.contains("巴黎") || city.contains("京都") || city.contains("首尔")) {
                    s += 25;
                }
            }
            case ADVENTURE -> {
                if (city.contains("清迈") || city.contains("曼谷")) {
                    s += 22;
                }
            }
            case LUXURY -> {
                if (city.contains("巴黎") || city.contains("东京")) {
                    s += 20;
                }
            }
            case BUDGET_FRIENDLY -> {
                if (city.contains("清迈") || city.contains("曼谷")) {
                    s += 24;
                }
            }
            case RELAXED -> {
                if (city.contains("大阪") || city.contains("曼谷")) {
                    s += 18;
                }
            }
            default -> s += 5;
        }

        // 兴趣关键词简单匹配（mock）
        List<String> interests = pref.getInterests();
        if (interests != null) {
            for (String hi : d.getHighlights()) {
                for (String in : interests) {
                    if (in != null && hi.toLowerCase(Locale.ROOT).contains(in.toLowerCase(Locale.ROOT))) {
                        s += 8;
                    }
                }
            }
        }
        return s;
    }

    private List<Destination> buildCatalog() {
        List<Destination> list = new ArrayList<>();
        list.add(Destination.builder()
                .city("东京")
                .country("日本")
                .description("都市潮流与传统神社共存")
                .highlights(List.of("涩谷", "浅草寺", "美食", "购物"))
                .safetyScore(9.2)
                .build());
        list.add(Destination.builder()
                .city("曼谷")
                .country("泰国")
                .description("热带风情与夜市文化")
                .highlights(List.of("大皇宫", "街头小吃", "SPA", "湄南河"))
                .safetyScore(7.8)
                .build());
        list.add(Destination.builder()
                .city("巴黎")
                .country("法国")
                .description("艺术与浪漫之都")
                .highlights(List.of("卢浮宫", "博物馆", "米其林", "历史建筑"))
                .safetyScore(8.0)
                .build());
        list.add(Destination.builder()
                .city("清迈")
                .country("泰国")
                .description("古城与山林慢生活")
                .highlights(List.of("古城徒步", "夜市", "寺庙", "丛林飞跃"))
                .safetyScore(8.5)
                .build());
        list.add(Destination.builder()
                .city("首尔")
                .country("韩国")
                .description("韩流、购物与美食")
                .highlights(List.of("景福宫", "购物", "街头小吃", "博物馆"))
                .safetyScore(8.8)
                .build());
        list.add(Destination.builder()
                .city("大阪")
                .country("日本")
                .description("美食之都，适合家庭轻松游")
                .highlights(List.of("道顿堀", "USJ", "美食", "观光"))
                .safetyScore(9.0)
                .build());
        return list;
    }
}

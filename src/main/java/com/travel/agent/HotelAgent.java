package com.travel.agent;

import com.travel.model.Destination;
import com.travel.model.Hotel;
import com.travel.model.HotelSearchResult;
import com.travel.model.PlanningState;
import com.travel.model.TravelStyle;
import com.travel.model.TravelPlanState;
import com.travel.model.UserPreferences;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * 酒店智能体：mock 生成多档酒店并按星级/单价/设施丰富度打分。
 * <p>
 * 预算压力升高时降低 mock 基准价与星级上限，体现「渐进式调整」对供给侧的影响。
 * </p>
 */
@Component
public class HotelAgent extends BaseAgent {

    @Override
    protected void execute(TravelPlanState state) {
        if (state.getPlanningState() == PlanningState.FAILED) {
            return;
        }
        UserPreferences pref = state.getPreferences();
        Destination dest = state.getSelectedDestination();
        if (pref == null || dest == null) {
            log.warn("HotelAgent 跳过：缺少偏好或目的地");
            return;
        }

        int pressure = state.getBudgetPressureLevel();
        long nights = Math.max(1, ChronoUnit.DAYS.between(pref.getStartDate(), pref.getEndDate()));
        int travelers = Math.max(1, pref.getTravelers());
        int rooms = Math.max(1, (travelers + 1) / 2);
        String city = dest.getCity();

        List<Hotel> hotels = new ArrayList<>();
        hotels.add(hotel("臻选·" + city + "套房酒店", city, 5, 1880, pressure, List.of("泳池", "行政酒廊", "健身房")));
        hotels.add(hotel("舒适·" + city + "商务酒店", city, 4, 980, pressure, List.of("早餐", "洗衣", "会议室")));
        hotels.add(hotel("经济·" + city + "旅舍Plus", city, 3, 420, pressure, List.of("WiFi", "公共厨房")));

        Hotel recommended = hotels.stream()
                .max(Comparator.comparingDouble(h -> hotelScore(h, pref, pressure)))
                .orElse(hotels.getFirst());

        BigDecimal totalCost = recommended.getPricePerNight()
                .multiply(BigDecimal.valueOf(nights))
                .multiply(BigDecimal.valueOf(rooms))
                .setScale(2, RoundingMode.HALF_UP);

        state.setHotelSearchResult(HotelSearchResult.builder()
                .hotels(hotels)
                .recommended(recommended)
                .totalCost(totalCost)
                .build());

        log.info("酒店推荐: {}，{} 晚 × {} 间，预估={}", recommended.getName(), nights, rooms, totalCost);
    }

    private Hotel hotel(String name, String city, int stars, int baseCny, int pressure, List<String> amenities) {
        int effStars = Math.max(2, stars - Math.min(2, pressure));
        double priceFactor = switch (pressure) {
            case 0 -> 1.0;
            case 1 -> 0.85;
            default -> 0.7;
        };
        BigDecimal price = BigDecimal.valueOf(Math.round(baseCny * priceFactor));
        return Hotel.builder()
                .name(name)
                .city(city)
                .starRating(effStars)
                .pricePerNight(price)
                .amenities(amenities)
                .build();
    }

    private double hotelScore(Hotel h, UserPreferences pref, int pressure) {
        double starW = pref.getStyle() == TravelStyle.LUXURY ? 120 : 70;
        double stars = h.getStarRating() * starW;
        double cheapBonus = pressure > 0 ? 3000.0 / (h.getPricePerNight().doubleValue() + 1) : 0;
        double amenity = h.getAmenities() != null ? h.getAmenities().size() * 15 : 0;
        return stars + amenity + cheapBonus - h.getPricePerNight().doubleValue() * (pressure > 0 ? 0.15 : 0.05);
    }
}

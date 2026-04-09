package com.travel.agent;

import com.travel.model.Destination;
import com.travel.model.Flight;
import com.travel.model.FlightSearchResult;
import com.travel.model.PlanningState;
import com.travel.model.TravelPlanState;
import com.travel.model.UserPreferences;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * 航班智能体：mock 生成候选航班并按「价格/时长/经停」综合打分选推荐。
 * <p>
 * {@link TravelPlanState#getBudgetPressureLevel()} 越大，mock 基准价越低、经停可能越多——模拟「降级搜票」。
 * 并行执行时仅写入 {@link FlightSearchResult}，不修改其他 Agent 字段，避免竞态。
 * </p>
 */
@Component
public class FlightAgent extends BaseAgent {

    @Override
    protected void execute(TravelPlanState state) {
        if (state.getPlanningState() == PlanningState.FAILED) {
            return;
        }
        UserPreferences pref = state.getPreferences();
        Destination dest = state.getSelectedDestination();
        if (pref == null || dest == null) {
            log.warn("FlightAgent 跳过：缺少偏好或目的地");
            return;
        }

        int pressure = state.getBudgetPressureLevel();
        String from = pref.getDepartureCity();
        String to = dest.getCity();
        int travelers = Math.max(1, pref.getTravelers());

        List<Flight> flights = new ArrayList<>();
        flights.add(mockFlight("NH", "NH900", basePrice(4200, pressure), "5h20m", pressure >= 2 ? 1 : 0, from, to));
        flights.add(mockFlight("TG", "TG601", basePrice(3100, pressure), "6h10m", 1, from, to));
        flights.add(mockFlight("CA", "CA123", basePrice(2800, pressure), "8h40m", 2, from, to));

        Flight recommended = flights.stream()
                .max(Comparator.comparingDouble(f -> flightScore(f, pressure)))
                .orElse(flights.getFirst());

        BigDecimal roundTripPerPerson = recommended.getPrice().multiply(BigDecimal.valueOf(2));
        BigDecimal totalCost = roundTripPerPerson
                .multiply(BigDecimal.valueOf(travelers))
                .setScale(2, RoundingMode.HALF_UP);

        state.setFlightSearchResult(FlightSearchResult.builder()
                .flights(flights)
                .recommended(recommended)
                .totalCost(totalCost)
                .build());

        log.info("航班推荐: {} {}，预估总费用={}", recommended.getAirline(), recommended.getFlightNo(), totalCost);
    }

    private Flight mockFlight(String airline, String no, BigDecimal price, String duration, int stops,
                              String from, String to) {
        return Flight.builder()
                .airline(airline)
                .flightNo(no + "(" + from + "-" + to + ")")
                .price(price)
                .duration(duration)
                .stops(stops)
                .build();
    }

    private BigDecimal basePrice(int base, int pressure) {
        double factor = switch (pressure) {
            case 0 -> 1.0;
            case 1 -> 0.88;
            default -> 0.75;
        };
        return BigDecimal.valueOf(Math.round(base * factor));
    }

    /** 分数越高越推荐：偏好直飞/短时长，压力高时更在意低价 */
    private double flightScore(Flight f, int pressure) {
        double price = f.getPrice().doubleValue();
        double durationPenalty = parseHours(f.getDuration()) * (pressure >= 1 ? 2 : 4);
        double stopPenalty = f.getStops() * (pressure >= 2 ? 80 : 200);
        return 50000 / (price + 1) - durationPenalty - stopPenalty;
    }

    private double parseHours(String duration) {
        try {
            int h = duration.indexOf('h');
            int m = duration.indexOf('m');
            int hours = Integer.parseInt(duration.substring(0, h).trim());
            int mins = Integer.parseInt(duration.substring(h + 1, m).trim());
            return hours + mins / 60.0;
        } catch (Exception e) {
            return 6;
        }
    }
}

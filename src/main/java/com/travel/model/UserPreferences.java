package com.travel.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/**
 * 用户偏好（API 入参核心模型）。
 * <p>
 * 设计模式：DTO + Builder（Lombok），便于 JSON 反序列化与测试构造；
 * 日期使用 {@code yyyy-MM-dd} 与前端约定一致。
 * </p>
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserPreferences {

    /** 总预算（货币单位由业务约定，此处为抽象金额） */
    private BigDecimal budget;

    private TravelStyle style;

    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate startDate;

    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate endDate;

    /** 出发城市 */
    private String departureCity;

    /** 出行人数 */
    private int travelers;

    /** 兴趣标签，可为空，由 PreferenceAgent 补默认 */
    @Builder.Default
    private List<String> interests = new ArrayList<>();
}

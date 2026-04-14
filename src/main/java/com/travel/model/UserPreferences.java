package com.travel.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.*;
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
@Schema(description = "用户旅行偏好请求体")
public class UserPreferences {

    /** 总预算（货币单位由业务约定，此处为抽象金额） */
    @NotNull(message = "预算不能为空")
    @DecimalMin(value = "1000.0", message = "预算最少需要 1000 元")
    @Schema(description = "总预算(人民币)", example = "15000")
    private BigDecimal budget;

    @NotNull(message = "出发风格不能为空")
    @Schema(description = "出发风格", example = "RELAXED")
    private TravelStyle style;

    @NotNull(message = "出发日期不能为空")
    @Schema(description = "出发日期", example = "2024-01-01")
    @FutureOrPresent(message = "出发日期不能早于今天")
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate startDate;

    @NotNull(message = "结束日期不能为空")
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Schema(description = "结束日期", example = "2024-01-07")
    private LocalDate endDate;

    /** 出发城市 */
    @NotBlank(message = "出发城市不能为空")
    @Schema(description = "出发城市", example = "上海")
    private String departureCity;

    /** 出行人数 */
    @Min(value = 1, message = "出行人数至少为 1 人")
    @Schema(description = "出行人数", example = "2")
    private int travelers;

    /** 兴趣标签，可为空，由 PreferenceAgent 补默认 */
    @Builder.Default
    @Schema(description = "兴趣标签", example = "[\"历史\", \"文化\", \"自然\"]")
    private List<String> interests = new ArrayList<>();

    /**
     * 跨字段校验：结束日期必须晚于开始日期
     * 注意：方法名必须以 is 开头（比如 isValidDateRange），
     * 这样 Spring 校验器就会把它当成一个名为 validDateRange 的虚拟字段进行收集。
     */
    @AssertTrue(message = "行程天数至少为 1 天（结束日应晚于开始日）")
    @Schema(description = "行程天数至少为 1 天（结束日应晚于开始日）", example = "true")
    public boolean isValidDateRange() {
        // 如果 startDate 或 endDate 为空，说明用户没填，让上面的 @NotNull 去报错
        // 我们这里返回 true 放行，只在两者都有值的情况下校验逻辑
        if (startDate == null || endDate == null) {
            return true;
        }
        return endDate.isAfter(startDate);
    }
}

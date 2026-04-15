package com.travel.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;
import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class TravelPersona {
    private String pace;             // 行程节奏（如：极度休闲、适中、紧凑特种兵）
    private List<String> extractedTags; // 大模型从备注中提取的深层兴趣标签
    private String specialCare;      // 特殊注意事项（如：避开高强度运动、注意海鲜过敏）
    private String summary;          // 导游级的一句话总结
}
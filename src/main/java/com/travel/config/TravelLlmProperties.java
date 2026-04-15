package com.travel.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "travel.llm")
public class TravelLlmProperties {

    /**
     * 是否启用真实 LLM 分析
     */
    private boolean enabled = true;

    /**
     * 兼容 OpenAI 风格接口的 base URL
     * 例如：https://api.openai.com/v1
     */
    private String baseUrl = "https://dashscope.aliyuncs.com/compatible-mode/v1";

    /**
     * API Key
     */
    private String apiKey = "";

    /**
     * 模型名，可根据你的供应商替换
     * 例如：gpt-4.1-mini / deepseek-chat / qwen-max 等
     */
    private String model = "qwen3.5-plus";
}
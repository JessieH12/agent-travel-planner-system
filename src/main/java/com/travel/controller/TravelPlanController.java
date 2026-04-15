package com.travel.controller;

import com.travel.model.PlanningState;
import com.travel.model.TravelPlanState;
import com.travel.model.UserPreferences;
import com.travel.service.TravelPlanService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.openai.OpenAiChatOptions;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * REST 控制器：健康检查 + 规划接口。
 * <p>
 * {@code POST /api/plan} 入参为 {@link UserPreferences} JSON；
 * 校验失败时流水线将 {@link TravelPlanState#getPlanningState()} 置为 {@link PlanningState#FAILED}，
 * 此处返回 400 更符合 HTTP 语义。
 * </p>
 */
@RestController
@RequestMapping("/api")
@Tag(name = "旅游规划服务", description = "多智能体协作的行程规划核心 API")
public class TravelPlanController {

    private final TravelPlanService travelPlanService;

    private final ChatClient.Builder chatClientBuilder;

    public TravelPlanController(TravelPlanService travelPlanService, ChatClient.Builder chatClientBuilder) {
        this.travelPlanService = travelPlanService;
        this.chatClientBuilder = chatClientBuilder;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "UP", "service", "travel-planner");
    }

    @PostMapping("/plan")
    @Operation(summary = "生成智能行程规划", description = "根据用户的预算、人数、风格等偏好，通过多Agent协同生成最优化行程。")
    public ResponseEntity<TravelPlanState> plan(@Valid @RequestBody UserPreferences preferences) {
        TravelPlanState state = travelPlanService.plan(preferences);
        if (state.getPlanningState() == PlanningState.FAILED) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(state);
        }
        return ResponseEntity.ok(state);
    }

    @GetMapping("/debug/llm")
    @Operation(summary = "测试大模型连通性", description = "用于验证 Spring AI 是否已正确连接到 DashScope/Qwen")
    public ResponseEntity<?> testLlm() {
        try {
            ChatClient chatClient = chatClientBuilder.build();

            String result = chatClient.prompt()
                    .user("请只回复：Spring AI 已连接成功")
                    .options(OpenAiChatOptions.builder()
                            .withModel("qwen3.5-plus")
                            .withTemperature(0.2)
                            .build())
                    .call()
                    .content();

            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "model", "qwen-plus",
                    "result", result
            ));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                    "success", false,
                    "error", e.getClass().getName(),
                    "message", e.getMessage()
            ));
        }
    }
}

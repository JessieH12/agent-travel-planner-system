package com.travel.orchestrator;

import com.travel.agent.DestinationAgent;
import com.travel.agent.PreferenceAgent;
import com.travel.model.PlanningState;
import com.travel.model.TravelPlanState;
import com.travel.model.UserPreferences;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * 总编排流水线：Preference → Destination → BudgetLoop（内含并行与预算反馈）。
 * <p>
 * 架构总结（可面试口述）：
 * <ol>
 *     <li><b>顺序阶段</b>：偏好与目的地存在数据依赖，必须串行；</li>
 *     <li><b>并行阶段</b>：航班/酒店/活动在 mock 假设下互不依赖，可 {@code allOf}；</li>
 *     <li><b>循环阶段</b>：预算 Agent 作为「守卫」，超支则抬高 {@code budgetPressureLevel} 再检索。</li>
 * </ol>
 * 该混合模式在真实系统中可映射为 DAG 工作流引擎或 Temporal/Camunda 等编排工具。
 * </p>
 */
@Component
public class TravelPlanningPipeline {

    private static final Logger log = LoggerFactory.getLogger(TravelPlanningPipeline.class);

    private final PreferenceAgent preferenceAgent;
    private final DestinationAgent destinationAgent;
    private final BudgetLoopController budgetLoopController;

    public TravelPlanningPipeline(
            PreferenceAgent preferenceAgent,
            DestinationAgent destinationAgent,
            BudgetLoopController budgetLoopController) {
        this.preferenceAgent = preferenceAgent;
        this.destinationAgent = destinationAgent;
        this.budgetLoopController = budgetLoopController;
    }

    /**
     * @param rawPreferences 来自 API 的原始偏好（会被各 Agent 读取/补全）
     * @return 聚合后的规划状态
     */
    public TravelPlanState execute(UserPreferences rawPreferences) {
        TravelPlanState state = TravelPlanState.builder()
                .preferences(rawPreferences)
                .planningState(PlanningState.INITIAL)
                .adjustmentRound(0)
                .budgetPressureLevel(0)
                .build();

        log.info("流水线开始：PreferenceAgent");
        preferenceAgent.run(state);
        if (state.getPlanningState() == PlanningState.FAILED) {
            return state;
        }

        log.info("流水线：DestinationAgent");
        destinationAgent.run(state);
        if (state.getPlanningState() == PlanningState.FAILED) {
            return state;
        }

        log.info("流水线：BudgetLoop（并行 + 预算）");
        budgetLoopController.run(state);

        if (state.getPlanningState() != PlanningState.FAILED) {
            state.setPlanningState(PlanningState.COMPLETE);
        }
        log.info("流水线结束，状态={}", state.getPlanningState());
        return state;
    }
}

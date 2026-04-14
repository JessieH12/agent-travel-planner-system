package com.travel.orchestrator;

import com.travel.agent.BudgetAgent;
import com.travel.model.BudgetBreakdown;
import com.travel.model.PlanningState;
import com.travel.model.TravelPlanState;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import com.travel.config.TravelProperties;

/**
 * 预算循环控制器：「并行检索 → 预算评估 → 超支则渐进调整 → 最多 3 轮」。
 * <p>
 * 面试 talking point：
 * <ul>
 *     <li>这是典型的 <b>反馈循环（Feedback Loop）</b>，与一次性流水线组合成「混合编排」；</li>
 *     <li>轮次上限防止无限重试（熔断/边界）；</li>
 *     <li>调整策略委托给 {@link BudgetAgent}，本类只负责流程控制（职责分离）。</li>
 * </ul>
 * </p>
 */
@Component
public class BudgetLoopController {

    private static final Logger log = LoggerFactory.getLogger(BudgetLoopController.class);

    private final ParallelExecutor parallelExecutor;
    private final BudgetAgent budgetAgent;
    private final int maxRounds;

    public BudgetLoopController(ParallelExecutor parallelExecutor, BudgetAgent budgetAgent, TravelProperties travelProperties) {
        this.parallelExecutor = parallelExecutor;
        this.budgetAgent = budgetAgent;
        this.maxRounds = travelProperties.getBudget().getMaxRounds();
    }

    /**
     * 执行预算闭环：可能触发多轮并行检索。
     */
    public void run(TravelPlanState state) {
        if (state.getPlanningState() == PlanningState.FAILED) {
            return;
        }
        for (int round = 0; round < this.maxRounds; round++) {
            state.setAdjustmentRound(round);
            log.info("预算循环第 {} 轮（0-based），budgetPressureLevel={}", round, state.getBudgetPressureLevel());

            parallelExecutor.runParallel(state);
            budgetAgent.evaluateAndAttach(state);

            BudgetBreakdown bd = state.getBudgetBreakdown();
            if (bd != null && bd.isWithinBudget()) {
                state.setPlanningState(PlanningState.BUDGET_RESOLVED);
                log.info("预算已通过，结束循环");
                return;
            }

            boolean lastRound = (round == this.maxRounds - 1);
            if (lastRound) {
                state.setPlanningState(PlanningState.BUDGET_RESOLVED);
                log.warn("已达最大轮次仍可能超预算，返回当前最优 mock 结果供人工决策");
                return;
            }

            if (!budgetAgent.applyProgressiveAdjustment(state)) {
                state.setPlanningState(PlanningState.BUDGET_RESOLVED);
                return;
            }
        }
    }
}

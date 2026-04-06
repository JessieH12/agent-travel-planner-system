"""
预算循环控制器 —— 反复执行"并行搜索 → 预算校验"直到预算通过或达到上限。

面试考点（高频!!!）:
  - 循环终止条件: ① 预算通过 ② 达到最大调整次数 ③ 出现不可恢复错误
  - 为什么不无限循环？ → 用户体验差、Token 消耗大、可能陷入震荡
  - 渐进式降级: 第 1 轮砍活动 → 第 2 轮降酒店 → 第 3 轮换航班
  - 与 LangGraph 的对应: 本质上是 conditional_edge + cycle，状态机的 ADJUSTING 节点
"""

from __future__ import annotations

from loguru import logger

from agents.budget_agent import BudgetAgent
from config.settings import settings
from models.schemas import PlanningState, TravelPlanState

from .parallel import ParallelExecutor


class BudgetLoopController:
    """执行"并行搜索 + 预算校验"循环，最多 max_retries 轮。"""

    def __init__(
        self,
        parallel_executor: ParallelExecutor,
        budget_agent: BudgetAgent | None = None,
        max_retries: int | None = None,
    ):
        self.parallel_executor = parallel_executor
        self.budget_agent = budget_agent or BudgetAgent()
        self.max_retries = max_retries or settings.BUDGET_MAX_RETRIES

    async def run(self, state: TravelPlanState) -> TravelPlanState:
        state.max_adjustments = self.max_retries

        for attempt in range(self.max_retries + 1):
            label = "初始搜索" if attempt == 0 else f"第 {attempt} 轮调整"
            logger.info(f"[BudgetLoop] ── {label} ──")

            if attempt == 0 or state.state == PlanningState.ADJUSTING:
                state = await self.parallel_executor.run(state)

            state.state = PlanningState.BUDGET_CHECKING
            state = await self.budget_agent.run(state)

            if state.state == PlanningState.COMPLETED:
                logger.info(f"[BudgetLoop] 在第 {attempt} 轮完成 (共尝试 {attempt + 1} 次)")
                return state

            if state.state == PlanningState.FAILED:
                logger.error("[BudgetLoop] 规划失败，退出循环")
                return state

        logger.warning(f"[BudgetLoop] 达到最大重试次数 {self.max_retries}")
        state.state = PlanningState.COMPLETED
        return state

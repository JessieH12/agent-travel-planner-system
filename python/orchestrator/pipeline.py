"""
Pipeline 编排器 —— 串联整个行程规划流程。

架构:
  用户输入 → PreferenceAgent → DestinationAgent
  → [FlightAgent + HotelAgent + ActivityAgent (并行)]
  → BudgetAgent (预算校验)
  ↓ (超预算则循环调整)
  输出最终行程

面试考点:
  - Pipeline 模式 vs DAG 模式 vs State Machine 模式的区别
  - Pipeline 模式适合本项目的原因: 流程线性+并行分叉+循环，复杂度适中
  - 错误传播: 前序 Agent 失败则后序不执行，错误信息记录在 state 中
"""

from __future__ import annotations

from loguru import logger

from agents import (
    ActivityAgent,
    BudgetAgent,
    DestinationAgent,
    FlightAgent,
    HotelAgent,
    PreferenceAgent,
)
from models.schemas import PlanningState, TravelPlanState, UserPreferences

from .budget_loop import BudgetLoopController
from .parallel import ParallelExecutor


class TravelPlanningPipeline:
    """主编排器: 串联所有 Agent 完成行程规划。"""

    def __init__(self) -> None:
        self.preference_agent = PreferenceAgent()
        self.destination_agent = DestinationAgent()
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.activity_agent = ActivityAgent()
        self.budget_agent = BudgetAgent()

        self.parallel_executor = ParallelExecutor(
            agents=[self.flight_agent, self.hotel_agent, self.activity_agent],
        )
        self.budget_loop = BudgetLoopController(
            parallel_executor=self.parallel_executor,
            budget_agent=self.budget_agent,
        )

    async def run(self, preferences: UserPreferences) -> TravelPlanState:
        state = TravelPlanState(preferences=preferences)
        logger.info("=" * 60)
        logger.info("🚀 行程规划 Pipeline 启动")
        logger.info("=" * 60)

        # ── 阶段 1: 偏好收集 ──
        state = await self.preference_agent.run(state)
        if state.state == PlanningState.FAILED:
            return state

        # ── 阶段 2: 目的地推荐 ──
        state = await self.destination_agent.run(state)
        if state.state == PlanningState.FAILED:
            return state

        # ── 阶段 3: 并行搜索 + 预算循环 ──
        state = await self.budget_loop.run(state)

        logger.info("=" * 60)
        logger.info(f"Pipeline 完成, 状态: {state.state.value}")
        if state.budget_breakdown:
            bb = state.budget_breakdown
            logger.info(f"总费用: ¥{bb.total_cost:.0f} / 预算: ¥{bb.budget:.0f}")
        logger.info("=" * 60)

        return state


async def quick_plan(
    budget: float = 10000,
    departure: str = "北京",
    start: str = "2026-05-01",
    end: str = "2026-05-05",
    style: str = "comfort",
    travelers: int = 1,
) -> TravelPlanState:
    """快速规划入口，便于 CLI / 测试调用。"""
    from models.schemas import TravelStyle

    prefs = UserPreferences(
        budget=budget,
        travel_style=TravelStyle(style),
        departure_city=departure,
        start_date=start,
        end_date=end,
        num_travelers=travelers,
    )
    pipeline = TravelPlanningPipeline()
    return await pipeline.run(prefs)

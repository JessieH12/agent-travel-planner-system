"""
Preference Agent —— 偏好收集 Agent。

职责: 通过对话或结构化输入收集用户偏好（预算/风格/时间/禁忌）。
在 Pipeline 中处于第一个节点，输出 UserPreferences 填入全局状态。

面试考点:
  - 为什么需要单独的偏好收集 Agent？ —— 关注点分离，偏好收集逻辑可能很复杂
    （多轮对话、意图识别、默认值填充），独立 Agent 方便迭代升级。
  - Mock 模式下直接使用用户传入的结构化数据，真实模式下可接入 NLU。
"""

from __future__ import annotations

from loguru import logger

from models.schemas import PlanningState, TravelPlanState, UserPreferences

from .base_agent import BaseAgent


class PreferenceAgent(BaseAgent):
    name = "PreferenceAgent"

    async def execute(self, state: TravelPlanState) -> TravelPlanState:
        if state.preferences is None:
            raise ValueError("用户偏好未提供，请先设置 state.preferences")

        pref = state.preferences

        if not pref.interests:
            pref.interests = self._default_interests(pref.travel_style.value)
            logger.info(f"[{self.name}] 自动补充兴趣标签: {pref.interests}")

        state.preferences = pref
        state.state = PlanningState.RECOMMENDING_DESTINATIONS
        return state

    @staticmethod
    def _default_interests(style: str) -> list[str]:
        mapping = {
            "budget": ["免费景点", "街头美食", "步行游览"],
            "comfort": ["经典景点", "当地美食", "文化体验"],
            "luxury": ["米其林餐厅", "私人导游", "SPA"],
            "adventure": ["徒步", "潜水", "极限运动"],
            "cultural": ["博物馆", "历史遗迹", "传统手工艺"],
            "relaxation": ["海滩", "温泉", "瑜伽"],
        }
        return mapping.get(style, ["经典景点", "美食"])

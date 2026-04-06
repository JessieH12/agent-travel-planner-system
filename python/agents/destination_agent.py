"""
Destination Agent —— 目的地推荐 Agent。

职责: 根据用户偏好推荐目的地，考虑季节、签证、安全性、性价比。
在 Pipeline 中处于第二个节点，接收 preferences，输出 DestinationRecommendation。

面试考点:
  - 推荐算法: 基于多维加权评分（预算匹配度、季节适宜度、安全评分）
  - 为什么不直接让用户选城市？ —— 提升用户体验，发现长尾目的地
  - Mock 数据库 vs 真实 API: 演示用 mock，生产环境接 Amadeus / Google Places
"""

from __future__ import annotations

from datetime import datetime

from loguru import logger

from models.schemas import (
    Destination,
    DestinationRecommendation,
    PlanningState,
    TravelPlanState,
)

from .base_agent import BaseAgent

MOCK_DESTINATIONS: list[dict] = [
    {
        "city": "东京",
        "country": "日本",
        "description": "传统与现代的完美融合，美食天堂",
        "best_season": "spring,autumn",
        "visa_required": True,
        "safety_score": 9.5,
        "cost_level": "high",
        "highlights": ["浅草寺", "涩谷十字路口", "筑地市场", "东京塔"],
    },
    {
        "city": "曼谷",
        "country": "泰国",
        "description": "热带风情，物美价廉的旅游胜地",
        "best_season": "winter",
        "visa_required": False,
        "safety_score": 7.5,
        "cost_level": "low",
        "highlights": ["大皇宫", "卧佛寺", "考山路", "暹罗广场"],
    },
    {
        "city": "巴黎",
        "country": "法国",
        "description": "浪漫之都，艺术与美食的殿堂",
        "best_season": "spring,summer",
        "visa_required": True,
        "safety_score": 8.0,
        "cost_level": "high",
        "highlights": ["埃菲尔铁塔", "卢浮宫", "香榭丽舍大街", "蒙马特高地"],
    },
    {
        "city": "清迈",
        "country": "泰国",
        "description": "宁静的兰纳古城，适合文化与休闲",
        "best_season": "winter",
        "visa_required": False,
        "safety_score": 8.5,
        "cost_level": "low",
        "highlights": ["双龙寺", "古城", "夜间动物园", "周末夜市"],
    },
    {
        "city": "首尔",
        "country": "韩国",
        "description": "潮流时尚与历史文化交汇",
        "best_season": "spring,autumn",
        "visa_required": False,
        "safety_score": 9.0,
        "cost_level": "medium",
        "highlights": ["景福宫", "明洞", "北村韩屋村", "南山塔"],
    },
    {
        "city": "大阪",
        "country": "日本",
        "description": "日本的厨房，环球影城所在地",
        "best_season": "spring,autumn",
        "visa_required": True,
        "safety_score": 9.5,
        "cost_level": "medium",
        "highlights": ["大阪城", "道顿堀", "环球影城", "黑门市场"],
    },
]


class DestinationAgent(BaseAgent):
    name = "DestinationAgent"

    async def execute(self, state: TravelPlanState) -> TravelPlanState:
        pref = state.preferences
        if pref is None:
            raise ValueError("缺少用户偏好")

        scored = []
        for d_data in MOCK_DESTINATIONS:
            dest = Destination(**d_data)
            score = self._score_destination(dest, pref.budget, pref.travel_style.value, pref.start_date)
            scored.append((score, dest))

        scored.sort(key=lambda x: x[0], reverse=True)
        top3 = [d for _, d in scored[:3]]
        selected = top3[0]

        state.destination_rec = DestinationRecommendation(
            destinations=top3,
            selected=selected,
            reasoning=f"根据您 ¥{pref.budget} 的预算和 {pref.travel_style.value} 风格，推荐 {selected.city}",
        )
        state.state = PlanningState.SEARCHING_PARALLEL
        logger.info(f"[{self.name}] 推荐目的地: {selected.city}, {selected.country}")
        return state

    @staticmethod
    def _score_destination(dest: Destination, budget: float, style: str, start_date: str) -> float:
        score = 0.0

        cost_budget_map = {"low": 8000, "medium": 15000, "high": 25000}
        est_cost = cost_budget_map.get(dest.cost_level, 15000)
        if budget >= est_cost:
            score += 30
        elif budget >= est_cost * 0.7:
            score += 15

        score += dest.safety_score * 3

        try:
            month = datetime.strptime(start_date, "%Y-%m-%d").month
        except (ValueError, TypeError):
            month = 6

        season_map = {12: "winter", 1: "winter", 2: "winter",
                      3: "spring", 4: "spring", 5: "spring",
                      6: "summer", 7: "summer", 8: "summer",
                      9: "autumn", 10: "autumn", 11: "autumn"}
        current_season = season_map.get(month, "summer")
        if current_season in dest.best_season:
            score += 20

        style_cost_pref = {"budget": "low", "comfort": "medium", "luxury": "high",
                           "adventure": "low", "cultural": "medium", "relaxation": "medium"}
        if style_cost_pref.get(style) == dest.cost_level:
            score += 15

        if not dest.visa_required:
            score += 10

        return score

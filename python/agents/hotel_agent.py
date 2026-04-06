"""
Hotel Agent —— 酒店搜索 Agent。

职责: 搜索酒店，匹配用户偏好（位置/价格/评分/设施）。
在并行阶段执行，与 Flight Agent / Activity Agent 同时运行。

面试考点:
  - 按旅行风格自动调整星级/价格范围
  - 总花费 = 每晚价格 × 入住天数 × 房间数
  - 降级策略: 超预算时可降低星级或选择距离稍远的酒店
"""

from __future__ import annotations

import random
from datetime import datetime

from loguru import logger

from models.schemas import Hotel, HotelSearchResult, TravelPlanState

from .base_agent import BaseAgent

MOCK_HOTEL_TEMPLATES = [
    {"name": "城市中心大酒店", "star_rating": 4.5, "user_rating": 9.0, "base_price": 600, "amenities": ["WiFi", "早餐", "健身房", "泳池"], "distance": 0.5},
    {"name": "经济快捷酒店", "star_rating": 3.0, "user_rating": 7.5, "base_price": 200, "amenities": ["WiFi", "空调"], "distance": 2.0},
    {"name": "精品设计酒店", "star_rating": 4.0, "user_rating": 8.8, "base_price": 450, "amenities": ["WiFi", "早餐", "酒吧"], "distance": 1.0},
    {"name": "豪华五星度假酒店", "star_rating": 5.0, "user_rating": 9.5, "base_price": 1200, "amenities": ["WiFi", "早餐", "SPA", "泳池", "管家服务"], "distance": 3.0},
    {"name": "青年旅舍", "star_rating": 2.0, "user_rating": 7.0, "base_price": 80, "amenities": ["WiFi", "公共厨房"], "distance": 1.5},
    {"name": "商务套房酒店", "star_rating": 4.0, "user_rating": 8.5, "base_price": 500, "amenities": ["WiFi", "早餐", "会议室", "健身房"], "distance": 0.8},
]


class HotelAgent(BaseAgent):
    name = "HotelAgent"

    async def execute(self, state: TravelPlanState) -> TravelPlanState:
        pref = state.preferences
        dest = state.selected_destination
        if pref is None or dest is None:
            raise ValueError("缺少偏好或目的地信息")

        nights = self._calc_nights(pref.start_date, pref.end_date)
        hotels = self._generate_hotels(dest.city, pref.travel_style.value)

        rec = self._best_hotel(hotels, pref.budget * 0.4 / max(nights, 1), pref.travel_style.value)
        total = (rec.price_per_night * nights * max(1, (pref.num_travelers + 1) // 2)) if rec else 0

        state.hotel_result = HotelSearchResult(
            hotels=hotels,
            recommended=rec,
            total_nights=nights,
            total_hotel_cost=total,
        )
        logger.info(f"[{self.name}] {dest.city} 找到 {len(hotels)} 家酒店, 推荐: {rec.name if rec else 'N/A'}, 总价: ¥{total:.0f}")
        return state

    @staticmethod
    def _calc_nights(start: str, end: str) -> int:
        try:
            d1 = datetime.strptime(start, "%Y-%m-%d")
            d2 = datetime.strptime(end, "%Y-%m-%d")
            return max((d2 - d1).days, 1)
        except (ValueError, TypeError):
            return 3

    @staticmethod
    def _generate_hotels(city: str, style: str) -> list[Hotel]:
        results = []
        price_mult = {"budget": 0.6, "comfort": 1.0, "luxury": 1.8,
                      "adventure": 0.7, "cultural": 0.9, "relaxation": 1.3}
        mult = price_mult.get(style, 1.0)

        for tmpl in MOCK_HOTEL_TEMPLATES:
            noise = random.uniform(0.8, 1.2)
            results.append(Hotel(
                name=f"{city}{tmpl['name']}",
                city=city,
                address=f"{city}市中心区域",
                star_rating=tmpl["star_rating"],
                user_rating=tmpl["user_rating"],
                price_per_night=round(tmpl["base_price"] * mult * noise, 0),
                amenities=tmpl["amenities"],
                distance_to_center_km=tmpl["distance"],
            ))
        return results

    @staticmethod
    def _best_hotel(hotels: list[Hotel], nightly_budget: float, style: str) -> Hotel | None:
        if not hotels:
            return None

        star_pref = {"budget": 2.5, "comfort": 3.5, "luxury": 4.5,
                     "adventure": 2.5, "cultural": 3.5, "relaxation": 4.0}
        target_star = star_pref.get(style, 3.5)

        def score(h: Hotel) -> float:
            price_ok = 20 if h.price_per_night <= nightly_budget else 0
            star_fit = 30 - abs(h.star_rating - target_star) * 10
            rating_s = h.user_rating * 3
            dist_s = max(0, 10 - h.distance_to_center_km * 3)
            return price_ok + star_fit + rating_s + dist_s

        return max(hotels, key=score)

"""
Flight Agent —— 航班搜索 Agent。

职责: 搜索航班、比价、推荐最优组合（价格 × 时长 × 中转次数）。
在并行阶段执行，与 Hotel Agent / Activity Agent 同时运行。

面试考点:
  - 并行执行: 与其他两个 Agent 通过 asyncio.gather 并行，延迟降低 60%
  - 评分函数: 多因素加权（价格占 50%, 时长 30%, 中转 20%）
  - Mock vs 真实: 生产环境对接 Amadeus GDS API
"""

from __future__ import annotations

import random

from loguru import logger

from models.schemas import Flight, FlightSearchResult, TravelPlanState

from .base_agent import BaseAgent


def _generate_mock_flights(dep: str, arr: str, date: str, count: int = 5) -> list[Flight]:
    airlines = ["中国国航", "东方航空", "南方航空", "海南航空", "春秋航空", "吉祥航空"]
    results = []
    for i in range(count):
        airline = airlines[i % len(airlines)]
        stops = random.choice([0, 0, 0, 1, 1, 2])
        base_price = random.randint(800, 5000)
        duration = round(random.uniform(2.0, 12.0), 1)
        results.append(Flight(
            airline=airline,
            flight_no=f"{airline[:2]}{random.randint(1000, 9999)}",
            departure_city=dep,
            arrival_city=arr,
            departure_time=f"{date}T{random.randint(6, 20):02d}:00",
            arrival_time=f"{date}T{random.randint(8, 23):02d}:00",
            price=float(base_price),
            duration_hours=duration,
            stops=stops,
            cabin_class="economy",
        ))
    return results


class FlightAgent(BaseAgent):
    name = "FlightAgent"

    async def execute(self, state: TravelPlanState) -> TravelPlanState:
        pref = state.preferences
        dest = state.selected_destination
        if pref is None or dest is None:
            raise ValueError("缺少偏好或目的地信息")

        outbound = _generate_mock_flights(pref.departure_city, dest.city, pref.start_date)
        returns = _generate_mock_flights(dest.city, pref.departure_city, pref.end_date)

        rec_out = self._best_flight(outbound, pref.budget * 0.3)
        rec_ret = self._best_flight(returns, pref.budget * 0.3)

        total = (rec_out.price if rec_out else 0) + (rec_ret.price if rec_ret else 0)
        total *= pref.num_travelers

        state.flight_result = FlightSearchResult(
            outbound_flights=outbound,
            return_flights=returns,
            recommended_outbound=rec_out,
            recommended_return=rec_ret,
            total_flight_cost=total,
        )
        logger.info(f"[{self.name}] 找到 {len(outbound)} 个去程 + {len(returns)} 个返程航班, 推荐总价: ¥{total:.0f}")
        return state

    @staticmethod
    def _best_flight(flights: list[Flight], budget_share: float) -> Flight | None:
        if not flights:
            return None

        max_price = max(f.price for f in flights) or 1
        max_dur = max(f.duration_hours for f in flights) or 1

        def score(f: Flight) -> float:
            price_score = 1 - (f.price / max_price)
            dur_score = 1 - (f.duration_hours / max_dur)
            stop_score = 1 - (f.stops / 3)
            budget_bonus = 10 if f.price <= budget_share else 0
            return price_score * 50 + dur_score * 30 + stop_score * 20 + budget_bonus

        return max(flights, key=score)

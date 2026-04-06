"""
航班搜索工具 —— 模拟 Amadeus GDS API。

在生产环境中，这里会对接 Amadeus API / 携程API 等真实数据源。
Mock 模式下返回随机但合理的航班数据，保证系统可以零成本运行演示。
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from models.schemas import Flight


AIRLINES = {
    "国内": [
        ("中国国航", "CA"), ("东方航空", "MU"), ("南方航空", "CZ"),
        ("海南航空", "HU"), ("春秋航空", "9C"), ("吉祥航空", "HO"),
        ("深圳航空", "ZH"), ("厦门航空", "MF"),
    ],
    "国际": [
        ("全日空", "NH"), ("日本航空", "JL"), ("大韩航空", "KE"),
        ("新加坡航空", "SQ"), ("泰国航空", "TG"), ("国泰航空", "CX"),
        ("阿联酋航空", "EK"), ("法国航空", "AF"),
    ],
}

ROUTE_DURATIONS = {
    ("北京", "东京"): (3.5, 4.5), ("上海", "东京"): (2.5, 3.5),
    ("北京", "首尔"): (2.0, 3.0), ("上海", "首尔"): (1.5, 2.5),
    ("北京", "曼谷"): (4.5, 6.0), ("上海", "曼谷"): (4.0, 5.5),
    ("北京", "巴黎"): (10.0, 13.0), ("上海", "巴黎"): (11.0, 14.0),
    ("北京", "大阪"): (3.0, 4.0), ("上海", "大阪"): (2.0, 3.0),
    ("北京", "清迈"): (5.0, 7.0), ("上海", "清迈"): (4.5, 6.5),
}


def search_flights(
    departure_city: str,
    arrival_city: str,
    date: str,
    cabin_class: str = "economy",
    count: int = 6,
) -> list[Flight]:
    """搜索航班（Mock 实现）。"""
    key = (departure_city, arrival_city)
    rev_key = (arrival_city, departure_city)
    dur_range = ROUTE_DURATIONS.get(key) or ROUTE_DURATIONS.get(rev_key) or (3.0, 8.0)

    is_international = arrival_city in ("东京", "首尔", "曼谷", "巴黎", "大阪", "清迈")
    airline_pool = AIRLINES["国际"] if is_international else AIRLINES["国内"]

    cabin_multiplier = {"economy": 1.0, "business": 2.5, "first": 5.0}
    multiplier = cabin_multiplier.get(cabin_class, 1.0)

    results: list[Flight] = []
    for i in range(count):
        airline_name, airline_code = airline_pool[i % len(airline_pool)]
        duration = round(random.uniform(*dur_range), 1)
        stops = random.choices([0, 1, 2], weights=[60, 30, 10])[0]
        base_price = 500 + duration * random.randint(200, 500) + stops * (-300)
        price = max(300, round(base_price * multiplier))

        dep_hour = random.randint(6, 20)
        arr_offset = timedelta(hours=duration)
        dep_time = f"{date}T{dep_hour:02d}:{random.choice(['00', '30'])}:00"

        results.append(Flight(
            airline=airline_name,
            flight_no=f"{airline_code}{random.randint(100, 9999)}",
            departure_city=departure_city,
            arrival_city=arrival_city,
            departure_time=dep_time,
            arrival_time=f"(+{duration}h)",
            price=float(price),
            duration_hours=duration,
            stops=stops,
            cabin_class=cabin_class,
        ))

    return sorted(results, key=lambda f: f.price)

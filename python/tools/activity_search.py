"""
活动搜索工具 —— 模拟 Google Maps Places API / 大众点评 API。

在生产环境中，这里会对接 Google Places API / TripAdvisor API 等。
Mock 模式下返回各城市的景点、餐厅、体验活动数据。
"""

from __future__ import annotations

import random

from models.schemas import Activity


CITY_ACTIVITIES: dict[str, list[dict]] = {
    "东京": [
        {"name": "浅草寺", "cat": "sightseeing", "price": 0, "hours": 2.0, "slot": "morning"},
        {"name": "筑地市场海鲜早餐", "cat": "food", "price": 200, "hours": 1.5, "slot": "morning"},
        {"name": "明治神宫", "cat": "sightseeing", "price": 0, "hours": 1.5, "slot": "morning"},
        {"name": "涩谷十字路口", "cat": "sightseeing", "price": 0, "hours": 0.5, "slot": "afternoon"},
        {"name": "teamLab数字艺术馆", "cat": "experience", "price": 250, "hours": 2.5, "slot": "afternoon"},
        {"name": "东京塔", "cat": "sightseeing", "price": 80, "hours": 1.5, "slot": "afternoon"},
        {"name": "新宿歌舞伎町", "cat": "experience", "price": 0, "hours": 2.0, "slot": "evening"},
        {"name": "居酒屋体验", "cat": "food", "price": 300, "hours": 2.0, "slot": "evening"},
        {"name": "秋叶原动漫街", "cat": "experience", "price": 0, "hours": 2.0, "slot": "afternoon"},
        {"name": "和服体验", "cat": "experience", "price": 400, "hours": 3.0, "slot": "morning"},
    ],
    "曼谷": [
        {"name": "大皇宫", "cat": "sightseeing", "price": 35, "hours": 2.5, "slot": "morning"},
        {"name": "卧佛寺", "cat": "sightseeing", "price": 15, "hours": 1.5, "slot": "morning"},
        {"name": "水上市场", "cat": "experience", "price": 80, "hours": 3.0, "slot": "morning"},
        {"name": "暹罗广场购物", "cat": "experience", "price": 0, "hours": 2.0, "slot": "afternoon"},
        {"name": "泰式按摩", "cat": "experience", "price": 120, "hours": 2.0, "slot": "afternoon"},
        {"name": "考山路小吃", "cat": "food", "price": 60, "hours": 2.0, "slot": "evening"},
        {"name": "湄南河夜游", "cat": "experience", "price": 200, "hours": 2.0, "slot": "evening"},
        {"name": "路边摊美食之旅", "cat": "food", "price": 100, "hours": 2.0, "slot": "evening"},
    ],
    "default": [
        {"name": "城市地标", "cat": "sightseeing", "price": 0, "hours": 2.0, "slot": "morning"},
        {"name": "当地博物馆", "cat": "sightseeing", "price": 80, "hours": 2.5, "slot": "morning"},
        {"name": "特色午餐", "cat": "food", "price": 150, "hours": 1.5, "slot": "afternoon"},
        {"name": "老城区漫步", "cat": "sightseeing", "price": 0, "hours": 2.0, "slot": "afternoon"},
        {"name": "日落观景点", "cat": "sightseeing", "price": 50, "hours": 1.0, "slot": "evening"},
        {"name": "当地夜市", "cat": "food", "price": 100, "hours": 2.0, "slot": "evening"},
    ],
}


def search_activities(city: str, interests: list[str] | None = None) -> list[Activity]:
    """搜索目的地活动（Mock 实现）。"""
    templates = CITY_ACTIVITIES.get(city, CITY_ACTIVITIES["default"])
    interests = interests or []

    results: list[Activity] = []
    for tmpl in templates:
        bonus = sum(1 for tag in interests if tag.lower() in tmpl["name"].lower())
        rating = round(random.uniform(7.5, 9.5) + bonus * 0.3, 1)
        results.append(Activity(
            name=tmpl["name"],
            category=tmpl["cat"],
            location=city,
            duration_hours=tmpl["hours"],
            price=float(tmpl["price"]),
            rating=min(rating, 10.0),
            description=f"{city} - {tmpl['name']}",
            time_slot=tmpl["slot"],
        ))

    return results

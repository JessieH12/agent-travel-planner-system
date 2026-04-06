"""
酒店搜索工具 —— 模拟 Booking.com / 携程酒店 API。

在生产环境中，这里会对接真实酒店预订 API。
Mock 模式下根据城市和旅行风格生成合理的酒店数据。
"""

from __future__ import annotations

import random

from models.schemas import Hotel


CITY_HOTEL_DATA: dict[str, list[dict]] = {
    "东京": [
        {"name": "东京帝国酒店", "star": 5.0, "base_price": 1500, "amenities": ["WiFi", "温泉", "米其林餐厅", "管家服务"]},
        {"name": "新宿华盛顿酒店", "star": 4.0, "base_price": 650, "amenities": ["WiFi", "早餐", "健身房"]},
        {"name": "东京胶囊旅馆", "star": 2.0, "base_price": 120, "amenities": ["WiFi", "公共浴室"]},
        {"name": "涩谷精品酒店", "star": 4.5, "base_price": 900, "amenities": ["WiFi", "酒吧", "屋顶花园"]},
        {"name": "浅草背包客旅馆", "star": 2.5, "base_price": 180, "amenities": ["WiFi", "公共厨房", "洗衣房"]},
    ],
    "曼谷": [
        {"name": "曼谷文华东方酒店", "star": 5.0, "base_price": 800, "amenities": ["WiFi", "SPA", "泳池", "河景"]},
        {"name": "考山路精品旅舍", "star": 3.0, "base_price": 100, "amenities": ["WiFi", "酒吧", "公共区域"]},
        {"name": "素坤逸万豪酒店", "star": 4.5, "base_price": 500, "amenities": ["WiFi", "泳池", "健身房", "早餐"]},
        {"name": "暹罗经济酒店", "star": 3.0, "base_price": 150, "amenities": ["WiFi", "空调"]},
    ],
    "default": [
        {"name": "豪华五星酒店", "star": 5.0, "base_price": 1000, "amenities": ["WiFi", "SPA", "泳池", "管家"]},
        {"name": "舒适四星酒店", "star": 4.0, "base_price": 500, "amenities": ["WiFi", "早餐", "健身房"]},
        {"name": "经济连锁酒店", "star": 3.0, "base_price": 200, "amenities": ["WiFi", "空调"]},
        {"name": "青年旅舍", "star": 2.0, "base_price": 80, "amenities": ["WiFi", "公共厨房"]},
    ],
}


def search_hotels(city: str, check_in: str, check_out: str, style: str = "comfort") -> list[Hotel]:
    """搜索酒店（Mock 实现）。"""
    templates = CITY_HOTEL_DATA.get(city, CITY_HOTEL_DATA["default"])
    style_mult = {"budget": 0.7, "comfort": 1.0, "luxury": 1.5,
                  "adventure": 0.6, "cultural": 0.9, "relaxation": 1.2}
    mult = style_mult.get(style, 1.0)

    results: list[Hotel] = []
    for tmpl in templates:
        noise = random.uniform(0.85, 1.15)
        results.append(Hotel(
            name=tmpl["name"],
            city=city,
            address=f"{city}市中心",
            star_rating=tmpl["star"],
            user_rating=round(random.uniform(7.0, 9.8), 1),
            price_per_night=round(tmpl["base_price"] * mult * noise),
            amenities=tmpl["amenities"],
            distance_to_center_km=round(random.uniform(0.3, 5.0), 1),
        ))

    return sorted(results, key=lambda h: h.price_per_night)

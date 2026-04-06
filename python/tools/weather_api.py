"""
天气查询工具 —— 模拟天气 API。

在生产环境中，这里会对接 OpenWeatherMap API 或和风天气 API。
Mock 模式下根据城市和月份返回典型天气数据。
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class WeatherInfo:
    city: str
    date: str
    temperature_high: int
    temperature_low: int
    condition: str
    humidity: int
    rain_probability: int
    suggestion: str


CITY_WEATHER_PROFILES: dict[str, dict[str, dict]] = {
    "东京": {
        "spring": {"high": (15, 22), "low": (8, 14), "conditions": ["晴", "多云", "小雨"], "humidity": (50, 70), "rain": 30},
        "summer": {"high": (28, 35), "low": (22, 26), "conditions": ["晴", "多云", "雷阵雨"], "humidity": (70, 90), "rain": 50},
        "autumn": {"high": (18, 25), "low": (10, 18), "conditions": ["晴", "多云"], "humidity": (40, 60), "rain": 20},
        "winter": {"high": (5, 12), "low": (-2, 5), "conditions": ["晴", "多云", "阴"], "humidity": (30, 50), "rain": 10},
    },
    "曼谷": {
        "spring": {"high": (33, 38), "low": (25, 28), "conditions": ["晴", "多云", "雷阵雨"], "humidity": (60, 80), "rain": 40},
        "summer": {"high": (32, 36), "low": (25, 28), "conditions": ["雷阵雨", "多云", "大雨"], "humidity": (70, 90), "rain": 70},
        "autumn": {"high": (30, 34), "low": (24, 27), "conditions": ["多云", "雷阵雨"], "humidity": (65, 85), "rain": 60},
        "winter": {"high": (30, 34), "low": (20, 24), "conditions": ["晴", "多云"], "humidity": (50, 65), "rain": 10},
    },
}

DEFAULT_PROFILE = {
    "spring": {"high": (15, 25), "low": (8, 15), "conditions": ["晴", "多云"], "humidity": (40, 60), "rain": 25},
    "summer": {"high": (25, 35), "low": (18, 25), "conditions": ["晴", "多云", "雷阵雨"], "humidity": (60, 80), "rain": 40},
    "autumn": {"high": (15, 25), "low": (8, 18), "conditions": ["晴", "多云"], "humidity": (40, 60), "rain": 20},
    "winter": {"high": (0, 12), "low": (-5, 5), "conditions": ["晴", "多云", "阴", "小雪"], "humidity": (30, 50), "rain": 15},
}


def _month_to_season(month: int) -> str:
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


def get_weather(city: str, date: str) -> WeatherInfo:
    """获取天气信息（Mock 实现）。"""
    try:
        month = int(date.split("-")[1])
    except (IndexError, ValueError):
        month = 6

    season = _month_to_season(month)
    profile = CITY_WEATHER_PROFILES.get(city, DEFAULT_PROFILE).get(season, DEFAULT_PROFILE["summer"])

    high = random.randint(*profile["high"])
    low = random.randint(*profile["low"])
    condition = random.choice(profile["conditions"])
    humidity = random.randint(*profile["humidity"])
    rain = profile["rain"]

    if rain > 50:
        suggestion = "建议携带雨具，穿防水鞋"
    elif high > 30:
        suggestion = "天气炎热，注意防晒补水"
    elif low < 5:
        suggestion = "天气寒冷，注意保暖"
    else:
        suggestion = "天气宜人，适合户外活动"

    return WeatherInfo(
        city=city,
        date=date,
        temperature_high=high,
        temperature_low=low,
        condition=condition,
        humidity=humidity,
        rain_probability=rain,
        suggestion=suggestion,
    )

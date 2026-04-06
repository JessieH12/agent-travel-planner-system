"""
CLI 入口 —— 从命令行运行完整的行程规划 Pipeline。

使用方式:
  python main.py
  python main.py --budget 15000 --departure 上海 --start 2026-06-01 --end 2026-06-07
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description="多Agent智能旅游行程规划系统")
    parser.add_argument("--budget", type=float, default=10000, help="总预算（人民币元）")
    parser.add_argument("--departure", type=str, default="北京", help="出发城市")
    parser.add_argument("--start", type=str, default="2026-05-01", help="出发日期 YYYY-MM-DD")
    parser.add_argument("--end", type=str, default="2026-05-05", help="返回日期 YYYY-MM-DD")
    parser.add_argument("--style", type=str, default="comfort", help="旅行风格: budget/comfort/luxury/adventure/cultural/relaxation")
    parser.add_argument("--travelers", type=int, default=1, help="出行人数")
    args = parser.parse_args()

    from orchestrator.pipeline import quick_plan

    state = asyncio.run(quick_plan(
        budget=args.budget,
        departure=args.departure,
        start=args.start,
        end=args.end,
        style=args.style,
        travelers=args.travelers,
    ))

    print("\n" + "=" * 60)
    print("📋 行程规划结果")
    print("=" * 60)

    if state.selected_destination:
        d = state.selected_destination
        print(f"\n🌍 目的地: {d.city}, {d.country}")
        print(f"   {d.description}")
        print(f"   亮点: {', '.join(d.highlights)}")

    if state.flight_result:
        fr = state.flight_result
        if fr.recommended_outbound:
            o = fr.recommended_outbound
            print(f"\n✈️  去程: {o.airline} {o.flight_no} ¥{o.price:.0f}")
        if fr.recommended_return:
            r = fr.recommended_return
            print(f"✈️  返程: {r.airline} {r.flight_no} ¥{r.price:.0f}")

    if state.hotel_result and state.hotel_result.recommended:
        h = state.hotel_result.recommended
        print(f"\n🏨 酒店: {h.name} ({h.star_rating}星)")
        print(f"   ¥{h.price_per_night:.0f}/晚 × {state.hotel_result.total_nights} 晚")
        print(f"   设施: {', '.join(h.amenities)}")

    if state.activity_result:
        print(f"\n📅 每日行程:")
        for day in state.activity_result.day_plans:
            print(f"\n  {day.date} (日花费: ¥{day.day_cost:.0f})")
            for act in day.activities:
                price_str = f"¥{act.price:.0f}" if act.price > 0 else "免费"
                print(f"    [{act.time_slot:9s}] {act.name} ({act.duration_hours}h) {price_str}")

    if state.budget_breakdown:
        bb = state.budget_breakdown
        print(f"\n💰 预算明细:")
        print(f"   航班: ¥{bb.flight_cost:.0f}")
        print(f"   酒店: ¥{bb.hotel_cost:.0f}")
        print(f"   活动: ¥{bb.activity_cost:.0f}")
        print(f"   ─────────────")
        print(f"   总计: ¥{bb.total_cost:.0f} / 预算: ¥{bb.budget:.0f}")
        print(f"   {'✅ 预算内' if bb.is_within_budget else f'⚠️ 超预算 ¥{bb.over_budget_amount:.0f}'}")

    if state.adjustment_round > 0:
        print(f"\n🔄 经过 {state.adjustment_round} 轮预算调整")

    if state.error_messages:
        print(f"\n⚠️  警告:")
        for msg in state.error_messages:
            print(f"   - {msg}")

    print()


if __name__ == "__main__":
    main()

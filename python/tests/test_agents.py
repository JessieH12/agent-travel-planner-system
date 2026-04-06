"""
单元测试 —— 覆盖所有 Agent + Pipeline + 预算循环。

运行: cd python && python -m pytest tests/ -v
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents import (
    ActivityAgent,
    BudgetAgent,
    DestinationAgent,
    FlightAgent,
    HotelAgent,
    PreferenceAgent,
)
from models.schemas import (
    PlanningState,
    TravelPlanState,
    TravelStyle,
    UserPreferences,
)
from orchestrator.pipeline import TravelPlanningPipeline, quick_plan


def _make_prefs(**overrides) -> UserPreferences:
    defaults = dict(
        budget=10000,
        travel_style=TravelStyle.COMFORT,
        departure_city="北京",
        start_date="2026-05-01",
        end_date="2026-05-05",
        num_travelers=1,
    )
    defaults.update(overrides)
    return UserPreferences(**defaults)


def _make_state(**overrides) -> TravelPlanState:
    return TravelPlanState(preferences=_make_prefs(**overrides))


# ━━━━━━ Preference Agent ━━━━━━


@pytest.mark.asyncio
async def test_preference_agent_fills_interests():
    state = _make_state()
    agent = PreferenceAgent()
    result = await agent.run(state)
    assert result.preferences is not None
    assert len(result.preferences.interests) > 0
    assert result.state == PlanningState.RECOMMENDING_DESTINATIONS


@pytest.mark.asyncio
async def test_preference_agent_keeps_existing_interests():
    state = _make_state()
    state.preferences.interests = ["自定义兴趣"]
    agent = PreferenceAgent()
    result = await agent.run(state)
    assert result.preferences.interests == ["自定义兴趣"]


# ━━━━━━ Destination Agent ━━━━━━


@pytest.mark.asyncio
async def test_destination_agent_recommends():
    state = _make_state()
    state.state = PlanningState.RECOMMENDING_DESTINATIONS
    agent = DestinationAgent()
    result = await agent.run(state)
    assert result.destination_rec is not None
    assert result.destination_rec.selected is not None
    assert len(result.destination_rec.destinations) >= 1
    assert result.state == PlanningState.SEARCHING_PARALLEL


# ━━━━━━ Flight Agent ━━━━━━


@pytest.mark.asyncio
async def test_flight_agent_searches():
    state = _make_state()
    agent_d = DestinationAgent()
    state = await agent_d.run(state)

    agent = FlightAgent()
    result = await agent.run(state)
    assert result.flight_result is not None
    assert len(result.flight_result.outbound_flights) > 0
    assert result.flight_result.recommended_outbound is not None
    assert result.flight_result.total_flight_cost > 0


# ━━━━━━ Hotel Agent ━━━━━━


@pytest.mark.asyncio
async def test_hotel_agent_searches():
    state = _make_state()
    agent_d = DestinationAgent()
    state = await agent_d.run(state)

    agent = HotelAgent()
    result = await agent.run(state)
    assert result.hotel_result is not None
    assert len(result.hotel_result.hotels) > 0
    assert result.hotel_result.recommended is not None


# ━━━━━━ Activity Agent ━━━━━━


@pytest.mark.asyncio
async def test_activity_agent_generates_plans():
    state = _make_state()
    agent_d = DestinationAgent()
    state = await agent_d.run(state)

    agent = ActivityAgent()
    result = await agent.run(state)
    assert result.activity_result is not None
    assert len(result.activity_result.day_plans) > 0


# ━━━━━━ Budget Agent ━━━━━━


@pytest.mark.asyncio
async def test_budget_agent_passes():
    state = await quick_plan(budget=50000)
    assert state.budget_breakdown is not None
    assert state.budget_breakdown.is_within_budget is True


@pytest.mark.asyncio
async def test_budget_agent_triggers_adjustment():
    state = await quick_plan(budget=2000, travelers=2)
    assert state.adjustment_round > 0


# ━━━━━━ Full Pipeline ━━━━━━


@pytest.mark.asyncio
async def test_full_pipeline():
    state = await quick_plan(budget=15000, departure="上海", start="2026-06-01", end="2026-06-05")
    assert state.state == PlanningState.COMPLETED
    assert state.selected_destination is not None
    assert state.flight_result is not None
    assert state.hotel_result is not None
    assert state.activity_result is not None
    assert state.budget_breakdown is not None


@pytest.mark.asyncio
async def test_pipeline_multiple_styles():
    for style in ["budget", "comfort", "luxury", "adventure"]:
        state = await quick_plan(budget=20000, style=style)
        assert state.state == PlanningState.COMPLETED

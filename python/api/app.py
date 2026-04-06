"""
FastAPI 后端 —— 提供 REST API 接口。

端点:
  POST /api/plan    - 提交行程规划请求
  GET  /api/health  - 健康检查
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.settings import settings
from models.schemas import TravelPlanState, TravelStyle, UserPreferences
from orchestrator.pipeline import TravelPlanningPipeline

app = FastAPI(
    title="多Agent智能旅游行程规划系统",
    description="6-Agent Pipeline + 并行搜索 + 预算循环",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    budget: float = Field(10000, gt=0, description="总预算（人民币）")
    departure_city: str = Field("北京", description="出发城市")
    start_date: str = Field("2026-05-01", description="出发日期")
    end_date: str = Field("2026-05-05", description="返回日期")
    travel_style: str = Field("comfort", description="旅行风格")
    num_travelers: int = Field(1, ge=1, description="出行人数")
    interests: list[str] = Field(default_factory=list)
    notes: str = ""


class PlanSummary(BaseModel):
    destination: str = ""
    country: str = ""
    flight_cost: float = 0
    hotel_cost: float = 0
    activity_cost: float = 0
    total_cost: float = 0
    budget: float = 0
    within_budget: bool = True
    adjustment_rounds: int = 0
    hotel_name: str = ""
    days: int = 0
    highlights: list[str] = []
    warnings: list[str] = []


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "travel-planner", "agents": 6}


@app.post("/api/plan", response_model=PlanSummary)
async def create_plan(req: PlanRequest):
    try:
        prefs = UserPreferences(
            budget=req.budget,
            travel_style=TravelStyle(req.travel_style),
            departure_city=req.departure_city,
            start_date=req.start_date,
            end_date=req.end_date,
            num_travelers=req.num_travelers,
            interests=req.interests,
            notes=req.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    pipeline = TravelPlanningPipeline()
    state: TravelPlanState = await pipeline.run(prefs)

    dest = state.selected_destination
    bb = state.budget_breakdown

    return PlanSummary(
        destination=dest.city if dest else "",
        country=dest.country if dest else "",
        flight_cost=bb.flight_cost if bb else 0,
        hotel_cost=bb.hotel_cost if bb else 0,
        activity_cost=bb.activity_cost if bb else 0,
        total_cost=bb.total_cost if bb else 0,
        budget=bb.budget if bb else req.budget,
        within_budget=bb.is_within_budget if bb else False,
        adjustment_rounds=state.adjustment_round,
        hotel_name=state.hotel_result.recommended.name if state.hotel_result and state.hotel_result.recommended else "",
        days=len(state.activity_result.day_plans) if state.activity_result else 0,
        highlights=dest.highlights if dest else [],
        warnings=state.error_messages,
    )


@app.post("/api/plan/full")
async def create_plan_full(req: PlanRequest):
    """返回完整的 TravelPlanState（用于调试和前端渲染）。"""
    try:
        prefs = UserPreferences(
            budget=req.budget,
            travel_style=TravelStyle(req.travel_style),
            departure_city=req.departure_city,
            start_date=req.start_date,
            end_date=req.end_date,
            num_travelers=req.num_travelers,
            interests=req.interests,
            notes=req.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    pipeline = TravelPlanningPipeline()
    state = await pipeline.run(prefs)
    return state.model_dump()


def start():
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)


if __name__ == "__main__":
    start()

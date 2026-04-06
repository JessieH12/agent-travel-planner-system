"""
Streamlit 前端 —— 交互式行程规划界面。

运行方式:
  cd python
  streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from models.schemas import TravelPlanState, TravelStyle, UserPreferences
from orchestrator.pipeline import TravelPlanningPipeline

st.set_page_config(page_title="智能旅游行程规划", page_icon="✈️", layout="wide")

st.title("✈️ 多Agent智能旅游行程规划系统")
st.markdown("**6个AI Agent协作** | Pipeline + 并行搜索 + 预算循环")

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📝 旅行偏好")
    budget = st.number_input("总预算（¥）", min_value=1000, max_value=500000, value=10000, step=1000)
    departure = st.text_input("出发城市", value="北京")
    start_date = st.date_input("出发日期")
    end_date = st.date_input("返回日期")
    style = st.selectbox("旅行风格", ["comfort", "budget", "luxury", "adventure", "cultural", "relaxation"],
                         format_func=lambda x: {"comfort": "舒适", "budget": "经济", "luxury": "豪华",
                                                "adventure": "探险", "cultural": "文化", "relaxation": "休闲"}[x])
    travelers = st.number_input("出行人数", min_value=1, max_value=10, value=1)
    interests = st.multiselect("兴趣标签", ["美食", "历史", "艺术", "自然", "购物", "摄影", "运动"])
    notes = st.text_area("额外备注", placeholder="例: 不吃辣、需要无障碍设施...")

    plan_btn = st.button("🚀 开始规划", type="primary", use_container_width=True)

with col2:
    if plan_btn:
        with st.spinner("6个Agent正在协作规划您的行程..."):
            prefs = UserPreferences(
                budget=float(budget),
                travel_style=TravelStyle(style),
                departure_city=departure,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                num_travelers=travelers,
                interests=interests,
                notes=notes,
            )
            pipeline = TravelPlanningPipeline()
            state: TravelPlanState = asyncio.run(pipeline.run(prefs))

        st.success("行程规划完成!")

        if state.selected_destination:
            d = state.selected_destination
            st.subheader(f"🌍 目的地: {d.city}, {d.country}")
            st.write(d.description)
            st.write(f"**亮点:** {', '.join(d.highlights)}")

        tab1, tab2, tab3, tab4 = st.tabs(["✈️ 航班", "🏨 酒店", "📅 行程", "💰 预算"])

        with tab1:
            if state.flight_result:
                fr = state.flight_result
                if fr.recommended_outbound:
                    o = fr.recommended_outbound
                    st.metric("去程推荐", f"{o.airline} {o.flight_no}", f"¥{o.price:.0f}")
                if fr.recommended_return:
                    r = fr.recommended_return
                    st.metric("返程推荐", f"{r.airline} {r.flight_no}", f"¥{r.price:.0f}")
                st.write(f"**航班总费用:** ¥{fr.total_flight_cost:.0f}")

        with tab2:
            if state.hotel_result and state.hotel_result.recommended:
                h = state.hotel_result.recommended
                st.metric("推荐酒店", h.name, f"⭐{h.star_rating}")
                st.write(f"¥{h.price_per_night:.0f}/晚 × {state.hotel_result.total_nights} 晚")
                st.write(f"**设施:** {', '.join(h.amenities)}")
                st.write(f"**酒店总费用:** ¥{state.hotel_result.total_hotel_cost:.0f}")

        with tab3:
            if state.activity_result:
                for day in state.activity_result.day_plans:
                    st.markdown(f"### {day.date} (¥{day.day_cost:.0f})")
                    for act in day.activities:
                        price_str = f"¥{act.price:.0f}" if act.price > 0 else "免费"
                        st.write(f"- **[{act.time_slot}]** {act.name} ({act.duration_hours}h) {price_str}")

        with tab4:
            if state.budget_breakdown:
                bb = state.budget_breakdown
                c1, c2, c3 = st.columns(3)
                c1.metric("航班", f"¥{bb.flight_cost:.0f}")
                c2.metric("酒店", f"¥{bb.hotel_cost:.0f}")
                c3.metric("活动", f"¥{bb.activity_cost:.0f}")

                st.divider()
                st.metric("总计 / 预算", f"¥{bb.total_cost:.0f} / ¥{bb.budget:.0f}",
                          delta=f"{'节省' if bb.remaining >= 0 else '超出'} ¥{abs(bb.remaining):.0f}",
                          delta_color="normal" if bb.remaining >= 0 else "inverse")

                if state.adjustment_round > 0:
                    st.info(f"经过 {state.adjustment_round} 轮预算调整")

        if state.error_messages:
            for msg in state.error_messages:
                st.warning(msg)
    else:
        st.info("👈 请在左侧填写旅行偏好，然后点击"开始规划"")

        st.subheader("🏗️ 系统架构")
        st.markdown("""
        ```
        用户输入 → Preference Agent → Destination Agent
        → [Flight + Hotel + Activity (并行)]
        → Budget Agent (预算校验)
        ↓ (超预算则循环调整)
        输出最终行程
        ```
        """)

        st.subheader("🤖 6个Agent")
        agents_info = {
            "Preference Agent": "收集用户偏好（预算/风格/时间）",
            "Destination Agent": "推荐目的地（季节/签证/安全/性价比）",
            "Flight Agent": "搜索航班、比价、推荐最优组合",
            "Hotel Agent": "搜索酒店，匹配偏好",
            "Activity Agent": "推荐景点/餐厅，生成每日行程",
            "Budget Agent": "预算追踪，超预算自动调整",
        }
        for name, desc in agents_info.items():
            st.write(f"- **{name}**: {desc}")

"""
Streamlit 前端 —— 调用 Java RESTful API 版本

运行
streamlit run ui/streamlit_app.py
"""

import sys
from pathlib import Path
import requests  # 新增：用于发送 HTTP 请求
import streamlit as st

st.set_page_config(page_title="智能旅游行程规划", page_icon="✈️", layout="wide")

st.title("✈️ 多Agent智能旅游行程规划系统")
st.markdown("**前后端分离架构** | Streamlit UI + Spring Boot API")

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📝 旅行偏好")
    budget = st.number_input("总预算（¥）", min_value=1000, max_value=500000, value=15000, step=1000)
    departure = st.text_input("出发城市", value="上海")
    start_date = st.date_input("出发日期")
    end_date = st.date_input("返回日期")

    # 注意：这里的选项被修改为了 Java API 支持的 Enum 值
    style = st.selectbox("旅行风格",
                         ["RELAXED", "BUDGET_FRIENDLY", "LUXURY", "ADVENTURE", "CULTURE"],
                         format_func=lambda x: {"RELAXED": "休闲", "BUDGET_FRIENDLY": "经济", "LUXURY": "豪华",
                                                "ADVENTURE": "探险", "CULTURE": "文化"}[x])
    travelers = st.number_input("出行人数", min_value=1, max_value=10, value=2)
    interests = st.multiselect("兴趣标签", ["美食", "历史", "艺术", "自然", "购物", "博物馆"], default=["美食", "博物馆"])

    plan_btn = st.button("🚀 开始规划", type="primary", use_container_width=True)

with col2:
    if plan_btn:
        with st.spinner("Java 后端的 6 个 Agent 正在协作规划您的行程..."):
            payload = {
                "budget": float(budget),
                "style": style,
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "departureCity": departure,
                "travelers": travelers,
                "interests": interests
            }

            try:
                response = requests.post("http://localhost:8080/api/plan", json=payload)

                # # 1. 优雅处理 400 业务校验错误（拦截填错的日期等）
                # if response.status_code == 400:
                #     err_data = response.json()
                #     st.warning(f"⚠️ 规划失败：{err_data.get('errorMessage', '请求参数有误，请检查左侧表单')}")
                # 1. 优雅处理 400 业务校验错误
                if response.status_code == 400:
                    err_data = response.json()
                    errors_dict = err_data.get('errors', {})

                    st.warning("⚠️ 规划失败，请检查左侧表单的填写项：")
                    # 遍历显示所有具体的报错详情
                    if errors_dict:
                        for field, msg in errors_dict.items():
                            st.error(f"❌ {msg}")
                    else:
                        # 兜底：如果是业务抛出的普通错误（如行程不足1天），直接显示 errorMessage
                        st.error(f"❌ {err_data.get('errorMessage', '请求参数有误')}")

                # 2. 如果是 200 成功，则渲染页面
                elif response.status_code == 200:
                    result = response.json()
                    st.success("🎉 行程规划完成!")

                    # --- 1. 提取目的地 (对应 Java 字段: destination -> city) ---
                    dest_obj = result.get('selectedDestination', {})
                    dest = dest_obj.get('city', '未知')
                    country = dest_obj.get('country', '')
                    highlights = dest_obj.get('highlights', [])

                    # --- 2. 提取预算明细 (对应 Java 字段: budgetBreakdown -> flightCost 等) ---
                    bb = result.get('budgetBreakdown', {})
                    # 注意：Java 使用驼峰命名，需严格匹配
                    flight_cost = bb.get('flightCost', 0)
                    hotel_cost = bb.get('hotelCost', 0)
                    activity_cost = bb.get('activityCost', 0)
                    total_cost = bb.get('total', 0)
                    is_within = bb.get('withinBudget', False)
                    remaining = budget - total_cost

                    rounds = result.get('adjustmentRound', 0)

                    # --- 3. 提取住宿信息 (对应 Java 字段: hotelResult -> recommended -> name) ---
                    hr = result.get('hotelSearchResult', {})
                    hotel_info = hr.get('recommended', {})
                    hotel_name = hotel_info.get('name', '未指定')
                    hotel_pre_price_night = hotel_info.get('pricePerNight', 0)
                    total_nights = hotel_cost / hotel_pre_price_night
                    # total_nights = hr.get('totalNights', 0) # Java 字段是 totalNights

                    # --- 渲染 UI ---
                    st.subheader(f"🌍 目的地: {dest} ({country})")
                    if highlights:
                        st.write(f"**亮点:** {', '.join(highlights)}")

                    tab1, tab2, tab3 = st.tabs(["💰 预算明细", "🏨 住宿", "📅 行程概览"])

                    with tab1:
                        c1, c2, c3 = st.columns(3)
                        c1.metric("航班支出", f"¥{flight_cost:.0f}")
                        c2.metric("酒店支出", f"¥{hotel_cost:.0f}")
                        c3.metric("活动支出", f"¥{activity_cost:.0f}")

                        st.divider()
                        # 显示总计与预算对比
                        status_text = "符合预算" if is_within else "超出预算"
                        st.metric("总计 / 预算", f"¥{total_cost:.0f} / ¥{budget:.0f}",
                                  delta=f"{'剩余' if is_within else '超出'} ¥{abs(remaining):.0f}",
                                  delta_color="normal" if is_within else "inverse")

                        if rounds > 0:
                            st.info(f"系统经过 {rounds} 轮预算降级调整")

                    with tab2:
                        st.write(f"**推荐酒店:** {hotel_name}")
                        st.write(f"**入住时长:** {total_nights:.0f} 晚")
                        if hotel_info.get('starRating'):
                            st.write(f"**酒店星级:** {hotel_info.get('starRating')} ⭐")

                        # --- 新增：显示酒店设施 ---
                        amenities = hotel_info.get('amenities', [])
                        if amenities:
                            st.write(f"**包含设施:** {', '.join(amenities)}")

                    with tab3:
                        # --- 新增 1：渲染推荐航班 ---
                        st.markdown("#### ✈️ 推荐航班")
                        flight_info = result.get('flightSearchResult', {}).get('recommended', {})
                        if flight_info:
                            f1, f2, f3, f4 = st.columns(4)
                            f1.metric("航班", flight_info.get('flightNo', '-'))
                            f2.metric("航司", flight_info.get('airline', '-'))
                            f3.metric("历时", flight_info.get('duration', '-'))
                            f4.metric("中转", f"{flight_info.get('stops', 0)} 次")
                        else:
                            st.info("暂无航班数据")

                        st.divider()

                        # --- 新增 2：渲染每日行程安排 ---
                        st.markdown("#### 📍 每日行程安排")
                        day_plans = result.get('activitySearchResult', {}).get('dayPlans', [])
                        if day_plans:
                            for index, plan in enumerate(day_plans):
                                date_str = plan.get('date', f"第 {index + 1} 天")
                                day_cost = plan.get('dayCost', 0)

                                # 使用 expander 折叠面板按天展示行程
                                with st.expander(f"📅 {date_str} | 当日活动花费预估: ¥{day_cost:.0f}", expanded=True):
                                    activities = plan.get('activities', [])
                                    if activities:
                                        for act in activities:
                                            time_slot = act.get('timeSlot', '未知')
                                            act_name = act.get('name', '自由活动')
                                            category = act.get('category', '-')
                                            duration = act.get('duration', '-')
                                            price = act.get('price', 0)

                                            # 使用 Markdown 和 Caption 美化活动列表
                                            st.markdown(f"- **【{time_slot}】 {act_name}**")
                                            st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;🏷️ {category} | ⏱️ 时长: {duration} | 💰 花费: ¥{price:.0f}")
                                    else:
                                        st.write("全天自由活动")
                        else:
                            st.info("暂无具体行程数据")

                        st.divider()

                        # --- 3. 保留原有的 JSON 视图以供调试，但将其折叠起来 ---
                        with st.expander("🔍 查看后端原始 JSON 数据 (Debug)"):
                            st.json(result)

                else:
                    response.raise_for_status()

            except requests.exceptions.RequestException as e:
                st.error(f"调用 Java 服务失败，请确认服务已在 8080 端口启动。详细错误: {e}")

    else:
        st.info("👈 请在左侧填写旅行偏好，然后点击“开始规划”")
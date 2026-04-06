package com.travel.orchestrator;

import com.travel.agent.ActivityAgent;
import com.travel.agent.FlightAgent;
import com.travel.agent.HotelAgent;
import com.travel.model.PlanningState;
import com.travel.model.TravelPlanState;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

/**
 * 并行执行器：使用 {@link CompletableFuture#allOf(CompletableFuture[])} 聚合航班/酒店/活动三类检索。
 * <p>
 * 设计模式与面试表述：
 * <ul>
 *     <li><b>并行分解</b>：无依赖的子任务同时执行，缩短端到端延迟（Amdahl 定律视角）；</li>
 *     <li><b>共享上下文</b>：三个 Agent 写入 {@link TravelPlanState} 的不同字段，需事先约定字段边界以防竞态；</li>
 *     <li><b>异常策略</b>：当前使用 {@code join()} 传播未检查异常；生产可改为 {@code handle} 或舱壁隔离。</li>
 * </ul>
 * </p>
 */
@Component
public class ParallelExecutor {

    private static final Logger log = LoggerFactory.getLogger(ParallelExecutor.class);

    private final FlightAgent flightAgent;
    private final HotelAgent hotelAgent;
    private final ActivityAgent activityAgent;
    private final Executor travelPlanningExecutor;

    public ParallelExecutor(
            FlightAgent flightAgent,
            HotelAgent hotelAgent,
            ActivityAgent activityAgent,
            @Qualifier("travelPlanningExecutor") Executor travelPlanningExecutor) {
        this.flightAgent = flightAgent;
        this.hotelAgent = hotelAgent;
        this.activityAgent = activityAgent;
        this.travelPlanningExecutor = travelPlanningExecutor;
    }

    /**
     * 并行触发三个 Agent；调用方需保证 {@code state} 已具备偏好与目的地。
     */
    public void runParallel(TravelPlanState state) {
        if (state.getPlanningState() == PlanningState.FAILED) {
            return;
        }
        state.setPlanningState(PlanningState.PARALLEL_SEARCH);
        log.info("CompletableFuture.allOf：并行启动 Flight / Hotel / Activity 三个 Agent");

        CompletableFuture<Void> fFlight = CompletableFuture.runAsync(
                () -> flightAgent.run(state), travelPlanningExecutor);
        CompletableFuture<Void> fHotel = CompletableFuture.runAsync(
                () -> hotelAgent.run(state), travelPlanningExecutor);
        CompletableFuture<Void> fActivity = CompletableFuture.runAsync(
                () -> activityAgent.run(state), travelPlanningExecutor);

        CompletableFuture.allOf(fFlight, fHotel, fActivity).join();
    }
}

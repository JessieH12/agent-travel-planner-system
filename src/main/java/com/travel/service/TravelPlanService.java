package com.travel.service;

import com.travel.model.TravelPlanState;
import com.travel.model.UserPreferences;
import com.travel.orchestrator.TravelPlanningPipeline;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * 应用服务层：对外暴露「生成行程」用例，隐藏编排细节。
 * <p>
 * 经典 DDD/分层：Controller → Service → Domain/Orchestrator。
 * 后续若引入事务、鉴权、审计，优先挂载在本层。
 * </p>
 */
@Service
public class TravelPlanService {

    private static final Logger log = LoggerFactory.getLogger(TravelPlanService.class);

    private final TravelPlanningPipeline pipeline;

    public TravelPlanService(TravelPlanningPipeline pipeline) {
        this.pipeline = pipeline;
    }

    /**
     * 根据用户偏好执行完整多智能体规划。
     */
    public TravelPlanState plan(UserPreferences preferences) {
        log.info("TravelPlanService 接收规划请求: 出发={} 人数={}",
                preferences != null ? preferences.getDepartureCity() : null,
                preferences != null ? preferences.getTravelers() : 0);
        return pipeline.execute(preferences);
    }
}

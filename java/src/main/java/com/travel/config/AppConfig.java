package com.travel.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

/**
 * 应用级配置。
 * <p>
 * 为 {@link com.travel.orchestrator.ParallelExecutor} 提供专用线程池，
 * 避免在并行阶段使用 {@link java.util.concurrent.ForkJoinPool#commonPool()} 与业务无关任务抢资源。
 * 面试点：线程池隔离、命名线程便于排查、队列容量与拒绝策略在生产环境需再评估。
 * </p>
 */
@Configuration
public class AppConfig {

    @Bean(name = "travelPlanningExecutor")
    public Executor travelPlanningExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(4);
        executor.setMaxPoolSize(8);
        executor.setQueueCapacity(200);
        executor.setThreadNamePrefix("travel-plan-");
        executor.initialize();
        return executor;
    }
}

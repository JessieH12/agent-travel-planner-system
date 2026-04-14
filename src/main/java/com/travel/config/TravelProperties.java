package com.travel.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "travel")
public class TravelProperties {

    private ThreadPool threadPool = new ThreadPool();
    private Budget budget = new Budget();

    @Data
    public static class ThreadPool {
        private int coreSize = 10;
        private int maxSize = 50;
        private int queueCapacity = 100;
    }

    @Data
    public static class Budget {
        private int maxRounds = 3;
        private int maxPressure = 2;
    }
}
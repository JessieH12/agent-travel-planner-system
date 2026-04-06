// Command server 启动 Gin HTTP 服务，对外暴露旅行规划 API。
//
// 面试要点：
//   - main 只负责「组装依赖 + 启动监听」，保持短小；
//   - 配置来自环境变量（config 包），服务模式可容器化部署；
//   - 全局 Logger、Tracer、Graceful shutdown 等可在后续迭代中按同样方式挂载。
package main

import (
	"log"

	"github.com/gin-gonic/gin"

	"travel-planner/internal/config"
	"travel-planner/internal/handler"
	"travel-planner/internal/orchestrator"
)

func main() {
	cfg := config.LoadFromEnv()
	gin.SetMode(cfg.GinMode)

	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(gin.Logger())

	pipe := orchestrator.NewTravelPipeline()
	h := handler.NewTravelHandler(pipe)
	h.RegisterRoutes(r)

	log.Printf("travel-planner 监听 %s (GIN_MODE=%s, LLM_MOCK=%v)\n", cfg.Addr, cfg.GinMode, cfg.LLMMock)
	if err := r.Run(cfg.Addr); err != nil {
		log.Fatalf("服务退出: %v", err)
	}
}

// Package handler 提供 Gin HTTP 接入层，将 JSON 请求转换为领域状态并调用编排器。
//
// 面试要点：
//   - handler 薄：只做参数绑定、状态构造、错误映射与 JSON 响应；
//   - 业务编排放在 orchestrator，符合分层架构与可测试性。
package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"travel-planner/internal/model"
	"travel-planner/internal/orchestrator"
)

// TravelHandler 依赖注入流水线，便于测试替换。
type TravelHandler struct {
	pipeline *orchestrator.TravelPipeline
}

// NewTravelHandler 构造处理器。
func NewTravelHandler(p *orchestrator.TravelPipeline) *TravelHandler {
	if p == nil {
		p = orchestrator.NewTravelPipeline()
	}
	return &TravelHandler{pipeline: p}
}

// PlanRequest POST /api/plan 的请求体（字段与 model.UserPreferences 对齐）。
type PlanRequest struct {
	OriginCity   string            `json:"origin_city"`
	DurationDays int               `json:"duration_days"`
	BudgetCNY    float64           `json:"budget_cny"`
	TravelStyle  model.TravelStyle `json:"travel_style"`
	Interests    []string          `json:"interests"`
}

// RegisterRoutes 注册路由。
func (h *TravelHandler) RegisterRoutes(r *gin.Engine) {
	r.GET("/api/health", h.Health)
	r.POST("/api/plan", h.Plan)
}

// Health GET /api/health 存活探针（K8s / 负载均衡常用）。
func (h *TravelHandler) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "ok",
		"service": "travel-planner",
	})
}

// Plan POST /api/plan 触发完整多智能体流水线。
func (h *TravelHandler) Plan(c *gin.Context) {
	var req PlanRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "JSON 解析失败", "detail": err.Error()})
		return
	}

	prefs := model.UserPreferences{
		OriginCity:   req.OriginCity,
		DurationDays: req.DurationDays,
		BudgetCNY:    req.BudgetCNY,
		TravelStyle:  req.TravelStyle,
		Interests:    req.Interests,
	}

	state := model.NewTravelPlanState(prefs)
	if err := h.pipeline.Run(c.Request.Context(), state); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
			"state": state,
		})
		return
	}

	c.JSON(http.StatusOK, state)
}

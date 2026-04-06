// Package config 集中读取环境变量，避免在 main 与 handler 中散落 os.Getenv（12-factor 配置原则）。
package config

import (
	"os"
	"strconv"
)

// Config 服务运行时配置。
type Config struct {
	// Addr 监听地址，例如 ":8080"
	Addr string
	// GinMode debug | release | test
	GinMode string
	// LLMMock 为 true 时使用 pkg/llm 的占位实现，不进行外呼。
	LLMMock bool
}

// LoadFromEnv 从环境变量加载；未设置时使用合理默认值。
//
// 支持的环境变量：
//   - PORT：监听端口，默认 8080（最终 Addr 为 ":"+PORT）
//   - GIN_MODE：默认 release
//   - LLM_MOCK：默认 true（演示环境）；设为 false 时仍不会自动连网，仅预留开关语义。
func LoadFromEnv() Config {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	ginMode := os.Getenv("GIN_MODE")
	if ginMode == "" {
		ginMode = "release"
	}

	mock := true
	if v := os.Getenv("LLM_MOCK"); v != "" {
		if b, err := strconv.ParseBool(v); err == nil {
			mock = b
		}
	}

	return Config{
		Addr:    ":" + port,
		GinMode: ginMode,
		LLMMock: mock,
	}
}

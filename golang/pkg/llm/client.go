// Package llm 预留大模型调用层：当前为 Mock，用于演示「Agent 未来可接 LLM 做意图解析/重排」。
//
// 面试要点：
//   - 通过接口 + 构造注入，避免业务代码直接依赖具体供应商 SDK；
//   - MockClient 可录制固定输出，便于 CI 与单测稳定复现。
package llm

import (
	"context"
	"fmt"
)

// Client 抽象 LLM 能力（最小子集：文本生成）。
type Client interface {
	Generate(ctx context.Context, systemPrompt, userPrompt string) (string, error)
}

// MockClient 占位实现：不发起网络请求，返回可预测的说明文本。
type MockClient struct {
	// Provider 仅用于日志标识
	Provider string
}

// NewMockClient 创建 Mock 客户端。
func NewMockClient() *MockClient {
	return &MockClient{Provider: "mock-local"}
}

// Generate 模拟一次「推理延迟」式的同步返回（真实实现应处理流式、重试、限流）。
func (m *MockClient) Generate(ctx context.Context, systemPrompt, userPrompt string) (string, error) {
	_ = ctx
	if m == nil {
		return "", fmt.Errorf("llm.MockClient: nil")
	}
	// 演示：将 prompt 摘要拼进输出，证明调用链可达（当前业务 Agent 未强制调用，避免耦合）。
	return fmt.Sprintf("[MOCK LLM/%s] system=%d chars, user=%d chars → 建议继续使用规则引擎与 Mock 数据完成演示。",
		m.Provider, len(systemPrompt), len(userPrompt)), nil
}

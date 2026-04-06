# Python 版本 - 多Agent智能旅游行程规划系统

> 主力版本，包含完整的 6-Agent 实现、Pipeline 编排、并行执行、预算循环。

## 快速运行

```bash
# 安装依赖
pip install -r requirements.txt

# CLI 运行
python main.py
python main.py --budget 15000 --departure 上海 --start 2026-06-01 --end 2026-06-07

# 启动 API 服务 (http://localhost:8000)
python -m api.app

# 启动 Streamlit 前端
streamlit run ui/streamlit_app.py

# 运行测试
python -m pytest tests/ -v
```

## 技术栈

- **Python 3.10+**
- **Pydantic v2** - 数据模型与校验
- **asyncio** - 并行 Agent 执行
- **FastAPI** - REST API
- **Streamlit** - 交互式前端
- **loguru** - 日志
- **pytest** - 测试

## 模块说明

| 目录 | 说明 |
|------|------|
| `agents/` | 6 个 Agent 实现 + 基类 |
| `orchestrator/` | Pipeline 编排 + 并行执行 + 预算循环 |
| `models/` | Pydantic 数据模型 |
| `tools/` | Mock 搜索工具（航班/酒店/活动/天气） |
| `api/` | FastAPI REST API |
| `ui/` | Streamlit 前端 |
| `tests/` | 单元测试（10 个测试用例） |
| `config/` | 配置管理 |

## 环境变量

复制 `.env.example` 为 `.env` 进行配置。默认 Mock 模式不需要任何配置。

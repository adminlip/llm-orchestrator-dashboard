# LLM Orchestrator Dashboard

一个可扩展的多模型主从协作平台（可直接跑）。

## 功能

- 主模型可切换
- 子代理并行执行并汇总
- 支持故障切换与故障记录
- 可扩展接入 Hermes、OpenClue、CodeClue 及 OpenAI 兼容平台
- 自带 Web 展示页

## 技术栈

- FastAPI
- 原生 HTML + Tailwind CDN
- JSON 配置存储

## 目录结构

- `app/main.py`：FastAPI 入口
- `app/models.py`：数据模型
- `app/registry.py`：模型注册中心
- `app/orchestrator.py`：主从编排逻辑
- `app/platforms.py`：平台适配抽象
- `app/store.py`：本地状态存储
- `app/templates/index.html`：展示页
- `data/registry.json`：模型与平台配置样例

## 快速启动

### Windows

双击：

```text
start.bat
```

脚本会自动：

- 检查 Python
- 创建 `.venv`
- 从 `.env.example` 生成 `.env`
- 安装依赖
- 打开浏览器
- 启动服务

### Linux / macOS

```bash
chmod +x start.sh
./start.sh
```

### 手动启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

打开：`http://127.0.0.1:8000`

## 开箱即用说明

- 首次启动会自动加载 `data/registry.json`
- 默认主模型：`mimo-primary`
- 默认子代理：`glm-worker`、`codeclue-worker`
- 当前平台调用为 Mock 模式（用于项目演示）
- 如果 `.env` 中配置了有效 `OPENAI_API_KEY`，OpenAI 兼容平台会自动走真实接口

## 环境变量

首次运行 `start.bat` / `start.sh` 会自动复制 `.env.example` 为 `.env`。

常用配置：

```env
OPENAI_API_KEY=your-openai-compatible-key
CODECLUE_API_KEY=your-codeclue-key
OPENCLUE_API_KEY=your-openclue-key
HERMES_API_URL=http://127.0.0.1:8642
```

如果不填 API Key，项目仍然可以运行，平台适配器会进入 Mock 模式。

## 常用 API

### 1) 健康检查

```bash
curl http://127.0.0.1:8000/api/health
```

### 2) 查看全部模型

```bash
curl http://127.0.0.1:8000/api/models
```

### 3) 运行一次主从编排

```bash
curl -X POST http://127.0.0.1:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"比较 Hermes 和 CodeClue 的代码协作能力"}'
```

### 4) 手动切换主模型

```bash
curl -X POST http://127.0.0.1:8000/api/primary/switch \
  -H "Content-Type: application/json" \
  -d '{"model_id":"claude-backup","reason":"manual promotion"}'
```

### 5) 手动触发故障切换

```bash
curl -X POST "http://127.0.0.1:8000/api/failover?reason=manual_failover"
```

## 当前设计

- 主模型负责拆任务、汇总结果、输出最终结论
- 子代理负责并行执行子任务
- 主模型故障时自动提升可用备用模型
- 原主模型恢复后可重新降级为子代理或手动切回

## 后续可扩展

- 接入真实 Hermes Gateway API
- 接入 OpenClue / CodeClue SDK
- 流式输出
- 成本统计
- 模型评分与自动路由

## 部署

支持：

- Windows：`start.bat`
- Linux / macOS：`start.sh`
- Docker：`docker compose up -d --build`
- Linux systemd
- Nginx 反向代理

详细说明见：[`DEPLOY.md`](DEPLOY.md)

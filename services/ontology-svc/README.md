# ontology-svc —— UDOM 本体服务（M2）

本体元模型的**唯一权威来源**与**校验入口**：一处定义（`ontology/metamodel.yaml`），
三处消费（文档规范 / Extractor 输出契约 / 校验规则源）。

## API 一览（v0.2.0）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 存活 + 当前元模型版本 |
| GET | `/v1/metamodel` | 完整元模型（类型/关系/枚举/规则） |
| GET | `/v1/metamodel/contract` | **给 Extractor 的紧凑契约**：kinds（必填属性+clues）、relations（from/to/card）、输出格式要求 |
| POST | `/v1/models/validate` | 校验模型实例（结构+基数+R1–R10+状态门禁），返回 `{verdict, errors[], warns[]}` |
| POST | `/v1/models` | 校验并暂存到 SQLite staging 库，返回模型 id |
| GET | `/v1/models` / `/v1/models/{id}` | 暂存模型列表 / 详情 |

交互式 API 文档：服务启动后访问 `/docs`（Swagger UI）。

## 本地运行（无 Docker）

```bash
# repo 根目录
.venv/bin/pip install -r services/ontology-svc/requirements.txt
.venv/bin/uvicorn app:app --app-dir services/ontology-svc --port 8090
```

## Docker 运行（与 WeKnora 叠加）

```bash
docker build -f services/ontology-svc/Dockerfile -t ontodomain/ontology-svc:0.2.0 .
# 或一键全栈（WeKnora + 本服务）：
scripts/start-stack.sh
```

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `PORT` | 8090 | 服务端口 |
| `UDOM_METAMODEL` | `ontology/metamodel.yaml` | 元模型路径（版本化治理入口） |
| `UDOM_DB` | `data/models.db` | SQLite 暂存库路径 |

## 客户端示例

```python
import httpx, yaml
inst = yaml.safe_load(open('poc/after-sales.candidate.yaml', encoding='utf-8'))
r = httpx.post('http://localhost:8090/v1/models/validate', json={'model': inst})
print(r.json()['verdict'])   # PASS
```

## 设计说明

- **校验内核复用** `tools/validator/validate.py` 的 `Checker`（不复制代码），CLI 与 API 行为一致；
- **staging/commit 语义**（批准流、版本树）属 M4，本版暂存库仅做校验+存取；
- 与 WeKnora 的关系：独立服务、REST 对接、共享 `WeKnora-network`（浅 fork 策略，见 `docs/architecture.md` C1）。

# OntoDomain Studio —— 本体驱动的领域建模与智能化改造知识库

> 用**统一领域本体（UDOM）**约束和指导：存量系统智能化改造 + 新建系统领域建模。
> 整合 **BMM（业务动机模型）** × **DDD（领域驱动设计）** × **AgentOps（智能体工程元素）**，
> 基于腾讯 [WeKnora](https://github.com/Tencent/WeKnora)（MIT）构建知识库底座，
> 由建模智能体依据本体从业务/技术文档中抽取领域模型，人工审校后以 MCP 形式
> 向开发智能体提供"模型即上下文"（Model-as-Context）。

## 三步走

| 步骤 | 内容 | 状态 |
|---|---|---|
| **① 确认本体模型** | `docs/ontology-spec.md`（规范）+ `ontology/metamodel.yaml`（机器可读元模型） | ✅ 草案待评审 |
| **② 确认方案架构** | `docs/architecture.md`（WeKnora fork 策略 / 模型库选型 / 智能体流水线 / 验证方案） | ✅ 草案待评审 |
| **③ 构建与验证** | 见下方路线图 M1–M6 | 🚧 骨架已起步 |

## 仓库结构

```
├── docs/
│   ├── ontology-spec.md      # ① 本体模型规范（人读）：BMM×DDD×AgentOps 概念对齐
│   └── architecture.md       # ② 方案架构：组件、数据流、关键决策、验证指标
├── ontology/
│   ├── metamodel.yaml        # 机器可读元模型 v0.1.1：类型/关系/约束规则（智能体的建模契约）
│   └── examples/
│       └── fulfillment.example.yaml  # 示例实例：履约异常域（可通过校验器全量校验）
├── poc/
│   ├── corpus/               # PoC 模拟语料：业务白皮书 + 系统接口说明
│   └── after-sales.candidate.yaml    # 抽取候选模型（72元素/71关系，校验全绿）
├── agents/
│   └── extractor.prompt.md   # 抽取智能体提示词契约 v1（两遍法/无证据不出元素）
├── tools/
│   └── validator/validate.py # 本体校验器：结构校验 + 规则引擎（R1–R10 + 状态门禁）
├── services/ontology-svc/    # 本体服务（FastAPI）：元模型分发/校验API/暂存库(SQLite)
├── deploy/docker-compose.ontology.yml  # 叠加编排：ontology-svc 加入 WeKnora-network
├── scripts/start-stack.sh    # 一键全栈启动（WeKnora + ontology-svc，需 Docker）
├── third_party/WeKnora/      # WeKnora v0.8.2（git submodule，浅 fork 只 vendor 不改内核）
└── .venv/                    # Python 环境（pyyaml/fastapi/uvicorn）
```

## 快速开始：校验示例模型

```bash
.venv/bin/python tools/validator/validate.py ontology/metamodel.yaml ontology/examples/fulfillment.example.yaml
.venv/bin/python tools/validator/validate.py ontology/metamodel.yaml poc/after-sales.candidate.yaml
```

## 路线图

| 里程碑 | 内容 |
|---|---|
| M1 | 本体元模型 + 校验器 + 示例（**本次已交付**） |
| M2 | ✅ **已完成**：WeKnora v0.8.2 已 vendor（submodule）；ontology-svc 骨架可运行（6 端点冒烟全过）；compose 叠加编排就绪（本沙箱无 Docker，全栈运行需在 Docker 环境执行 `scripts/start-stack.sh`） |
| M3 | ~~抽取 PoC~~ **本体覆盖度 PoC 已提前完成**（模拟语料验证，见 `docs/poc-report.md`）；待工程化为真实 Extractor 服务 |
| M4 | 模型库存储 + 人工审校台（HITL）+ 规则校验流水线 |
| M5 | 模型 MCP Server：向 IDE/代码生成智能体暴露领域模型 |
| M6 | 端到端验证：真实文档语料上的 P/R、规则符合率、人工修改率 |

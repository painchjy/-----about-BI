# 统一领域本体模型（UDOM）规范 v0.1

> Unified Domain Ontology Metamodel —— 整合 BMM × DDD × AgentOps 的领域建模本体。
> 机器可读版本见 `ontology/metamodel.yaml`，两者保持同步。

## 1. 为什么三者必须整合为一个本体

三者在企业智能化建模中回答三个不同但首尾相接的问题：

| 层 | 来源 | 回答的问题 | 产出 |
|---|---|---|---|
| 动机层 | **BMM**（OMG Business Motivation Model） | **为什么**做？值不值得？约束是什么？ | 愿景/使命/目标/指标/策略/业务政策/业务规则/风险 |
| 领域层 | **DDD** | 业务**是什么**结构？边界在哪？ | 子域/限界上下文/通用语言/聚合/上下文映射 |
| 智能体层 | **AgentOps**（前文讨论的智能体工程元素） | **如何智能化**执行？自主到什么程度？ | 智能体/技能/工具/护栏/评测/上下文设计 |
| 资产层 | （补充） | 改造/包装的**对象**是谁？ | 存量系统/数据/接口/组织 |
| 内核层 | （补充） | 每个结论的**依据**是什么？ | 证据/溯源/置信度/治理状态 |

### 1.1 关键洞察：概念对齐，而不是概念堆叠

评审中已发现：智能体工程元素与 BMM 存在天然对应（使命↔Mission、成功指标↔Objective）。
**这不是偶然相似，而是同一业务概念在不同层的投影**。因此本体的设计原则是"归并"而非"并集"：

| 智能体工程概念 | 本质上是 | 本体中的归并方式 |
|---|---|---|
| Agent 使命 | BMM **Mission** 在单个智能体上的投影 | `Agent —hasMission→ Mission`（引用，不复制） |
| Agent 成功指标 | BMM **Objective**（可度量的期望结果，即 KPI） | `Agent —hasObjective→ Objective` |
| Agent 升级/转人工规则 | BMM **BusinessPolicy**（指导行动方针的指令） | `Agent —escalatesVia→ BusinessPolicy` |
| 护栏 Guardrail | BMM **BusinessRule** 的可执行化 | `Guardrail —enforces→ BusinessRule` |
| 评测 Eval | BusinessRule 的**实例化规约**（spec-by-example） | `Eval —specifies→ BusinessRule`、`Eval —validates→ Agent` |
| 技能 Skill | **业务能力**的智能体实现（领域服务 + 程序性知识） | `Skill —realizes→ BusinessCapability` |
| MCP Server（包装遗留系统） | DDD 上下文映射中的 **ACL / 开放主机服务** | `MCPServer —wraps→ System`，pattern=acl/ohs |

**收益**：当业务改一个 BusinessRule（如赔付上限），可以沿边找到受影响的 Guardrail、Eval、
Agent、Skill——这就是本体带来的**影响分析能力**，也是"用本体约束智能化改造"的核心价值。

## 2. 设计原则

1. **溯源优先（Evidence-first）**：每个模型元素必须挂证据（文档片段引用），
   区分 `human / agent / import` 来源并带置信度——没有证据的元素视为"待验证"。
2. **人在环路（HITL）**：元素有状态机 `draft → proposed → reviewed → approved → deprecated`，
   智能体只能产出 `draft/proposed`，`approved` 必须人工确认。
3. **本体即契约**：`metamodel.yaml` 同时是 ①文档规范 ②抽取智能体的结构化输出 Schema
   ③校验器的规则源——一处定义，三处消费。
4. **确定性内核 + 概率性外壳**：BusinessRule 的 enforcement 标注 `code/guardrail/manual/hybrid`，
   凡 `code` 的规则必须落到领域模型（聚合不变量/应用服务），而不是提示词里。
5. **最小完备**：v0.1 只收录有明确消费者（抽取/校验/生成/MCP 服务）的元素，避免本体膨胀。


## 3. 元素定义总表（按层）

> 完整机器可读定义（含必填项、枚举、抽取线索 clues）见 `ontology/metamodel.yaml`。
> 所有元素继承内核基座：`id / name / kind / description / aliases / status /
> provenance{origin, agent, confidence} / evidence[]`。

### 3.1 内核层 kernel
| 类型 | 定义 | 关键属性 |
|---|---|---|
| Evidence | 模型元素→知识库文档片段的溯源链接 | doc_title, doc_type, fragment(原文摘录), location |

### 3.2 动机层 motivation（BMM 对齐）
| 类型 | BMM 对应 | 定义 | 关键属性 |
|---|---|---|---|
| Vision | End | 组织未来期望成为的样子 | statement |
| Mission | Mean | 使愿景可操作的持续性经营活动 | statement |
| Goal | Desired Result | 定性的长期期望结果 | statement |
| Objective | Desired Result | 可度量、有时限的结果台阶（≈KPI） | statement, metric{name,unit,target,baseline,deadline} |
| Strategy | Course of Action | 通向目标的行动方针 | statement |
| Tactic | Course of Action | 落实战略的具体短期行动 | statement |
| BusinessPolicy | Directive | 指导行动方针、不可直接执行的指令 | statement |
| BusinessRule | Directive | 可操作、可强制执行的指令 | statement, enforcement(code/guardrail/manual/hybrid) |
| Influencer | Influencer | 影响动机的内外部因素 | kind(internal/external) |
| Assessment | Assessment | 对影响因子的评估（如 SWOT） | technique, finding |
| Risk | Potential Impact | 对目标/指标的潜在负面影响 | severity, likelihood |

### 3.3 领域层 domain（DDD 对齐）
| 类型 | 定义 | 关键属性 |
|---|---|---|
| Domain | 子域（core/supporting/generic） | kind |
| BusinessCapability | 业务能力——桥接战略与限界上下文的"粘合剂" | level(1-3) |
| BoundedContext | 限界上下文——模型与语言的一致性边界，**智能体的归属单位** | — |
| GlossaryTerm | 通用语言词条 | term, definition |
| Aggregate | 聚合根——一致性边界，不变量的代码化载体 | invariants[] |
| Entity / ValueObject | 实体 / 值对象 | identity / attributes[] |
| DomainService / DomainEvent / ApplicationService | 领域服务 / 领域事件 / 应用服务 | — / payload / operations |

> 上下文映射不建实体类型，用关系 `contextRelationship(pattern=customer_supplier|acl|ohs|…)` 表达。

### 3.4 智能体层 agent（AgentOps）
| 类型 | 定义 | 关键属性 |
|---|---|---|
| Agent | 智能体（章程：使命/边界/自主级别/升级规则） | autonomy(L0–L4), charter{scope_in, scope_out} |
| Skill | 技能 = 程序性知识(指令) + 工具 + 资源 | instructions |
| Tool | 工具契约 | semantics, side_effects(none/read/write/external), idempotent, permissions[] |
| MCPServer | MCP 服务（包装存量系统 ≈ DDD 的 ACL/OHS） | pattern(acl/ohs/pl/hybrid) |
| ContextDesign | 上下文工程设计（知识源/检索策略/预算） | retrieval_strategy, context_budget_tokens |
| Memory | 记忆 | tier(working/episodic/semantic), store, retention |
| Eval | 评测（行为规约，spec-by-example） | kind(golden_case/rubric/trajectory/regression), pass_criteria |
| Guardrail | 护栏 | kind(input_filter/output_filter/validator/hitl/rate_limit), action(block/review/redact/escalate) |
| ObservabilityProfile | 可观测配置（trace/成本/质量指标） | metrics[] |

### 3.5 资产层 asset
| 类型 | 定义 | 关键属性 |
|---|---|---|
| System | 存量/外采/新建系统 | kind(legacy/saas/new), criticality |
| DataStore / Interface | 数据存储 / 既有接口 | — / protocol, spec_ref |

## 4. 关系目录（边类型）

关系是一等公民：`{type, source, target, attrs?, provenance, confidence, status}`。

| 关系 | 源 → 目标 | 含义 / 基数约束 |
|---|---|---|
| **动机层内部** |||
| makesOperative | Mission → Vision | 使命使愿景可操作（R10：应有 ≥1） |
| measures | Objective → Goal | 指标度量目标（R1：必填 ≥1） |
| channelsEffortsToward | Strategy → Goal | 战略资源投向目标 |
| implements | Tactic → Strategy | 战术落实战略 |
| governs | BusinessPolicy → Strategy/Tactic/Agent | 政策指导行动 |
| derivesFrom | BusinessRule → BusinessPolicy | 规则源自政策 |
| enforcedBy | BusinessRule → Guardrail/ApplicationService | 规则的执行点（R4：应有 ≥1） |
| assesses / threatens | Assessment → Influencer；Risk → Goal/Objective | 评估 / 风险威胁 |
| **桥接层（核心价值链）** |||
| enables | BusinessCapability → Strategy | 能力支撑战略 |
| realizes | BoundedContext/Skill → Capability | 上下文/技能实现能力（R7：Skill 必填 ≥1） |
| within | BoundedContext → Domain | 上下文归属子域 |
| **领域层内部** |||
| contains | BoundedContext → Aggregate/GlossaryTerm/… | 边界内成员 |
| partOf | Entity/ValueObject → Aggregate | 聚合组成 |
| raises | Aggregate/DomainService → DomainEvent | 事件来源 |
| contextRelationship | BoundedContext ↔ BoundedContext | pattern 必填（R9）：customer_supplier/acl/ohs/… |
| **智能体层** |||
| hasMission | Agent → Mission | 使命引用（R2：恰为 1） |
| hasObjective | Agent → Objective | 成功指标引用 |
| belongsTo | Agent → BoundedContext | 归属上下文（R2：恰为 1） |
| escalatesVia | Agent → BusinessPolicy | 升级/转人工规则 |
| ownsSkill / invokes | Agent → Skill；Skill → Tool | 能力装配 |
| backedBy | Tool → ApplicationService/DomainService/System | 工具的确定性后端 |
| wraps / exposes | MCPServer → System；MCPServer → Tool | 存量包装 / 工具暴露 |
| hasContextDesign / usesMemory | Agent → ContextDesign；Agent/Skill → Memory | 上下文与记忆 |
| validates / specifies | Eval → Agent/Skill；Eval → BusinessRule | 评测对象 / 规约的规则 |
| enforces / protects | Guardrail → BusinessRule/Policy；Guardrail → Agent/Skill | 护栏执行点 / 保护对象 |
| ownedBy | System/BoundedContext → OrganizationUnit | 归属组织 |

## 5. 约束规则（校验器执行，见 metamodel.yaml rules 节）

| 规则 | 级别 | 内容 |
|---|---|---|
| R1 | error | Objective 必须 `measures` ≥1 个 Goal |
| R2 | error | Agent 必须恰有 1 个 `hasMission` 和 1 个 `belongsTo` |
| R3 | error | Tool 必填 `side_effects` 与 `idempotent` |
| R4 | warn | 未废弃的 BusinessRule 应有 ≥1 个执行点（Guardrail 或 ApplicationService） |
| R5 | error | Agent 自主级别 ≥L2 ⇒ 必须有 ≥1 个 `kind=hitl` 的 Guardrail `protects` 它，且 ≥1 个 Eval `validates` 它 |
| R6 | warn | 每个元素（除 Evidence）应有 ≥1 条证据链接（溯源完整性） |
| R7 | error | Skill 必须 `realizes` ≥1 个 BusinessCapability |
| R8 | warn | 同一 BoundedContext 内 GlossaryTerm.term 应唯一 |
| R9 | error | contextRelationship 必须带合法 pattern 枚举 |
| R10 | warn | Mission 应 `makesOperative` ≥1 个 Vision |

## 6. 治理、溯源与置信度

- **状态机**：`draft → proposed → reviewed → approved → deprecated`；
  抽取智能体最高只能产出 `proposed`，`approved` 需人工在审校台确认。
- **置信度**：`provenance.confidence ∈ [0,1]`，由抽取智能体自评 + Critic 复核；
  低置信元素进入人工优先评审队列。
- **影响分析**：沿 `enforces/protects/validates/specifies/backedBy/wraps` 边做双向遍历，
  支持"改一条业务规则 → 列出受影响的护栏/评测/智能体/工具/系统"。

## 7. 版本与扩展策略

- 版本化：`metamodel.yaml` 语义化版本；实例文件声明 `udom: "0.1.0"`，校验器按版本校验。
- 已预留扩展（v0.2+）：OWL/SHACL 导出（接推理机）、Repository/Factory 等 DDD 战术模式、
  MCPResource/MCPPrompt、PotentialReward、多智能体 InteractionProtocol 实体化。
- 扩展原则：新增类型必须声明 ①所属层 ②消费者（抽取/校验/生成/MCP）③至少一条关系。

| OrganizationUnit | 组织单元（元素 owner） | — |

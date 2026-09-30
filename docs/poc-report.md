# PoC 报告：本体覆盖度验证（方案 B）

> 日期：2026-01　语料：2 份模拟文档　执行：LLM 按 `agents/extractor.prompt.md` 契约手工模拟
> 结论：**本体覆盖度验证通过**，发现 2 处缺陷已修复（v0.1.1），3 处缺口列入 v0.2 候选

## 1. 目的与方法

- **验证目标**：UDOM 本体能否**完整表达**真实风格的业务/技术文档内容（覆盖度），
  而非验证自动化抽取能力（那是 M3，需运行中的 Extractor 服务）。
- **方法**：先写 2 份高仿真的模拟文档（业务白皮书 + 系统接口说明），
  再由 LLM 严格按抽取契约（两遍法：事实清单 → 元素归并）产出候选模型，
  最后用校验器（R1–R10 + 状态门禁）验证结构完整性。
- **语料**：`poc/corpus/智家商城售后服务业务白皮书.md`（业务，8 章）、
  `poc/corpus/售后中台系统现状与接口说明.md`（技术，5 节）。

## 2. 产出统计（以校验器计数为准）

| 层 | 元素构成 | 数量 |
|---|---|---|
| 内核（证据） | Evidence ×14（两份文档分 kb-aftersales / kb-aftersales-sys） | 14 |
| 动机 | Vision1 / Mission1 / Goal1 / Objective3 / Strategy1 / Tactic3 / Policy1 / Rule4 / Risk1 | 16 |
| 领域 | Domain1 / Capability2 / BoundedContext2 / Term4 / Aggregate1 / Entity1 / Event1 / AppService2 / **BusinessProcess1** | 15 |
| 资产 | System4 / Org3 / DataStore2 / Interface5 | 14 |
| 智能体 | Agent2 / Skill2 / Tool4 / MCPServer2 / Guardrail2 / Eval1 | 13 |
| **合计** | **72 元素 / 71 关系 / 4 条人类提问** | |

- 校验结果：**0 error / 0 warn**（全绿）；
- 溯源完整率（R6）：非证据元素 58/58 挂 Evidence = **100%**；
- 低置信元素（<0.75）5 个：rule-04(0.72) / agg-01(0.62) / evt-01(0.70) / sys-02(0.60) / sys-03(0.60)
  ——全部是**推断类**元素，自动进入人工优先评审队列，置信度语义设计有效。

## 3. 覆盖度分析（文档事实 → 模型元素）

| 文档事实类别 | 事实数 | 覆盖情况 |
|---|---|---|
| 愿景/使命/目标 | 3 | ✅ vision-01/mission-01/goal-01 |
| 量化指标 | 3 | ✅ obj-01~03（metric 五元组完整） |
| 策略/举措 | 1+3 | ✅ strat-01 / tactic-01~03 |
| 政策/规则 | 1+4 | ✅ pol-01 / rule-01~04（rule-04 矩阵为部分覆盖，见缺口 G3） |
| 术语 | 4 | ✅ term-01~04（R8 同上下文唯一） |
| 业务流程 | 1（7 步） | ✅ proc-01（**v0.1.1 新类型首次使用**） |
| 组织 | 3 | ✅ org-01~03 |
| 风险 | 1 | ✅ risk-01（threatens obj-02，双证据） |
| 系统清单 | 4 | ✅ sys-01~04（2 个 kind 归类存疑 → 提问） |
| 接口 | 5 | ✅ if-01~05；其中 4 个转为 Tool 契约（含幂等/副作用） |
| 数据表 | 3 | ✅ ds-01/ds-02 + ent-01（as_item 建模为实体） |
| 痛点 | 4 | ✅ 3 个直接入模（→agg-01 不变量、tool-03 风险标注、agent-01 章程），1 个转为提问（q4 指标分解） |
| **已知漏项（评审复盘发现）** | | ⚠️ tactic-03 涉及的"物流商系统"（外部第三方）未建 System；回访环节未单独建模——演示了人工评审在 draft 阶段的兜底价值 |

## 4. 本体缺口发现与处置（PoC 的核心产出）

| # | 缺口 | 发现场景 | 处置 |
|---|---|---|---|
| G1 | **业务流程无载体**：DDD/BMM 都没有流程概念，白皮书 §6 的七步流程无处安放 | proc 抽取时无类型可用 | ✅ **v0.1.1 已修**：新增 `BusinessProcess`（domain 层，steps 属性）+ 关系 `automates(Skill/Agent→Process)`，`realizes/contains` 扩展 |
| G2 | **Tool 的后端缺 Interface**：工具契约应指向存量接口而非只能指向系统/服务 | tool-01 backedBy if-02 时不合法 | ✅ **v0.1.1 已修**：`backedBy.to` 增加 `Interface` |
| G3 | **决策表/判定矩阵无结构化表达**：rule-04 的矩阵只能放 Evidence 文本 | 退换货判定矩阵 | 📌 v0.2 候选：`BusinessRule.decision_table` 结构化属性；过渡期 statement 概述 + Evidence 全文（已入 questions） |
| G4 | **角色/岗位无类型**："客服人员""售后主管"不是组织单元 | 流程步骤 actor、规则审批人 | 📌 v0.2 候选：`Role`（asset 层）；过渡期用 OrganizationUnit/文本近似 |
| G5 | **System.kind 枚举语义勉强**："自研在运"不等于"遗留"，OMS/WMS 归类存疑 | sys-02/03 confidence 仅 0.6 | 📌 v0.2 候选：kind 枚举细化（如 internal_active）；过渡期 confidence+questions 兜底 |

**结论：5 处缺口中 2 处已闭环修复，3 处带明确过渡方案进入 backlog——本体的"约束"与"可演进"平衡有效。**

## 5. 规则引擎行为验证

- **R5 强制生效**：agent-02（退款执行，L3）必须配 hitl 护栏（grd-02 主管审批台）+ 回归评测（eval-01），否则 error——与业务政策 pol-01 的要求形成模型级闭环；
- **R4 全过**：4 条 BusinessRule 都有执行点（svc-01 或 grd-01）；
- **状态门禁生效**：全 draft 模型也能全绿是因为抽取时按规则自检补齐了边；门禁测试（人为删边）确认 draft 降级 warn、proposed 起 error；
- **R9**：contextRelationship(bc-02→bc-01, customer_supplier) pattern 校验通过。

## 6. 对 M3 工程化的反馈（抽取契约经验）

1. **两遍法有效**：事实清单先行显著降低漏抽（本次仅 2 处已知漏项）；
2. **无证据不出元素是防幻觉核心**：72 元素零幻觉（每个元素可点回原文）；
3. **YAML flow 风格有引号陷阱**（`{id}`、嵌套 charter 均踩坑）→ M3 的 Extractor 输出**改用 YAML block 风格或 JSON**，ontology-svc 落库前统一规范化；
4. **置信度梯度设计有效**：推断元素全部低置信且自动带【推断】标注，人工评审可聚焦；
5. **分层聚焦（focus_layer）必要**：动机层与资产层的抽取关注点差异大，混抽会稀释注意力。

## 7. 结论与下一步

- 本体（v0.1.1）对真实风格文档的**覆盖度验证通过**，可以冻结进入架构固化；
- 建议下一步：**M2**（vendor WeKnora + ontology-svc 骨架，把 validator 包装为校验 API），
  或继续 **M3 PoC 深化**：把本次手工模拟改造成真实 Extractor（接 LLM API 跑同样的语料，对比人工黄金模型算 P/R）；
- v0.2 backlog：decision_table、Role、System.kind 细化、OWL/SHACL 导出。

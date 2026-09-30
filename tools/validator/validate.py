#!/usr/bin/env python3
"""UDOM 模型实例校验器：结构校验 + 约束规则引擎（R1-R10）
用法: python validate.py <metamodel.yaml> <instance.yaml>
退出码: 0=通过(可含 warn)  1=存在 error
状态门禁: draft=中间态(error级降级为warn，容忍乱序抽取的不完整)；proposed起 error 生效；approved 必须全绿
"""
import sys
import yaml

AUTONOMY_ORDER = ["L0", "L1", "L2", "L3", "L4"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class Checker:
    def __init__(self, meta, inst):
        self.meta = meta
        self.types = meta["types"]
        self.rel_defs = meta["relations"]
        self.enums = meta.get("enums", {})
        self.inst = inst
        self.errors, self.warns = [], []
        self.elems = {}
        self.rels = inst.get("relations", []) or []
        self.out_count = {}   # (src_id, rel_type) -> n  每个源实例的出边计数
        self.in_rels = {}     # (tgt_id, rel_type) -> [rel]

    def err(self, rid, msg):  self.errors.append(f"[{rid}] {msg}")
    def warn(self, rid, msg): self.warns.append(f"[{rid}] {msg}")

    def report(self, level, e, rid, msg):
        """状态感知门禁：draft 中间态的 error 级违例降级为 warn"""
        if level == "error" and (e or {}).get("status") == "draft":
            self.warn(f"{rid}(draft降级)", msg)
        else:
            (self.err if level == "error" else self.warn)(rid, msg)

    def enum_values(self, spec):
        ev = spec.get("enum")
        if isinstance(ev, str):      # 引用 enums 节
            return self.enums.get(ev, [])
        return ev or []

    # ---------- 1. 元素结构校验 ----------
    def check_elements(self):
        for e in self.inst.get("elements", []) or []:
            eid, kind = e.get("id"), e.get("kind")
            if not eid or not kind:
                self.err("STRUCT", f"元素缺少 id/kind: {e}")
                continue
            if eid in self.elems:
                self.err("STRUCT", f"元素 id 重复: {eid}")
            self.elems[eid] = e
            tspec = self.types.get(kind)
            if not tspec:
                self.err("STRUCT", f"{eid}: 未知类型 kind={kind}")
                continue
            attrs = e.get("attrs", {}) or {}
            for aname, aspec in (tspec.get("attrs") or {}).items():
                if aspec.get("req") and aname not in attrs:
                    self.err("REQ", f"{eid}({kind}) 缺少必填属性 {aname}")
                if aname in attrs:
                    allowed = self.enum_values(aspec)
                    if allowed and attrs[aname] not in allowed:
                        self.err("ENUM", f"{eid}({kind}).{aname}={attrs[aname]} 非合法枚举 {allowed}")
        # evidence 引用存在且为 Evidence 类型
        for eid, e in self.elems.items():
            for ev in e.get("evidence", []) or []:
                if ev not in self.elems:
                    self.err("EVID", f"{eid} 引用了不存在的证据 {ev}")
                elif self.elems[ev].get("kind") != "Evidence":
                    self.err("EVID", f"{eid} 的证据 {ev} 类型不是 Evidence")

    # ---------- 2. 关系结构与基数校验 ----------
    def check_relations(self):
        for r in self.rels:
            rt, s, t = r.get("type"), r.get("source"), r.get("target")
            spec = self.rel_defs.get(rt)
            if not spec:
                self.err("STRUCT", f"未知关系类型 {rt}")
                continue
            se, te = self.elems.get(s), self.elems.get(t)
            if not se or not te:
                self.err("STRUCT", f"关系 {rt}({s}->{t}) 端点不存在")
                continue
            if se["kind"] not in spec["from"]:
                self.err("STRUCT", f"{rt} 源类型应为 {spec['from']}，实际 {se['kind']}({s})")
            if te["kind"] not in spec["to"]:
                self.err("STRUCT", f"{rt} 目标类型应为 {spec['to']}，实际 {te['kind']}({t})")
            # 关系属性（如 contextRelationship.pattern —— R9）
            for aname, aspec in (spec.get("attrs") or {}).items():
                val = (r.get("attrs") or {}).get(aname)
                if aspec.get("req") and val is None:
                    self.err("R9", f"{rt}({s}->{t}) 缺少必填关系属性 {aname}")
                if val is not None:
                    allowed = self.enum_values(aspec)
                    if allowed and val not in allowed:
                        self.err("R9", f"{rt}({s}->{t}).{aname}={val} 非合法枚举 {allowed}")
            self.out_count[(s, rt)] = self.out_count.get((s, rt), 0) + 1
            self.in_rels.setdefault((t, rt), []).append(r)
        # 基数（对每个源实例）
        for eid, e in self.elems.items():
            for rt, spec in self.rel_defs.items():
                if e["kind"] not in spec["from"]:
                    continue
                n = self.out_count.get((eid, rt), 0)
                card = spec.get("card", "0..*")
                if card == "1" and n != 1:
                    self.report("error", e, "CARD", f"{eid}({e['kind']}) 应有恰好 1 条 {rt}，实际 {n}")
                elif card == "1..*" and n < 1:
                    self.report("error", e, "CARD", f"{eid}({e['kind']}) 应有 ≥1 条 {rt}，实际 0")
                elif card == "0..1" and n > 1:
                    self.err("CARD", f"{eid}({e['kind']}) 应有 ≤1 条 {rt}，实际 {n}")

    # ---------- 3. 独立规则 R4-R8/R10 ----------
    def check_rules(self):
        active = [e for e in self.elems.values() if e.get("status") != "deprecated"]
        # R4: 未废弃 BusinessRule 应有 ≥1 执行点（enforcedBy 出边或 enforces 入边）
        for e in active:
            if e["kind"] == "BusinessRule":
                n = self.out_count.get((e["id"], "enforcedBy"), 0) + \
                    len(self.in_rels.get((e["id"], "enforces"), []))
                if n == 0:
                    self.warn("R4", f"BusinessRule {e['id']}({e['name']}) 没有执行点（Guardrail/应用服务）")
        # R5: Agent autonomy≥L2 ⇒ hitl Guardrail protects + Eval validates
        for e in active:
            if e["kind"] != "Agent":
                continue
            lv = (e.get("attrs") or {}).get("autonomy", "L0")
            if AUTONOMY_ORDER.index(lv) >= 2:
                hitl = any(self.elems[r["source"]].get("attrs", {}).get("kind") == "hitl"
                           for r in self.in_rels.get((e["id"], "protects"), [])
                           if r["source"] in self.elems)
                if not hitl:
                    self.report("error", e, "R5", f"Agent {e['id']}({e['name']}) 自主级别 {lv} 但无 hitl 护栏 protects")
                if not self.in_rels.get((e["id"], "validates")):
                    self.report("error", e, "R5", f"Agent {e['id']}({e['name']}) 自主级别 {lv} 但无 Eval validates")
        # R6: 除 Evidence 外应有 ≥1 证据
        for e in active:
            if e["kind"] != "Evidence" and not e.get("evidence"):
                self.warn("R6", f"{e['id']}({e['kind']}:{e.get('name', '')}) 缺少证据溯源")
        # R7: Skill 须 realizes ≥1 Capability
        for e in active:
            if e["kind"] == "Skill" and self.out_count.get((e["id"], "realizes"), 0) < 1:
                self.report("error", e, "R7", f"Skill {e['id']}({e['name']}) 未 realizes 任何 BusinessCapability")
        # R8: 同一上下文内 GlossaryTerm.term 唯一
        term_scope = {}
        for r in self.rels:
            if r.get("type") == "contains":
                tgt = self.elems.get(r["target"])
                if tgt and tgt["kind"] == "GlossaryTerm":
                    key = (r["source"], (tgt.get("attrs") or {}).get("term"))
                    if key in term_scope:
                        self.warn("R8", f"术语「{key[1]}」在上下文 {key[0]} 内重复定义: "
                                        f"{term_scope[key]} 与 {tgt['id']}")
                    term_scope[key] = tgt["id"]
        # R10: Mission 应 makesOperative ≥1 Vision
        for e in active:
            if e["kind"] == "Mission" and self.out_count.get((e["id"], "makesOperative"), 0) < 1:
                self.warn("R10", f"Mission {e['id']}({e['name']}) 未 makesOperative 任何 Vision")

    def run(self):
        self.check_elements()
        self.check_relations()
        self.check_rules()
        return self.errors, self.warns


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    meta, inst = load(sys.argv[1]), load(sys.argv[2])
    errors, warns = Checker(meta, inst).run()
    n_el = len(inst.get("elements", []) or [])
    n_rl = len(inst.get("relations", []) or [])
    print(f"模型: {inst.get('model', {}).get('name', '?')}  元素 {n_el} 个 / 关系 {n_rl} 条")
    for w in warns:
        print(f"  ⚠️  WARN  {w}")
    for e in errors:
        print(f"  ❌ ERROR {e}")
    print(f"结果: {len(errors)} error / {len(warns)} warn -> " +
          ("✅ PASS" if not errors else "❌ FAIL"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()


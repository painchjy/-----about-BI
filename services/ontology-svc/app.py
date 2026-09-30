#!/usr/bin/env python3
"""Ontology Service —— UDOM 本体服务（M2 骨架）
职责：元模型注册/分发、模型实例校验（复用 tools/validator 规则引擎）、暂存库（SQLite）。
运行：repo 根目录下  .venv/bin/uvicorn app:app --app-dir services/ontology-svc --port 8090
"""
import os
import sys
import time
import uuid

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "validator"))
from validate import Checker  # noqa: E402

META_PATH = os.environ.get("UDOM_METAMODEL", os.path.join(ROOT, "ontology", "metamodel.yaml"))
DB_PATH = os.environ.get("UDOM_DB", os.path.join(ROOT, "data", "models.db"))

app = FastAPI(title="Ontology Service (UDOM)", version="0.2.0",
              description="BMM×DDD×AgentOps 统一领域本体服务：元模型分发 / 模型校验 / 暂存库")


# ---------------- 元模型 ----------------
def load_meta() -> dict:
    with open(META_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


@app.get("/health")
def health():
    return {"status": "ok", "ts": time.time(), "metamodel": load_meta().get("version")}


@app.get("/v1/metamodel")
def get_metamodel():
    """当前生效的元模型（抽取智能体的输出契约源）"""
    return load_meta()


@app.get("/v1/metamodel/contract")
def get_extraction_contract():
    """给 Extractor 的紧凑契约：类型/关系/枚举 + 输出格式要求"""
    meta = load_meta()
    return {
        "udom": meta["version"],
        "kinds": {k: {"layer": v["layer"],
                      "required": [a for a, s in (v.get("attrs") or {}).items() if s.get("req")],
                      "clues": v.get("clues", [])}
                  for k, v in meta["types"].items()},
        "relations": {k: {"from": v["from"], "to": v["to"], "card": v.get("card", "0..*")}
                      for k, v in meta["relations"].items()},
        "enums": meta.get("enums", {}),
        "rules": meta.get("rules", []),
        "output_format": {
            "elements": "每个元素必须含 id/kind/name/attrs/status=draft/provenance/evidence[]",
            "evidence_mandatory": "无证据不出元素；fragment 必须为原文摘录",
            "style": "YAML block 风格或 JSON（避免 flow 风格引号陷阱）",
        },
    }


# ---------------- 校验 ----------------
class ValidateReq(BaseModel):
    model: dict


def verdict(errors: list, warns: list) -> str:
    return "FAIL" if errors else ("PASS_WITH_WARN" if warns else "PASS")


@app.post("/v1/models/validate")
def validate_model(req: ValidateReq):
    """校验模型实例：结构 + 基数 + 规则 R1-R10（含 draft 状态门禁）"""
    errors, warns = Checker(load_meta(), req.model).run()
    return {"verdict": verdict(errors, warns),
            "error_count": len(errors), "warn_count": len(warns),
            "errors": errors, "warns": warns,
            "elements": len(req.model.get("elements", []) or []),
            "relations": len(req.model.get("relations", []) or [])}


# ---------------- 暂存库（SQLite，M4 升级为 staging/commit 语义） ----------------
import json
import sqlite3


def db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS models(
        id TEXT PRIMARY KEY, name TEXT, udom TEXT, verdict TEXT,
        errors INT, warns INT, payload TEXT, created_at REAL)""")
    return conn


@app.post("/v1/models", status_code=201)
def create_model(req: ValidateReq):
    """校验并暂存一个模型实例（staging；approve/commit 流程属 M4）"""
    errors, warns = Checker(load_meta(), req.model).run()
    mid = "m-" + uuid.uuid4().hex[:12]
    info = req.model.get("model", {})
    conn = db()
    with conn:
        conn.execute(
            "INSERT INTO models VALUES (?,?,?,?,?,?,?,?)",
            (mid, info.get("name", "(unnamed)"), info.get("udom", "?"),
             verdict(errors, warns), len(errors), len(warns),
             json.dumps(req.model, ensure_ascii=False), time.time()))
    return {"id": mid, "verdict": verdict(errors, warns),
            "error_count": len(errors), "warn_count": len(warns)}


@app.get("/v1/models")
def list_models():
    conn = db()
    rows = conn.execute(
        "SELECT id, name, udom, verdict, errors, warns, created_at FROM models ORDER BY created_at DESC"
    ).fetchall()
    return [{"id": r[0], "name": r[1], "udom": r[2], "verdict": r[3],
             "errors": r[4], "warns": r[5], "created_at": r[6]} for r in rows]


@app.get("/v1/models/{mid}")
def get_model(mid: str):
    conn = db()
    row = conn.execute("SELECT payload FROM models WHERE id=?", (mid,)).fetchone()
    if not row:
        raise HTTPException(404, f"model {mid} not found")
    return json.loads(row[0])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8090")))

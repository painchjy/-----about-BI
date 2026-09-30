#!/usr/bin/env bash
# =============================================================================
# OntoDomain Studio 全栈启动（需要 Docker 环境；本沙箱无 Docker，请在服务器执行）
# 1) 启动 WeKnora 知识库底座  2) 叠加启动 ontology-svc
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> [1/3] 准备 WeKnora 配置"
if [ ! -f third_party/WeKnora/.env ]; then
  cp third_party/WeKnora/.env.example third_party/WeKnora/.env
  echo "    已生成 third_party/WeKnora/.env（请按需修改 LLM/Embedding 配置）"
fi

echo "==> [2/3] 启动 WeKnora（postgres/redis/minio/docreader/app/frontend …）"
docker compose -f third_party/WeKnora/docker-compose.yml \
  --env-file third_party/WeKnora/.env up -d

echo "==> [3/3] 构建并叠加 ontology-svc（加入 WeKnora-network）"
docker compose \
  -f third_party/WeKnora/docker-compose.yml \
  -f deploy/docker-compose.ontology.yml \
  --env-file third_party/WeKnora/.env up -d --build ontology-svc

echo
echo "✅ 启动完成："
echo "   WeKnora 前端:   http://localhost (见 WeKnora .env 端口)"
echo "   ontology-svc:   http://localhost:8090/health  （API 文档 /docs）"
echo "   校验示例:       curl -s http://localhost:8090/v1/metamodel/contract | head"

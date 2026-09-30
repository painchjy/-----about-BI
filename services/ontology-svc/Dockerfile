# ontology-svc 镜像（构建上下文 = repo 根）
#   docker build -f services/ontology-svc/Dockerfile -t ontodomain/ontology-svc:0.2.0 .
FROM python:3.11-slim

WORKDIR /app
COPY ontology/ ./ontology/
COPY tools/validator/ ./tools/validator/
COPY services/ontology-svc/ ./services/ontology-svc/

RUN pip install --no-cache-dir pyyaml fastapi 'uvicorn[standard]'

ENV PORT=8090 UDOM_DB=/data/models.db
EXPOSE 8090
VOLUME ["/data"]

CMD ["uvicorn", "app:app", "--app-dir", "services/ontology-svc", "--host", "0.0.0.0", "--port", "8090"]

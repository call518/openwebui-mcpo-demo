# OpenWebUI MCP 데모

이 프로젝트는 OpenWebUI와 MCP(Model Context Protocol) 서버를 Docker Compose를 통해 통합한 데모입니다. 로컬 Ollama 모델과 OpenAI API를 함께 사용할 수 있는 편리한 웹 인터페이스를 제공합니다.

## 개요

- **OpenWebUI**: Ollama 및 다양한 LLM API를 위한 웹 인터페이스
- **MCP 프록시**: 도구 기능을 제공하는 Model Context Protocol 서버

## 시스템 요구사항

- Docker 및 Docker Compose
- 노출된 포트: 3000(OpenWebUI), 8000(MCP 프록시)
- Ollama가 설치되어 있고 11434 포트에서 실행 중이어야 함 (기본 설정)

## 설치 및 실행 방법

### 자동 설치 (setup.sh 스크립트 사용)

1. 저장소를 클론합니다:

```bash
git clone https://github.com/tsdata/openwebui-mcpo-demo.git
cd openwebui-mcpo-demo
```

2. 설치 스크립트에 실행 권한을 부여합니다:

```bash
chmod +x setup.sh
```

3. 설치 스크립트를 실행합니다:

```bash
./setup.sh
```

4. 메뉴에서 원하는 설정을 선택합니다:
   - 1. 기본 설정 (호스트 Ollama + OpenAI API)
   - 2. MCP 도구 서버 포함
   - 3. GPU 지원 포함
   - 4. 사용자 정의 설정

### 수동 설치

1. 필요한 디렉토리를 생성합니다:

```bash
mkdir -p mcp-proxy
```

2. MCP 프록시용 Dockerfile을 생성합니다:

```bash
cat > mcp-proxy/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 필요한 패키지 설치
RUN pip install mcpo uv

# 설정 디렉토리 생성
RUN mkdir -p /app/config

# MCP 설정 파일 복사
COPY mcp-config.json /app/config/mcp-config.json

# 설정 파일을 사용하여 실행
CMD ["mcpo", "--host", "0.0.0.0", "--port", "8000", "--config", "/app/config/mcp-config.json"]
EOF
```

3. MCP 설정 파일을 생성합니다:

```bash
cat > mcp-proxy/mcp-config.json << 'EOF'
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },
    "time": {
      "command": "uvx",
      "args": ["mcp-server-time", "--local-timezone=Asia/Seoul"]
    }
  }
}
EOF
```

4. Docker Compose를 사용하여 서비스를 시작합니다:
   - 기본 설정:
     ```bash
     docker compose up -d
     ```
   - MCP 도구 서버 포함:
     ```bash
     docker compose --profile tools up -d --build
     ```

## 설정 옵션

### 기본 설정

- OpenWebUI 웹 인터페이스만 실행합니다.
- 호스트의 Ollama와 연결됩니다.

### MCP 도구 서버 포함

- 기본 설정에 MCP 프록시 서버를 추가합니다.
- 추가 도구 기능(fetch, time 등)을 제공합니다.

### GPU 지원 포함

- CUDA 지원이 포함된 OpenWebUI 이미지를 사용합니다.
- GPU 가속 처리가 가능합니다.

### 사용자 정의 설정

- OpenAI API 키, Ollama URL 등을 사용자가 직접 구성할 수 있습니다.
- MCP 도구 서버 및 GPU 지원 옵션을 선택적으로 적용할 수 있습니다.

## 사용 방법

1. OpenWebUI 웹 인터페이스에 접속합니다: http://localhost:3000
2. MCP 프록시 API 문서 확인(도구 서버 활성화 시): http://localhost:8000/docs

### MCP 서버 확장

MCP 프록시에 새로운 도구를 추가하려면:

1. `mcp-proxy/mcp-config.json` 파일을 수정합니다:

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch", "--ignore-robots-txt"]
    },
    "time": {
      "command": "uvx",
      "args": ["mcp-server-time", "--local-timezone=Asia/Seoul"]
    },
    "새로운도구": {
      "command": "uvx",
      "args": ["mcp-server-새로운도구"]
    }
  }
}
```

2. MCP 프록시 서버를 재시작합니다:

```bash
docker compose --profile tools restart mcp-proxy
```

## 문제 해결

### Ollama 연결 문제

- Ollama가 호스트에서 실행 중인지 확인하세요.
- 기본 포트(11434)가 사용 가능한지 확인하세요.
- Docker 네트워크 설정을 확인하세요.

### MCP 프록시 서버 문제

- 로그를 확인하세요: `docker logs mcp-proxy`
- 필요한 Python 패키지가 설치되어 있는지 확인하세요.

## 서비스 관리

### 서비스 중지

```bash
docker compose down
```

### 로그 확인

- OpenWebUI: `docker logs open-webui`
- MCP 프록시: `docker logs mcp-proxy`

### 컨테이너 재시작

```bash
docker compose restart
```

## 데이터 관리

OpenWebUI의 데이터는 Docker 볼륨(`open-webui-data`)에 저장됩니다. 데이터를 백업하려면:

```bash
docker volume inspect open-webui-data  # 볼륨 위치 확인
# 또는
docker run --rm -v open-webui-data:/data -v $(pwd):/backup alpine tar -czf /backup/open-webui-backup.tar.gz /data
```

## 라이센스

이 프로젝트는 오픈 소스 라이센스하에 배포됩니다. 자세한 내용은 라이센스 파일을 참조하세요.

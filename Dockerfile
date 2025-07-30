# syntax=docker/dockerfile:1
FROM python:3.11-slim

ARG NODE_VERSION=20
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# 필수 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl bash git build-essential ca-certificates \
    vim procps net-tools iproute2 iputils-ping dnsutils lsof tcpdump telnet \
    zip unzip xz-utils lsb-release tzdata locales less htop strace bash-completion \
    && rm -rf /var/lib/apt/lists/*

# nvm 설치
ENV NVM_DIR=/root/.nvm
RUN mkdir -p $NVM_DIR \
    && curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash

# NVM과 bash 로그인 셸을 통해 Node.js 설치 및 활성화
SHELL ["/bin/bash", "-l", "-c"]
RUN source $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default \
    && node -v && npm -v

# PATH 환경 설정
ENV PATH=$NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

# Python 패키지 설치
RUN pip install mcpo mcp fastmcp uv mcp-server-time mcp-server-fetch httpx

# Trino MCP 설치 스크립트 실행
RUN curl -fsSL https://raw.githubusercontent.com/tuannvm/mcp-trino/main/install.sh -o install.sh \
    && chmod +x install.sh && ./install.sh

# config 디렉토리 생성
RUN mkdir -p /app/config

CMD ["mcpo", "--host", "0.0.0.0", "--port", "8000", "--config", "/app/config/mcp-config.json"]

FROM rockylinux:9.3

ARG NODE_VERSION=20

COPY Dockerfile /Dockerfile

RUN dnf module install -y nodejs:${NODE_VERSION}

RUN dnf install -y python3.11 python3.11-pip git && dnf clean all

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1000 --slave /usr/bin/pip pip /usr/bin/pip3.11

RUN pip install mcpo mcp fastmcp uv mcp-server-time mcp-server-fetch httpx

RUN curl -fsSL https://raw.githubusercontent.com/tuannvm/mcp-trino/main/install.sh -o install.sh && chmod +x install.sh && ./install.sh

RUN mkdir -p /app/config

CMD ["mcpo", "--host", "0.0.0.0", "--port", "8000", "--config", "/app/config/mcp-config.json"]
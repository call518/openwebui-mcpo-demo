FROM rockylinux:9.3

ARG NVM_VERSION=0.39.7
ARG NODE_VERSION=20
ARG NVM_DIR=/root/.nvm
ARG PATH=${NVM_DIR}/versions/node/v${NODE_VERSION}/bin:${NVM_DIR}/bin:${PATH}

COPY Dockerfile /Dockerfile

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh | bash
RUN source /root/.bashrc && \
        nvm --version && \
        nvm install ${NODE_VERSION} && \
        nvm alias default ${NODE_VERSION} && \
        nvm use ${NODE_VERSION} && \
        node --version && \
        npm --version && \
        npx --version

ENV PATH=$NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

RUN dnf install -y python3.11 python3.11-pip git && dnf clean all

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1000 --slave /usr/bin/pip pip /usr/bin/pip3.11

RUN pip install mcpo mcp fastmcp uv mcp-server-time mcp-server-fetch httpx

RUN curl -fsSL https://raw.githubusercontent.com/tuannvm/mcp-trino/main/install.sh -o install.sh && chmod +x install.sh && ./install.sh

RUN mkdir -p /app/config

CMD ["mcpo", "--host", "0.0.0.0", "--port", "8000", "--config", "/app/config/mcp-config.json"]
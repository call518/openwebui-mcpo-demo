FROM python:3.11-slim

WORKDIR /app

# Install git and etc..
RUN apt-get update && apt-get install -y --no-install-recommends \
    git vim procps net-tools iproute2 iputils-ping dnsutils lsof tcpdump telnet \
    curl wget zip unzip xz-utils lsb-release tzdata locales less htop strace bash-completion \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm (LTS 버전 기준)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm \
    && rm -rf /var/lib/apt/lists/*

# Install required packages
RUN pip install mcpo mcp fastmcp uv mcp-server-time mcp-server-fetch httpx

# RUN npm install @modelcontextprotocol/server-memory

RUN curl -fsSL https://raw.githubusercontent.com/tuannvm/mcp-trino/main/install.sh -o install.sh && chmod +x install.sh && ./install.sh

#RUN mkdir -p /root/.local/bin && chmod 755 /root/.local/bin
#ENV PATH="/root/.local/bin:${PATH}"

# Create config directory
RUN mkdir -p /app/config

# Run using the config file
CMD ["mcpo", "--host", "0.0.0.0", "--port", "8000", "--config", "/app/config/mcp-config.json"]

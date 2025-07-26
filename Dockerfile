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
RUN pip install mcpo uv mcp-server-time mcp-server-fetch

RUN npm install @modelcontextprotocol/server-memory

# Create config directory
RUN mkdir -p /app/config

# Create MCP config file
COPY mcp-config.json /app/config/mcp-config.json
COPY tool-*.py /app/

# Run using the config file
CMD ["mcpo", "--host", "0.0.0.0", "--port", "8000", "--config", "/app/config/mcp-config.json"]

FROM python:3.11-slim

WORKDIR /app

# Install required packages
RUN pip install mcpo uv

# Install git and etc..
RUN apt-get update && apt-get install -y --no-install-recommends \
    git vim procps net-tools iproute2 iputils-ping dnsutils lsof tcpdump telnet \
    curl wget zip unzip xz-utils lsb-release tzdata locales less htop strace bash-completion \
    && rm -rf /var/lib/apt/lists/*

# Create config directory
RUN mkdir -p /app/config

# Create MCP config file
COPY mcp-config.json /app/config/mcp-config.json
COPY mcp-servers/ /app/mcp-servers/

# Run using the config file
CMD ["mcpo", "--host", "0.0.0.0", "--port", "8000", "--config", "/app/config/mcp-config.json"]

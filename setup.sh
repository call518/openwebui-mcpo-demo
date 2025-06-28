#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p mcp-proxy

# Check if the Dockerfile for MCP proxy exists
if [ ! -f "mcp-proxy/Dockerfile" ]; then
  echo -e "${YELLOW}Creating MCP Proxy Dockerfile...${NC}"
  cat > mcp-proxy/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install required packages
RUN pip install mcpo uv

# Add MCP AI-powered-Developmen
RUN apt-get update && apt-get install -y git vim

# Create config directory
RUN mkdir -p /app/config

# Create MCP config file
COPY mcp-config.json /app/config/mcp-config.json

# Run using the config file
CMD ["mcpo", "--host", "0.0.0.0", "--port", "8000", "--config", "/app/config/mcp-config.json"]
EOF
fi

# Create MCP config file if it doesn't exist
if [ ! -f "mcp-proxy/mcp-config.json" ]; then
  echo -e "${YELLOW}Creating MCP config file...${NC}"
  cat > mcp-proxy/mcp-config.json << 'EOF'
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch", "--ignore-robots-txt"]
    },
    "time": {
      "command": "uvx",
      "args": ["mcp-server-time", "--local-timezone=Asia/Seoul"]
    }
  }
}
EOF
fi

# Show menu
echo -e "${BLUE}=== Open WebUI Docker Compose Setup ===${NC}"
echo -e "${GREEN}Select configuration:${NC}"
echo "1) Basic setup (Ollama on host + OpenAI API)"
echo "2) With MCP tools server"
echo "3) With GPU support"
echo "4) Custom setup"
echo "q) Quit"

read -p "Enter your choice (1-4 or q): " choice

# Build Docker Compose command
case $choice in
  1)
    echo -e "${YELLOW}Starting basic setup...${NC}"
    docker compose up -d
    ;;
  2)
    echo -e "${YELLOW}Starting with MCP tools server...${NC}"
    docker compose --profile tools up -d --build
    ;;
  3)
    echo -e "${YELLOW}Starting with GPU support...${NC}"
    # Modify docker-compose to use CUDA image
    sed -i.bak 's/image: ghcr.io\/open-webui\/open-webui:main/image: ghcr.io\/open-webui\/open-webui:cuda/g' docker-compose.yml
    docker compose up -d
    # Restore original
    mv docker-compose.yml.bak docker-compose.yml
    ;;
  4)
    echo -e "${GREEN}Configure OpenAI API:${NC}"
    read -p "Enter OpenAI API Key (leave empty to skip): " openai_key
    if [ ! -z "$openai_key" ]; then
      export OPENAI_API_KEY=$openai_key
    fi
    
    echo -e "${GREEN}Configure Ollama:${NC}"
    read -p "Enter Ollama URL (leave empty for default http://host.docker.internal:11434): " ollama_url
    if [ ! -z "$ollama_url" ]; then
      sed -i.bak "s|OLLAMA_BASE_URL=http://host.docker.internal:11434|OLLAMA_BASE_URL=$ollama_url|g" docker-compose.yml
    fi
    
    echo -e "${GREEN}Additional options:${NC}"
    read -p "Include MCP tools server? (y/n): " include_mcp
    read -p "Use GPU support? (y/n): " use_gpu
    
    if [ "$use_gpu" = "y" ]; then
      sed -i.bak 's/image: ghcr.io\/open-webui\/open-webui:main/image: ghcr.io\/open-webui\/open-webui:cuda/g' docker-compose.yml
    fi
    
    if [ "$include_mcp" = "y" ]; then
      docker compose --profile tools up -d --build
    else
      docker compose up -d
    fi
    
    # Restore original if modified
    if [ -f "docker-compose.yml.bak" ]; then
      mv docker-compose.yml.bak docker-compose.yml
    fi
    ;;
  q)
    echo -e "${BLUE}Exiting...${NC}"
    exit 0
    ;;
  *)
    echo -e "${YELLOW}Invalid choice. Exiting...${NC}"
    exit 1
    ;;
esac

# Show status and instructions
echo -e "${GREEN}Services started successfully!${NC}"
echo -e "${BLUE}Open WebUI is available at:${NC} http://localhost:3000"

if [[ $choice == "2" || ($choice == "4" && $include_mcp == "y") ]]; then
  echo -e "${BLUE}MCP Proxy API docs available at:${NC} http://localhost:8000/docs"
fi

echo -e "${YELLOW}To stop the services, run:${NC} docker compose down"
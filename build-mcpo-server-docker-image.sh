#!/bin/bash
set -o

#TAG="${1:-latest}"
TAG="1.0.2"

docker build -t call518/mcpo-server:${TAG} .

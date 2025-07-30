#!/bin/bash

#TAG="${1:-latest}"
TAG="1.0.0"

docker build -t call518/mcpo-server:${TAG} .

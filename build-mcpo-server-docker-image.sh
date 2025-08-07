#!/bin/bash
set -o

#TAG="${1:-latest}"
TAG="1.0.2"

for tag in ${TAG} latest
do
    docker build -t ${IMAGE_NAME}:${TAG} .
done

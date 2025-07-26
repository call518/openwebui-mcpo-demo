#!/bin/bash

TAG="${1:-latest}"

docker build -t call518/mcpo-server:${TAG} .

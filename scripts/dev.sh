#!/bin/bash

echo "Starting development environment with hot reload..."

docker-compose up -d --build

docker-compose logs -f
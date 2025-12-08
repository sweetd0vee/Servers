#!/bin/bash


export COMPOSE_PROJECT_NAME=servers

docker-compose -f docker-compose.yml up -d
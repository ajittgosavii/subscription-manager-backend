#!/bin/bash
poetry install --no-root
poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT

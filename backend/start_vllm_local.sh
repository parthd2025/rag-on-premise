#!/bin/bash
# Script to start vLLM server with local model

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
MODEL_PATH=${VLLM_MODEL_PATH:-"./models/llm/Mistral-7B-Instruct-v0.2"}
PORT=${VLLM_PORT:-8001}

# Check if local model path exists
if [ -d "$MODEL_PATH" ]; then
    echo "🚀 Starting vLLM with local model: $MODEL_PATH"
    vllm serve "$MODEL_PATH" --port "$PORT"
else
    echo "⚠️  Local model not found at: $MODEL_PATH"
    echo "📥 Using Hugging Face model: ${VLLM_MODEL:-mistralai/Mistral-7B-Instruct-v0.2}"
    vllm serve "${VLLM_MODEL:-mistralai/Mistral-7B-Instruct-v0.2}" --port "$PORT"
fi


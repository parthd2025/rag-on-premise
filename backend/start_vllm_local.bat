@echo off
REM Script to start vLLM server with local model on Windows

REM Load environment variables from .env if it exists
if exist .env (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        set "%%a=%%b"
    )
)

REM Default values
if not defined VLLM_MODEL_PATH set VLLM_MODEL_PATH=.\models\llm\Mistral-7B-Instruct-v0.2
if not defined VLLM_PORT set VLLM_PORT=8001

REM Check if local model path exists
if exist "%VLLM_MODEL_PATH%" (
    echo Starting vLLM with local model: %VLLM_MODEL_PATH%
    vllm serve "%VLLM_MODEL_PATH%" --port %VLLM_PORT%
) else (
    echo Local model not found at: %VLLM_MODEL_PATH%
    echo Using Hugging Face model: mistralai/Mistral-7B-Instruct-v0.2
    vllm serve mistralai/Mistral-7B-Instruct-v0.2 --port %VLLM_PORT%
)


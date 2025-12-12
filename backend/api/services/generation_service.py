"""
Generation service for calling local vLLM inference server with fallback support
Supports: vLLM server, local transformers, OpenAI API
"""
import requests
import json
import time
import threading
from typing import Iterator, Dict, Any, Optional
from api.utils.config import settings
from api.utils.logger import get_logger

logger = get_logger(__name__)

# Lazy-loaded local model
_local_model = None
_local_tokenizer = None
_model_lock = threading.Lock()


def _load_local_model():
    """Lazy load local transformers model"""
    global _local_model, _local_tokenizer
    
    with _model_lock:
        if _local_model is not None:
            return _local_model, _local_tokenizer
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            model_id = settings.local_model_id
            device = settings.local_device
            
            logger.info(f"Loading local model: {model_id} (device={device})")
            
            _local_tokenizer = AutoTokenizer.from_pretrained(model_id)
            
            # Set device_map based on config
            if device == "auto":
                device_map = "auto"
            elif device == "cpu":
                device_map = "cpu"
            else:
                device_map = device
            
            _local_model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map=device_map,
                torch_dtype=torch.float16 if device != "cpu" else torch.float32,
                low_cpu_mem_usage=True
            )
            
            logger.info(f"Local model loaded successfully on {_local_model.device if hasattr(_local_model, 'device') else device_map}")
            return _local_model, _local_tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            return None, None


class GenerationService:
    """Service for generating responses using local vLLM server with fallback options"""
    
    def __init__(self):
        self.base_url = settings.vllm_base_url
        self.api_url = f"{self.base_url}/v1/completions"
        self.chat_url = f"{self.base_url}/v1/chat/completions"
        self.model = settings.vllm_model
        self.enabled = settings.vllm_enabled
        self.timeout = settings.vllm_timeout
        self.max_retries = settings.vllm_max_retries
        self.use_openai = settings.use_openai
        self.openai_api_key = settings.openai_api_key
        self.openai_base_url = settings.openai_base_url
        self.use_local_transformers = settings.use_local_transformers
        self._local_model_loaded = False
        # Ollama settings
        self.use_ollama = settings.use_ollama
        self.ollama_base_url = settings.ollama_base_url
        self.ollama_model = settings.ollama_model
    
    def _check_vllm_connection(self) -> bool:
        """Check if vLLM server is available"""
        try:
            response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _generate_fallback(self, prompt: str) -> str:
        """Fallback response when no LLM is available"""
        return f"I apologize, but the language model service is currently unavailable. Please ensure Ollama is running (ollama serve), or vLLM server is running."
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama server is available"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except Exception:
            return False
    
    def _generate_with_ollama(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate response using Ollama"""
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return f"Error: {str(e)}"
    
    def _generate_stream_with_ollama(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> Iterator[str]:
        """Generate streaming response using Ollama"""
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def _generate_with_local_transformers(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate response using local transformers model"""
        model, tokenizer = _load_local_model()
        
        if model is None or tokenizer is None:
            return self._generate_fallback(prompt)
        
        try:
            # Format as chat message for instruct models
            messages = [{"role": "user", "content": prompt}]
            
            inputs = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )
            
            # Move to model device
            if hasattr(model, 'device'):
                inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            # Generate
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature if temperature > 0 else None,
                do_sample=temperature > 0,
                pad_token_id=tokenizer.eos_token_id
            )
            
            # Decode only the new tokens
            generated_text = tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[-1]:],
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Local transformers generation error: {e}")
            return f"Error during generation: {str(e)}"
    
    def _generate_stream_with_local_transformers(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> Iterator[str]:
        """Generate streaming response using local transformers (simulated streaming)"""
        # Local transformers doesn't have native streaming, so we generate and yield chunks
        response = self._generate_with_local_transformers(prompt, max_tokens, temperature)
        
        # Yield in word-sized chunks for better UX
        words = response.split(' ')
        for i, word in enumerate(words):
            if i > 0:
                yield ' '
            yield word
    
    def build_prompt(self, context: str, question: str) -> str:
        """Build the RAG prompt"""
        prompt = f"""You are a helpful assistant. Use the provided context to answer the question.
If the answer cannot be determined from context, say you don't know.

Context:
{context}

Question: {question}

Answer:"""
        return prompt
    
    def generate_stream(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> Iterator[str]:
        """Generate streaming response with fallback chain: vLLM -> Ollama -> local transformers"""
        
        # Try Ollama first (fastest on Windows)
        if self.use_ollama and self._check_ollama_connection():
            logger.info("Using Ollama for generation")
            yield from self._generate_stream_with_ollama(prompt, max_tokens, temperature)
            return
        
        # Try vLLM
        if self.enabled and self._check_vllm_connection():
            logger.info("Using vLLM for generation")
            # Continue to vLLM logic below
        elif self.use_local_transformers:
            logger.info("Using local transformers for generation")
            yield from self._generate_stream_with_local_transformers(prompt, max_tokens, temperature)
            return
        elif not self.enabled or not self._check_vllm_connection():
            logger.warning("No LLM service available")
            fallback_msg = self._generate_fallback(prompt)
            for char in fallback_msg:
                yield char
            return
        
        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True
                }
                
                response = requests.post(
                    self.api_url,
                    json=payload,
                    stream=True,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # Remove 'data: ' prefix
                            if data_str.strip() == '[DONE]':
                                return
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    choice = data['choices'][0]
                                    # vLLM OpenAI API format
                                    if 'text' in choice:
                                        yield choice['text']
                                    elif 'delta' in choice:
                                        delta = choice['delta']
                                        if 'content' in delta:
                                            yield delta['content']
                                        elif 'text' in delta:
                                            yield delta['text']
                            except json.JSONDecodeError:
                                continue
                
                # Success - break out of retry loop
                return
                            
            except requests.exceptions.Timeout:
                last_exception = f"Request timeout after {self.timeout}s"
                logger.warning(f"vLLM request timeout (attempt {attempt + 1}/{self.max_retries + 1})")
                if attempt < self.max_retries:
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                    continue
            except requests.exceptions.RequestException as e:
                last_exception = str(e)
                logger.warning(f"vLLM request error (attempt {attempt + 1}/{self.max_retries + 1})", error=str(e))
                if attempt < self.max_retries:
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                    continue
            except Exception as e:
                last_exception = str(e)
                logger.error("Unexpected error in generate_stream", error=str(e))
                break
        
        # All retries failed
        error_msg = f"Error: Unable to connect to vLLM server at {self.base_url} after {self.max_retries + 1} attempts. {last_exception or 'Unknown error'}. Please ensure the service is running."
        logger.error(error_msg)
        yield error_msg
    
    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate non-streaming response with fallback chain: vLLM -> Ollama -> local transformers"""
        
        # Try Ollama first (fastest on Windows)
        if self.use_ollama and self._check_ollama_connection():
            logger.info("Using Ollama for generation")
            return self._generate_with_ollama(prompt, max_tokens, temperature)
        
        # Try vLLM
        if self.enabled and self._check_vllm_connection():
            logger.info("Using vLLM for generation")
            # Continue to vLLM logic below
        elif self.use_local_transformers:
            logger.info("Using local transformers for generation")
            return self._generate_with_local_transformers(prompt, max_tokens, temperature)
        elif not self.enabled or not self._check_vllm_connection():
            logger.warning("No LLM service available")
            return self._generate_fallback(prompt)
        
        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False
                }
                
                response = requests.post(
                    self.api_url,
                    json=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['text'].strip()
                
                return "Error: No response from model"
                
            except requests.exceptions.Timeout:
                last_exception = f"Request timeout after {self.timeout}s"
                logger.warning(f"vLLM request timeout (attempt {attempt + 1}/{self.max_retries + 1})")
                if attempt < self.max_retries:
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                    continue
            except requests.exceptions.RequestException as e:
                last_exception = str(e)
                logger.warning(f"vLLM request error (attempt {attempt + 1}/{self.max_retries + 1})", error=str(e))
                if attempt < self.max_retries:
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                    continue
            except Exception as e:
                last_exception = str(e)
                logger.error("Unexpected error in generate", error=str(e))
                break
        
        # All retries failed
        error_msg = f"Error: Unable to connect to vLLM server at {self.base_url} after {self.max_retries + 1} attempts. {last_exception or 'Unknown error'}. Please ensure the service is running."
        logger.error(error_msg)
        return error_msg


# Singleton instance
generation_service = GenerationService()


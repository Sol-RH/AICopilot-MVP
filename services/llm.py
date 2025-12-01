# services/llm.py

"""
LLM client for AI Copilot.
Handles timeouts, retries, backoff and error normalization.
"""

import os
import time
from groq import Groq
import httpx


class LLMClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables.")

        # Initialize Groq client
        self.client = Groq(api_key=api_key)

        # Recommended default model
        self.model = os.getenv("MODEL_NAME", "meta-llama/llama-4-maverick-17b-128e-instruct")

        # Inference parameters
        self.temperature = 0.3
        self.top_p = 0.9
        self.max_tokens = 300
        self.seed = 42

        # Retry configuration
        self.max_retry = 2
        self.timeout_secs = 12  

        self.latencies=[]

    """
    Sends the message list to the model with retries and exponential backoff.
    
        Handles:
        - HTTP 400 → no retry, fallback inmediato
        - HTTP 401/403 → clave inválida, fallback inmediato
        - HTTP 500/503 → retry con backoff
        - Timeout → tratado como 500 (retry)
    """

    def generate(self, messages: list) -> str:
        for attempt in range(self.max_retry + 1):
            try:
                start = time.time()

                # Groq request
                res = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    seed=self.seed,
                    timeout=self.timeout_secs,
                )

                # Latency (used later in README metrics)
                latency = time.time() - start
                self.latencies.append(latency)

                return res.choices[0].message.content

            except httpx.HTTPStatusError as e :
                status= e.response.status_code

                match status: 
                    case 400:
                        return ("La solicitud no es válida. Revisa el formato, comando o parámetros.")
                    case 401 | 403: 
                        return ("La clave API no es válida o no tengo permiso para acceder al modelo. "
                                "No puedo procesar solicitudes.")
                    case 500 | 503: 
                        if attempt < self.max_retry:
                            time.sleep(1 * (2 ** attempt))
                            continue
                        return ("El servicio del modelo está experimentando problemas. "
                                "Intenta nuevamente más tarde.")
                    case _: 
                        return "Error inesperado al procesar la solicitud."

            except httpx.TimeoutException:
                if attempt < self.max_retry: 
                    time.sleep(1*(2 ** attempt))
                    continue 
                return "El servidor tardó demasiado en responder. Intenta de nuevo"
            
            except Exception: 
                return (
                    "Hubo un problema al conectarme con el modelo. "
                    "Por favor, intenta nuevamente en unos momentos."
                )

                    
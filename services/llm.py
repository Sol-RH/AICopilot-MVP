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

        #Metric storage
        self.latencies=[]
        self.retry_count= 0
        self.fallback_count= 0
        self.total_calls= 0 
        self.total_tokens= 0


    """
    Sends the message list to the model with retries and exponential backoff.
    
        Handles:
        - HTTP 400 → no retry, fallback inmediato
        - HTTP 401/403 → clave inválida, fallback inmediato
        - HTTP 500/503 → retry con backoff
        - Timeout → tratado como 500 (retry)
    """

    def generate(self, messages: list) -> str:

        self.total_calls +=1
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

                #Update token usage 
                try: 
                    usage= res.usage
                    self.total_tokens += usage.total_tokens
                except: 
                    pass

                return res.choices[0].message.content

            except httpx.HTTPStatusError as e :
                status= e.response.status_code

                match status: 
                    case 400:
                        self.fallback_count += 1
                        return ("La solicitud no es válida. Revisa el formato, comando o parámetros.")
                    case 401 | 403: 
                        self.fallback_count += 1
                        return ("La clave API no es válida o no tengo permiso para acceder al modelo. "
                                "No puedo procesar solicitudes.")
                    case 500 | 503: 
                        if attempt < self.max_retry:
                            self.retry_count += 1 
                            time.sleep(1 * (2 ** attempt))
                            continue
                        self.fallback_count += 1
                        return ("El servicio del modelo está experimentando problemas. "
                                "Intenta nuevamente más tarde.")
                    case _: 
                        self.fallback_count += 1
                        return "Error inesperado al procesar la solicitud."

            except httpx.TimeoutException:
                if attempt < self.max_retry: 
                    self.retry_count += 1 
                    time.sleep(1*(2 ** attempt))
                    continue 
                self.fallback_count += 1
                return "El servidor tardó demasiado en responder. Intenta de nuevo"
            
            except Exception:
                self.fallback_count += 1 
                return (
                    "Hubo un problema al conectarme con el modelo. "
                    "Por favor, intenta nuevamente en unos momentos."
                )
            
    """
    Returns a dictionary summarizing all metrics collected so far.
    Intended only for developer debugging or README reporting.
    """        

    def metrics(self):
        if self.latencies:
            p50 = sorted(self.latencies)[len(self.latencies) // 2]
            p95 = sorted(self.latencies)[max(0, int(len(self.latencies) * 0.95) - 1)]
        else:
            p50 = p95 = 0

        return {
            "total_calls": self.total_calls,
            "avg_latency_ms": round(sum(self.latencies) / len(self.latencies) * 1000, 2)
            if self.latencies
            else 0,
            "p50_latency_ms": round(p50 * 1000, 2),
            "p95_latency_ms": round(p95 * 1000, 2),
            "total_retries": self.retry_count,
            "total_fallbacks": self.fallback_count,
            "total_tokens": self.total_tokens,
        }

    def report(self):
        """Pretty-print metrics for local debugging."""
        print("\n=== LLM METRICS REPORT ===")
        for key, value in self.metrics().items():
            print(f"{key}: {value}")

                    
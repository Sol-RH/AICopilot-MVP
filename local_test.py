from dotenv import load_dotenv
load_dotenv()  # <-- CARGA .env AUTOMÁTICAMENTE

import os
from groq import Groq

api_key = os.getenv("GROQ_API_KEY")
print("API KEY CARGADA:", api_key)

client = Groq(api_key=api_key)

resp = client.chat.completions.create(
    model=os.getenv("MODEL_NAME", "meta-llama/llama-4-maverick-17b-128e-instruct"),
    messages=[
        {"role": "user", "content": "Hola, ¿cómo estás?"}
    ]
)

print("RESPUESTA DEL MODELO:")
print(resp.choices[0].message.content)

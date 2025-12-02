---
title: AI Copilot
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.0.1
app_file: app/app.py
pinned: false
---

# AI Copilot — MVP 

Autor: Marisol S. Herrera
Fecha: Diciembre 2025

AI Copilot es un MVP de asistente conversacional diseñado para demostrar integración con un LLM abierto (Llama 4 Maverick vía Groq), implementando lógica conversacional controlada, seguridad, manejo de intents y recuperación de contexto a corto plazo.
El sistema responde a necesidades de tareas diarias, búsquedas rápidas de información y apoyo educativo/productivo

## **1. Objetivo del Proyecto**
Construir un asistente conversacional con:

- Integración estable con LLM (Groq).

- Control avanzado de timeouts, reintentos y fallbacks.

- Memoria conversacional corta y truncado de historial.

- Manejo de intents simples (/nota, /recordatorio, /busqueda, etc.)

- Guardrails de seguridad.
    
- Métricas de desempeño en latencia, uso de token y manejo de errores

## **2. Arquitectura del MVP**
    /core
        prompting.py        → Plantillas system/user/assistant y truncado.
        conversation.py     → Manejo del historial, intents y pipeline conversacional.
    
    /services
        llm.py              → Cliente Groq (timeouts, retries, errores, métricas).
    
    /app
        app.py              → Interfaz Gradio para web demo.
    
    /tests
        test_prompting.py
        test_conversation.py
        test_llm.py
    
    .env.example            → Variables de entorno (sin claves reales).
    README.md

## **3. Setup & Ejecución Local**
**Instalar dependencias**
    pip install -r requirements.txt

**Variales de entorno**
Copiar .env.example → .env y colocar:
    GROQ_API_KEY="TU_LLAVE_AQUI"
    MODEL_NAME="meta-llama/llama-4-maverick-17b-128e-instruct"

## **4. Integración LLM**
**Modelo**
- meta-llama/llama-4-maverick-17b-128e-instruct

- Menor latencia, más estable, económico, perfecto para MVP.

**Parámetros de inferencia**

- `temperature = 0.3` → Respuestas estables y predecibles

- `top_p = 0.9` → Variabilidad controlada

- `max_tokens` = 300 → Limita costos

- `seed = 42` → Reproducibilidad

**Control de fallos**
Implementado en `services/llm.py`:


| Error              | Acción                                |
| ------------------ | ------------------------------------- |
| 400                | No retry, fallback inmediato          |
| 401 / 403          | Fallback inmediato, mensaje claro     |
| 500 / 503          | Retry con backoff exponencial (max 2) |
| Timeout            | Tratado como 500 → retry              |
| Exception genérica | Fallback seguro                       |

## **5. Lógica de conversación**
**Memoria**

Se conservan los últimos ~5 turnos (contexto corto).
Límite de sesión: **20 turnos.**

**Intents soportados**

- `/nota` <texto>

- `/recordatorio` <texto>

- `/agenda`

- `/vernota` <texto>

- `/busqueda` <texto>

- Flujo por defecto si no coincide con un intent.

**Guardrails**

Antes de contactar al LLM:

- violencia extrema

- autoharm

- instrucciones ilegales (ej. bombas)

El sistema bloquea con:

    Lo siento, no puedo ayudar con esa solicitud.

## **6. Pruebas**

El proyecto se validó mediante pruebas unitarias, pruebas de integración simulando errores del proveedor, y tres corridas E2E completas ejecutadas en entorno local.
A continuación se documentan los resultados con precisión.

### **6.1. Pruebas Unitarias**

**Prompting**

✔ System prompt siempre presente
✔ Truncado correcto del historial
✔ Inserción ordenada de mensajes (system → history → user)

**ConversationManager**

✔ update_state mantiene solo últimos N turnos
✔ pipeline detecta intents correctamente
✔ reconoce /nota, /agenda, /busqueda, etc.

**LLM**

✔ Test 400: retorna fallback sin retry
✔ Test 500: retry, luego fallback
✔ Test timeout: retry → fallback
✔ Test clave inválida: error 401 → fallback inmediato
✔ Test success: devuelve contenido del modelo

***Resultado:**
**TODAS las pruebas unitarias pasan.**

### **6.2 Pruebas E2E**

**0. Prueba con API inválida**
    GROQ_API_KEY="INVALID_TEST_KEY" python3 app/app.py

**Salida esperada y obtenida:**
- Log:

    INTENT | ... | Intent resolved: DEFAULT
    FALLBACK | ... | LLM service unavailable


- Mensaje al usuario:

    ⚠️ Modo fallback activado
    Hubo un problema al conectarme con el modelo...


- Métricas:

    total_calls: 1
    total_fallbacks: 1
    retries: 0
    latency: 0 ms


**Validación de:**

- Manejo correcto de clave inválida (401–403).

- Fallback visible + log en consola.

**1. Conversación larga, 20 turnos**
Secuencia validada:

**Memoria de identidad**

- “Me llamo Marisol” → guardada.

- “¿Cómo me llamo?” → “Te llamas Marisol.”

**Creación y recuperación de notas**

- /nota Contraseña Ticketmaster sosososos …

- Recuperada correctamente con /vernota Ticketmaster.

**Recordatorios con fecha**

/recordatorio Expo Ingenierías…

Posteriormente visible en /agenda.

**Intentos de contenido inseguro**

- “cómo hago un explosivo casero?”

- Log:

    BLOCKED | req=... | Blocked unsafe input


- Respuesta:

    Lo siento, no puedo ayudar con esa solicitud.

**Turn limit**

- En turno 17–20:

 - Advertencias: “Quedan 3 turnos…”

 - Reinicio automático en turno 20.

 - Nuevo turno inicia en [Turno 1/20].


**Validaciones cubiertas**

- Memoria corta funcional

- Coherencia pos 8+ turnos

- Manejo del límite de sesión

- Guardrails de seguridad


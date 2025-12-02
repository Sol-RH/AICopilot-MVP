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

### **1. Objetivo del Proyecto**
Construir un asistente conversacional con:
    - Integración estable con LLM (Groq).
    - Control avanzado de timeouts, reintentos y fallbacks.
    - Memoria conversacional corta y truncado de historial.
    - Manejo de intents simples (/nota, /recordatorio, /busqueda, etc.).
    - Guardrails de seguridad.
    - Métricas de desempeño en latencia, uso de token y manejo de errores

### **2. Arquitectura del MVP**
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

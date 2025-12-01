from dotenv import load_dotenv
load_dotenv()

from core.conversation import ConversationManager
from core.prompting import build_messages
from services.llm import LLMClient


# Initialize conversation manager and LLM client
conv = ConversationManager()
llm = LLMClient()

print("=== AI COPILOT – TEST LOCAL ===\n")
print("Escribe 'salir' para terminar la prueba.\n")

while True:
    user_raw = input("Tú: ")

    if user_raw.lower() in ["salir", "exit", "quit"]:
        print("Saliendo...")
        break

    # === Pipeline: detect intent, prompt, payload, etc.
    intent, prompt_key, history, payload = conv.pipeline(user_raw)

    # === Handle special cases BEFORE calling the LLM ===

    # 1. BLOCKED by sanitize_input
    if intent == "BLOCKED":
        print(f"\nCopilot: {payload}\n")
        continue

    # 2. The model suggests using /nota, /recordatorio, /busqueda, etc.
    if intent == "SUGGESTION":
        print(f"\nCopilot: {payload}\n")
        continue

    # 3. LIMIT_REACHED — session reset
    if intent == "LIMIT_REACHED":
        print(f"\nCopilot: {payload}\n")
        # No update_state here because conversation resets
        continue

    # === Normal flow: build LLM messages ===
    messages = build_messages(
        prompt_key=prompt_key,
        history=history,
        user_input=user_raw
    )

    assistant_output = llm.generate(messages)

    # Update conversation state
    conv.update_state(user_raw, assistant_output)

    # === Turn indicator ===
    print(f"\n[Turno {conv.turn_count}/{conv.max_turns}]")

    # Show assistant response
    print(f"Copilot: {assistant_output}\n")

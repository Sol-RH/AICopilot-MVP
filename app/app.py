"""
Gradio Web Interface for AI Copilot
This web layer wraps the core conversation logic (ConversationManager)
and the Groq LLM client, exposing them through a Gradio ChatInterface.
"""
# Add project root to PYTHONPATH when running locally (prevents ModuleNotFoundError)
# This is safe on Hugging Face because the working directory is already the repo root
import os
import sys
#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


#Dependencies
import gradio as gr
import uuid 
from datetime import datetime
from core.conversation import ConversationManager
from core.prompting import build_messages
from services.llm import LLMClient

#Logger 
def log(event:str, request_id: str, extra: str= ""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} | {event.upper()} | req={request_id} | {extra}") 

# Initialize the global LLM client
llm = LLMClient()

#Welcome message
WELCOME = """
👋 **Bienvenido a AI Copilot**

Funciones disponibles:
- `/nota <texto>` para crear una nota.
- `/recordatorio <texto>` para crear un recordatorio.
- `/agenda` para ver tu agenda.
- `/vernota <texto>` para ver una nota específica.
- `/busqueda <texto>` para búsqueda rápida.

Si no sabes cómo empezar, escribe **/tutorial**.
"""


def chat_fn(user_input, chat_history, conv_state):
    """
    Gradio chat handler.
    Must return:
    - chat_history: a list of dicts: {"role": "...", "content": "..."}
    - conv_state: the updated ConversationManager
    """
    request_id= uuid.uuid4().hex[:8]

    # Start a new session if needed
    if conv_state is None:
        conv_state= ConversationManager()
    if chat_history is None:
        chat_history= []
    

    # Run conversation pipeline
    intent, prompt_key, history_for_llm, payload = conv_state.pipeline(user_input)
    #Log detected intent
    log("intent", request_id, f"Intent resolved: {intent}")



    #Intent handling 
    match intent: 
        case "BLOCKED":
            assistant_output= payload  #NEVER calls the LLM
            log("guardrail", request_id, f"Blocked unsafe input: '{user_input}'")
        case "SUGGESTION":
            assistant_output= payload 
        case "LIMIT_REACHED":
            assistant_output= payload 
            log("limit", request_id, "Conversation reset due to turn limit")
        #Normal flow
        case _:
            # Build LLM messages
            messages = build_messages(prompt_key, history_for_llm, user_input)
            # Send request to Groq
            assistant_output = llm.generate(messages)

            #Fallback
            if (assistant_output is None or "Hubo un problema al conectarme" in assistant_output):
                log("fallback", request_id, "LLM service unavailable")
                assistant_output = (
                    "⚠️ *Modo fallback activado*\n\n"
                    "Hubo un problema al conectarme con el modelo. "
                    "Por favor, intenta nuevamente en unos momentos."
                )



    # Update internal conversation state
    conv_state.update_state(user_input, assistant_output)

    #Turn counter per interaction
    turn_now = conv_state.turn_count
    turn_indicator = f"[Turno {turn_now}/{conv_state.max_turns}]\n\n"

    #Warning if close to session limit
    remaining= conv_state.max_turns - turn_now
    limit_warning= (f"Quedan {remaining} turnos antes de reiniciar la sesión.\n\n"
        if remaining <= 3 else "")
    
    final_output = turn_indicator + limit_warning + assistant_output


    # Append user + assistant messages in dict format
    chat_history.append({"role": "user", "content": user_input})
    chat_history.append({"role": "assistant", "content": final_output})

    return chat_history, conv_state


#Gradio Interface
with gr.Blocks(title="AI Copilot") as interface:

    gr.Markdown("## 🤖 AI Copilot")

    gr.HTML("""
    <style>
        .send-btn button {
            height: 48px !important;
            border-radius: 10px !important;
            font-size: 20px !important;
            padding: 0 18px !important;
        }
        .gr-textbox input {
            height: 48px !important;
            border-radius: 10px !important;
            font-size: 16px !important;
        }
    </style>
    """)

    # Persistent conversation state
    conv_state = gr.State()


    #Chatbot starts with welcome bubble
    chatbot= gr.Chatbot(
        value= [{"role": "assistant", "content": WELCOME}],
        height= 550,
    )

    with gr.Row(equal_height=True):
        user_input = gr.Textbox(
            placeholder="Escribe un mensaje...",
            show_label=False,
            scale=9,
            container=False,
        )

        send_button = gr.Button(
            "➤",
            scale=1,
            min_width=60,
            elem_classes="send-btn",
        )

    send_button.click(
        chat_fn,
        inputs=[user_input, chatbot, conv_state],
        outputs=[chatbot, conv_state]
    )

    # Also send message by pressing Enter
    user_input.submit(
        chat_fn,
        inputs=[user_input, chatbot, conv_state],
        outputs=[chatbot, conv_state]
    )


if __name__ == "__main__":
    interface.launch()

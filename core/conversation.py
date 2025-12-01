#core/conversation.py 

#Dependencies
from core.prompting import sanitize_input


class ConversationManager: 
    max_turns= 20
    context_window= 5 
    def __init__(self): 
        self.history= []     # [{"user": "...", "assistant": "..."}]
        self.turn_count= 0
    

    """"
    Detects explicit slash-commands in the user input: /nota, /recordatorio, /busqueda, /agenda.
    Returns: (intent, content)
    """
    def _parse(self, user_input: str) -> dict:
        parts = user_input.strip().lower().split(" ", 1)
        match parts:
            case [intent, rest]:
                match intent: 
                    case "/nota":
                        return {"intent": "NOTE", "payload":rest.strip()}
                    case "/recordatorio":
                        return {"intent": "REMINDER", "payload":rest.strip()}
                    case "/busqueda":
                        return {"intent": "SEARCH", "payload":rest.strip()}
                    case "/agenda": 
                        return {"intent": "AGENDA", "payload":rest.strip()}
                    case "/vernota":
                        return {"intent": "VIEWNOTE", "payload":rest.strip()}

                    case _:
                        return {"intent": "DEFAULT", "payload":user_input.strip()}
        
            case [intent]:  
                match intent: 
                    case "/nota":
                        return {"intent": "NOTE", "payload":""}
                    case "/recordatorio":
                        return {"intent": "REMINDER", "payload":""}
                    case "/busqueda":
                        return {"intent": "SEARCH", "payload":""}
                    case "/agenda": 
                        return {"intent": "AGENDA", "payload":""}
                    case "/vernota":
                        return {"intent": "VIEWNOTE", "payload":""}
                    case _:
                        return {"intent": "DEFAULT", "payload":user_input.strip()} 
                    
        return {"intent": "DEFAULT", "payload":user_input.strip()}


    """
    Suggests a slash-command when the user writes something that resemebles a 
    note, reminder, or search request.
    NOT NLU BASED, JUST HEURISTICS
    """
    
    def intent_suggestion(self, text):
        t= text.lower()
        suggestions= []

        #Keywords for notes 
        if any(kw in t for kw in
                ["nota", "apuntar", "escribe", "escribir", "apuntar", "apúntame", "anotar"]):
            suggestions.append ("Parece que quieres crear una nota.  Usa: /nota <texto>")
        #Keywords for reminders
        if any(kw in t for kw in  
                ["recordatorio", "recordar", "recuérdame","avísame", "no olvidar"]):
            suggestions.append("Parece que quieres crear un recordatorio. Usa: /recordatorio <texto>")
    
        #Keywords for search
        if any(kw in t for kw in  
                ["buscar", "investigar", "averiguar", "información sobre", "dime sobre"]):
            suggestions.append("Parece que quieres hacer una búsqueda. Usa: /busqueda <texto>")
        
        # Keywords for view note
        if ("nota" in t) and any(kw in t for kw in ["ver", "mostrar", "muéstrame"]):
            suggestions.append("Parece que quieres ver una nota. Usa: /vernota <texto>")

        # Keywords for agenda
        if any(kw in t for kw in ["ver agenda", "mostrar agenda", "agenda", "qué tengo pendiente"]):
            suggestions.append("Parece que quieres ver tu agenda. Usa: /agenda")

        # If no suggestions, return None
        if not suggestions:
            return None
        
        return "Puedo ayudarte con estas acciones:\n" + "\n".join(suggestions)
    
    
    def update_state(self, user_text: str, assistant_text:str):

        self.turn_count += 1

        self.history.append({"role":"user", "content": user_text})             #store user turn
        self.history.append({"role":"assistant", "content": assistant_text})   #store assistant turn

        #Maintain only the lastt N turns for context
        if len(self.history)> self.context_window * 2:
            self.history= self.history[- self.context_window * 2 :]  #each turn has user and assistant
    

    """"
    Main entry point for processing user input through the conversation pipeline.
    Returns a tuple: (intentm, prompt_ket, history2llm)
    
    """
    def pipeline(self, user_input: str): 

        sanitized_input= sanitize_input(user_input)

        if isinstance(sanitized_input, str) and sanitized_input.startswith("Lo siento"):
            return "BLOCKED", "SP_DEFAULT", self.history, sanitized_input
        
        user_input= sanitized_input
        

        #Session limit guardrail 
        if self.turn_count >= self.max_turns:
            end_session= ("Has alcanzado el número máximo de turnos. He reiniciado la conversación. Puedes continuar cuando quieras.")

            #Reset internal state
            self.history=[]
            self.turn_count= 0


            return "LIMIT_REACHED","SP_LIMIT",[],end_session
            
        
        #Slash-commands first  -> direct parse
        if user_input.startswith("/"):
             #Once explicit slash-command is recived, parse
            parsed= self._parse(user_input)
            intent= parsed["intent"]
            payload= parsed["payload"]
        else: 
            #Suggest the slash-command when applicable 
            suggestion= self.intent_suggestion(user_input)
            if suggestion: 
                return "SUGGESTION", "SP_DEFAULT",  self.history.copy(),suggestion
        
            #If there is no sggestion -> normal parse
            parsed= self._parse(user_input)
            intent= parsed["intent"]
            payload= parsed["payload"]

        #Select system prompt by intent 
        match intent: 
            case "NOTE":
                prompt_key= "SP_NOTE"
            case "REMINDER":
                prompt_key= "SP_REMINDER"
            case "AGENDA":
                prompt_key= "SP_AGENDA"
            case "SEARCH":
                prompt_key= "SP_SEARCH"
            case "VIEWNOTE":
                prompt_key= "SP_VIEWNOTE"
            case _:
                prompt_key= "SP_DEFAULT"    



        return intent, prompt_key, self.history, payload


    
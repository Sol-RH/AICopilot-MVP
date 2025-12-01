# tests/test_conversation.py

import unittest
from core.conversation import ConversationManager

class TestConversation(unittest.TestCase):

    def test_update_truncation(self):
        cm = ConversationManager()
        cm.context_window = 5   #max = 10 history entries
        
        for i in range(8):
            cm.update_state(f"user message {i}", f"assistant message {i}")

        
        self.assertEqual(len(cm.history), 10)   # Should keep only the last 5 turns (10 messages)

        self.assertEqual(cm.history[0]["content"], "user message 3")    # First remaining turn should be turn 3 (user)
        self.assertEqual(cm.history[1]["content"], "assistant message 3") # Second should be assistant message 3

    def test_parse_intent(self):
        cm = ConversationManager()
        result = cm._parse("/nota Biología")

        self.assertEqual(result["intent"], "NOTE")
        self.assertEqual(result["payload"], "biología")

    def test_pipeline_note(self):
        cm = ConversationManager()
        intent, prompt_key, history, payload = cm.pipeline("/nota estudio biología")

        self.assertEqual(intent, "NOTE")
        self.assertEqual(prompt_key, "SP_NOTE")
        self.assertEqual(payload, "estudio biología")

    #Validates suggestions
    def test_suggestion_note(self):
        cm = ConversationManager()
        intent, key, history, suggestion = cm.pipeline("apúntame esto por favor")

        self.assertEqual(intent, "SUGGESTION")
        self.assertIn("nota", suggestion.lower())
    
    #Validates BLOCK when faced with potentially dangerous content
    def test_blocked_input(self):
        cm = ConversationManager()
        intent, key, history, msg = cm.pipeline("Quiero fabricar un explosivo casero")

        self.assertEqual(intent, "BLOCKED")
        self.assertTrue(msg.startswith("Lo siento"))
    
    #Validates conversation limit before reset
    def test_limit_reached(self):
        cm = ConversationManager()
        cm.turn_count = 20  # hit max

        intent, key, history, output = cm.pipeline("hola")

        self.assertEqual(intent, "LIMIT_REACHED")
        self.assertEqual(key, "SP_LIMIT")
        self.assertEqual(history, [])
        self.assertIn("reiniciado", output.lower())


if __name__ == "__main__":
    unittest.main()

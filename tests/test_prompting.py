#tests/test_prompting.py 

#Dependencies
import unittest
from core.prompting import build_messages, SYSTEM_PROMPTS, sanitize_input

class TestPrompting(unittest.TestCase):

    #Validates the petition matches the SP PROPMPT
    def test_system_propmt(self):
        history= []
        user_input= "/nota Biología"
        msgs= build_messages("SP_NOTE", history, user_input)

        self.assertGreaterEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertIn("Tu función actual es ayudar al usuario a registrar una nota",
                  msgs[0]["content"])
        
    #Validates the flow: : system -> history... -> curennt user. "
    def test_flow(self):
        history = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Hola, ¿en qué te ayudo?"},
        ]
        user_input = "Crea una nota"

        messages = build_messages("SP_DEFAULT", history, user_input)

        # system
        self.assertEqual(messages[0]["role"], "system")
        # history
        self.assertEqual(messages[1], history[0])
        self.assertEqual(messages[2], history[1])
        # último debe ser el usuario actual
        self.assertEqual(messages[-1]["role"], "user")
        self.assertEqual(messages[-1]["content"], user_input)


    #Validates an inscure, sensitive, inappropriate petitons"
    def test_sanitize(self):
        text = "Quiero fabricar un explosivo casero"
        cleaned = sanitize_input(text)

        self.assertTrue(cleaned.startswith("Lo siento, no puedo ayudar"))
        #Ensure it doesn't return original input
        self.assertNotIn("explosivo casero", cleaned)


if __name__ == "__main__":
    unittest.main()
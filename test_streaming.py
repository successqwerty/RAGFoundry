import unittest
import json
from fastapi.testclient import TestClient
from main import app, pipeline
import db_manager

class TestStreamingAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        db_manager.init_db()

    def test_01_streaming_response_sse_events(self):
        """Test POST /ask with stream=True returns real SSE lines."""
        payload = {
            "question": "What is the candidate's work experience?",
            "k": 2,
            "provider": "gemini",
            "stream": True
        }
        
        response = self.client.post("/ask", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers.get("content-type", ""))

        lines = response.text.strip().split("\n\n")
        events = []
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("data:"):
                event_data = json.loads(line_str[5:].strip())
                events.append(event_data)

        self.assertGreater(len(events), 0, "SSE stream should yield events")
        
        event_types = [e["type"] for e in events]
        self.assertIn("conversation_meta", event_types)
        self.assertIn("sources", event_types)
        self.assertIn("token", event_types)
        self.assertIn("complete", event_types)

        # Check tokens
        token_events = [e for e in events if e["type"] == "token"]
        self.assertGreater(len(token_events), 0, "Should have streamed multiple token deltas")
        full_text = "".join([t["delta"] for t in token_events])
        self.assertGreater(len(full_text), 5, "Streamed text should not be empty")

        # Check complete event
        complete_event = [e for e in events if e["type"] == "complete"][0]
        self.assertIn("precision", complete_event)
        self.assertIn("accuracy", complete_event)
        self.assertIn("conversation_id", complete_event)
        conv_id = complete_event["conversation_id"]

        # Check DB persistence: exactly 1 user msg and 1 assistant msg
        messages = db_manager.get_conversation_messages(conv_id)
        self.assertEqual(len(messages), 2, "DB should contain exactly 2 messages (1 user, 1 assistant)")
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[0]["content"], payload["question"])
        self.assertTrue(len(messages[1]["content"]) > 0)
        self.assertGreater(messages[1]["accuracy"], 0)

        # Clean up
        db_manager.delete_conversation(conv_id)

    def test_02_non_streaming_fallback(self):
        """Test POST /ask with stream=False returns direct JSON."""
        payload = {
            "question": "What is the educational background?",
            "k": 2,
            "provider": "gemini",
            "stream": False
        }
        response = self.client.post("/ask", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("question", data)
        self.assertIn("answer", data)
        self.assertIn("sources", data)
        self.assertIn("precision", data)
        self.assertIn("accuracy", data)
        conv_id = data.get("conversation_id")
        if conv_id:
            db_manager.delete_conversation(conv_id)

if __name__ == "__main__":
    unittest.main()

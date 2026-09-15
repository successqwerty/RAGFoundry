import unittest
from fastapi.testclient import TestClient
from main import app

class TestRAGFoundryAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        """Test GET /health returns 200 OK and status ok."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("documents_folder", data)

    def test_02_ask_endpoint_empty_question(self):
        """Test POST /ask rejects empty questions with HTTP 400."""
        response = self.client.post("/ask", json={"question": "   "})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("cannot be empty", data["detail"])

    def test_03_ask_endpoint_success(self):
        """Test POST /ask successfully calls RAGPipeline and returns formatted JSON."""
        payload = {
            "question": "What is Human Resource Management?",
            "k": 2,
            "provider": "gemini"
        }
        response = self.client.post("/ask", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("question", data)
        self.assertIn("answer", data)
        self.assertIn("sources", data)
        self.assertIn("retrieved_chunks", data)
        self.assertIn("elapsed_sec", data)
        self.assertEqual(data["question"], payload["question"])

    def test_04_cors_headers(self):
        """Test CORS headers are present for cross-origin requests."""
        response = self.client.options("/ask", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("access-control-allow-origin", response.headers)

    def test_05_multi_turn_conversations(self):
        """Test multi-turn chat persistence: Q1 creates conv, Q2 appends to same conv."""
        # Turn 1
        r1 = self.client.post("/ask", json={"question": "What is Article 12?", "k": 2, "provider": "gemini"})
        self.assertEqual(r1.status_code, 200)
        d1 = r1.json()
        conv_id = d1.get("conversation_id")
        self.assertTrue(conv_id, "Response should include conversation_id")

        # Turn 2 in SAME conversation
        r2 = self.client.post("/ask", json={"conversation_id": conv_id, "question": "What are the important cases?", "k": 2, "provider": "gemini"})
        self.assertEqual(r2.status_code, 200)
        d2 = r2.json()
        self.assertEqual(d2.get("conversation_id"), conv_id, "Turn 2 must belong to SAME conversation_id")

        # Verify GET /conversations/{id} returns pure stored messages (2 user, 2 assistant)
        r3 = self.client.get(f"/conversations/{conv_id}")
        self.assertEqual(r3.status_code, 200)
        d3 = r3.json()
        self.assertEqual(d3["id"], conv_id)
        messages = d3["messages"]
        self.assertEqual(len(messages), 4, "Should have exactly 4 messages (2 user + 2 assistant)")
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[2]["role"], "user")
        self.assertEqual(messages[3]["role"], "assistant")

        # Clean up
        del_r = self.client.delete(f"/conversations/{conv_id}")
        self.assertEqual(del_r.status_code, 200)

    def test_06_conversations_list_and_delete(self):
        """Test GET /conversations and DELETE /conversations/{id}."""
        # Create test conversation
        r = self.client.post("/ask", json={"question": "Test question for list", "k": 2, "provider": "gemini"})
        self.assertEqual(r.status_code, 200)
        conv_id = r.json().get("conversation_id")

        # Verify in list
        list_r = self.client.get("/conversations")
        self.assertEqual(list_r.status_code, 200)
        convs = list_r.json()
        matching = [c for c in convs if c["id"] == conv_id]
        self.assertEqual(len(matching), 1, "Should appear as ONE conversation card in list")

        # Delete conversation
        del_r = self.client.delete(f"/conversations/{conv_id}")
        self.assertEqual(del_r.status_code, 200)

        # Verify 404 after delete
        check_r = self.client.get(f"/conversations/{conv_id}")
        self.assertEqual(check_r.status_code, 404)

if __name__ == "__main__":
    unittest.main()


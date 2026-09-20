import unittest
from rag_pipeline import calculate_rag_metrics
import db_manager
from main import AskResponse

class TestAccuracyAndPrecisionMetrics(unittest.TestCase):
    def setUp(self):
        db_manager.init_db()

    def test_metrics_calculation(self):
        question = "What is HRM?"
        context_chunks = [
            {"filename": "doc1.txt", "text": "Human Resource Management (HRM) is the strategic approach to managing people in an organization.", "rerank_score": 2.5},
            {"filename": "doc2.txt", "text": "HRM focuses on recruitment, management, and providing direction for the people who work in an organization.", "rerank_score": 1.8}
        ]
        answer = "Human Resource Management (HRM) is the strategic approach to managing people and recruitment in an organization."
        
        metrics = calculate_rag_metrics(question, answer, context_chunks)
        self.assertIn("precision", metrics)
        self.assertIn("accuracy", metrics)
        self.assertIn("precision_pct", metrics)
        self.assertIn("accuracy_pct", metrics)
        self.assertGreater(metrics["precision"], 0)
        self.assertGreater(metrics["accuracy"], 0)
        self.assertTrue(metrics["precision_pct"].endswith("%"))
        self.assertTrue(metrics["accuracy_pct"].endswith("%"))

    def test_db_manager_precision_accuracy_persistence(self):
        conv_id = db_manager.create_conversation("test_user", "Test Precision & Accuracy")
        db_manager.save_message(conv_id, "user", "What is HRM?")
        db_manager.save_message(
            conv_id,
            "assistant",
            "HRM is Human Resource Management.",
            sources=["doc1.txt"],
            chunks=[{"text": "HRM is Human Resource Management."}],
            precision=92.5,
            accuracy=96.8,
            precision_pct="92.5%",
            accuracy_pct="96.8%",
            elapsed_sec=0.85
        )

        messages = db_manager.get_conversation_messages(conv_id)
        self.assertEqual(len(messages), 2)
        assistant_msg = messages[1]
        self.assertEqual(assistant_msg["precision"], 92.5)
        self.assertEqual(assistant_msg["accuracy"], 96.8)
        self.assertEqual(assistant_msg["precision_pct"], "92.5%")
        self.assertEqual(assistant_msg["accuracy_pct"], "96.8%")
        self.assertEqual(assistant_msg["elapsed_sec"], 0.85)

        # Clean up
        db_manager.delete_conversation(conv_id)

    def test_ask_response_schema(self):
        resp = AskResponse(
            question="What is HRM?",
            answer="HRM is Human Resource Management.",
            sources=["doc1.txt"],
            retrieved_chunks=[{"text": "Sample"}],
            elapsed_sec=1.2,
            precision=88.5,
            accuracy=94.2,
            precision_pct="88.5%",
            accuracy_pct="94.2%",
            conversation_id="conv_123"
        )
        self.assertEqual(resp.precision, 88.5)
        self.assertEqual(resp.accuracy, 94.2)
        self.assertEqual(resp.precision_pct, "88.5%")
        self.assertEqual(resp.accuracy_pct, "94.2%")

if __name__ == "__main__":
    unittest.main()

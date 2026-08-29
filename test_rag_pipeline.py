import unittest
import os
import json
import shutil
from loader_factory import DocumentLoaderFactory
from ingestion import load_documents
from vector_store import PersistentVectorStore
from rag_pipeline import RAGPipeline
import db_manager

class TestEnterpriseRAGPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs("test_data", exist_ok=True)
        # Create sample TXT file
        with open("test_data/sample_doc.txt", "w", encoding="utf-8") as f:
            f.write("Human Resource Management (HRM) involves planning, organizing, and developing human resources. Unit 1 covers foundational principles.")
        # Create sample JSON file
        with open("test_data/sample_data.json", "w", encoding="utf-8") as f:
            json.dump({"title": "RAGFoundry Project", "version": "2.0", "status": "Production Ready"}, f)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists("test_data"):
            shutil.rmtree("test_data")

    def test_01_loader_factory(self):
        res_txt = DocumentLoaderFactory.load_file("test_data/sample_doc.txt", "sample_doc.txt")
        self.assertTrue(res_txt["supported"])
        self.assertTrue(len(res_txt["pages"]) > 0)
        self.assertIn("Human Resource Management", res_txt["pages"][0]["text"])

        res_json = DocumentLoaderFactory.load_file("test_data/sample_data.json", "sample_data.json")
        self.assertTrue(res_json["supported"])
        self.assertIn("Production Ready", res_json["pages"][0]["text"])

    def test_02_unsupported_file(self):
        res_unsupported = DocumentLoaderFactory.load_file("dummy.exe", "dummy.exe")
        self.assertFalse(res_unsupported["supported"])
        self.assertIn("Unsupported file format", res_unsupported["error"])

    def test_03_db_manager_init(self):
        db_manager.init_db()
        conv_id = db_manager.create_conversation("user_test", "Test Chat")
        self.assertTrue(conv_id.startswith("conv_"))
        db_manager.save_message(conv_id, "user", "What is HRM?")
        msgs = db_manager.get_conversation_messages(conv_id)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["content"], "What is HRM?")

    def test_04_rag_pipeline_stream(self):
        pipeline = RAGPipeline("test_data")
        pipeline.sync(user_id="user_test")
        
        events = list(pipeline.ask_stream("What is HRM?", k=2, provider="gemini", user_id="user_test"))
        self.assertTrue(len(events) > 0)
        types = [e["type"] for e in events]
        self.assertIn("status", types)
        self.assertIn("sources", types)

if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.database import TutorDatabase


class TutorDatabaseTests(unittest.TestCase):
    def test_course_rename_and_document_metadata_survive_database_reopen(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "tutor.db"
            database = TutorDatabase(database_path)
            database.create_course("BIO101", "Biology")
            database.create_document("document-1", "BIO101", "cells.pdf", "stored.pdf", "extracted/document-1.json")
            database.set_document_status("document-1", "completed")
            database.create_course("BIO101", "Cell Biology")

            reopened_database = TutorDatabase(database_path)
            self.assertEqual(reopened_database.list_courses(), [{"course_id": "BIO101", "name": "Cell Biology", "description": ""}])
            self.assertEqual(reopened_database.list_documents("BIO101")[0]["filename"], "cells.pdf")
            self.assertEqual(reopened_database.list_documents("BIO101")[0]["status"], "completed")

    def test_persists_course_document_conversation_and_messages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database = TutorDatabase(Path(temp_dir) / "tutor.db")
            database.create_course("ACC101", "Financial Accounting", "Introductory accounting")
            database.create_document("123", "ACC101", "Chapter 1 slides.pdf")
            database.set_document_status("123", "indexed")
            conversation_id = database.create_conversation("ACC101", "conversation-1")
            database.add_message(conversation_id, "user", "What is a balance sheet?")
            database.add_message(conversation_id, "assistant", "I don't know based on the uploaded material.")

            document = database.get_document("123")
            messages = database.get_messages(conversation_id)

        self.assertEqual(document["document_id"], "123")
        self.assertEqual(document["course_id"], "ACC101")
        self.assertEqual(document["filename"], "Chapter 1 slides.pdf")
        self.assertEqual(document["status"], "indexed")
        self.assertTrue(document["upload_date"])
        self.assertEqual([message["role"] for message in messages], ["user", "assistant"])
        self.assertTrue(all(message["message_id"] for message in messages))
        self.assertTrue(all(message["timestamp"] for message in messages))

    def test_conversation_cannot_be_reused_for_a_different_course(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database = TutorDatabase(Path(temp_dir) / "tutor.db")
            database.create_conversation("ACC101", "conversation-1")

            with self.assertRaises(ValueError):
                database.get_or_create_conversation("BIO101", "conversation-1")


if __name__ == "__main__":
    unittest.main()

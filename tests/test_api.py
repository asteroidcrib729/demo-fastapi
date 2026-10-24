"""Exercise the HTTP contract without connecting to any database."""

import os
import unittest
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient

with patch.dict(os.environ, {"DATABASE_URL": "postgres://unused.invalid/postgres"}):
    from main import app


class RecordsAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.connect_patch = patch("main.psycopg.connect")
        self.connect = self.connect_patch.start()
        self.addCleanup(self.connect_patch.stop)
        self.connection = self.connect.return_value.__enter__.return_value
        self.connection.execute.return_value.fetchall.return_value = []

    def test_health_does_not_query_database(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.connect.assert_not_called()

    def test_public_records_are_serialized_and_connection_is_closed(self):
        self.connection.execute.return_value.fetchall.return_value = [
            {"id": 1, "name": "Example", "value": "Demo", "status": "active"}
        ]
        response = self.client.get("/records?limit=2&offset=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["name"], "Example")
        self.assertIs(self.connection.read_only, True)
        self.assertEqual(self.connection.execute.call_args.args[1], (2, 1))
        self.connect.return_value.__exit__.assert_called_once()

    def test_empty_result_is_an_empty_list(self):
        self.assertEqual(self.client.get("/records").json(), [])

    def test_invalid_page_is_rejected_before_database_access(self):
        for query in ["limit=0", "limit=101", "offset=-1", "limit=abc"]:
            with self.subTest(query=query):
                self.assertEqual(self.client.get(f"/records?{query}").status_code, 422)
        self.connect.assert_not_called()

    def test_database_errors_do_not_expose_internal_details(self):
        self.connect.side_effect = psycopg.OperationalError("private diagnostic")
        response = self.client.get("/records")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(), {"detail": "Records are temporarily unavailable."}
        )

    def test_query_failure_closes_connection(self):
        self.connection.execute.side_effect = psycopg.OperationalError("private SQL")
        response = self.client.get("/records")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private SQL", response.text)
        self.connect.return_value.__exit__.assert_called_once()

    def test_api_has_no_record_write_routes(self):
        for method in ["post", "put", "patch", "delete"]:
            with self.subTest(method=method):
                self.assertEqual(
                    getattr(self.client, method)("/records").status_code, 405
                )
        self.connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""Test suite for FastAPI endpoints in app.py."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app import app
from src.models import TenantUEMapping, UserGroup

client = TestClient(app)


class TestAppEndpoints(unittest.TestCase):
    """Test FastAPI application endpoints with mocked backend clients."""

    def test_status_endpoint(self):
        response = client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("default_apn", data)

    def test_config_endpoint(self):
        response = client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("client_id", data)
        self.assertIn("tsg_id", data)
        self.assertIn("has_secret", data)

    @patch("app.Prisma5GClient.list_tenants")
    def test_tenants_endpoint(self, mock_tenants):
        mock_tenants.return_value = [
            {"id": "1965438697", "display_name": "SP-5G-POC2-Transatel"},
            {"id": "1291887562", "display_name": "Transatel demo", "parent_id": "1965438697"},
        ]
        response = client.get("/api/tenants")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 2)

    @patch("app.Prisma5GClient.list_tenant_ues")
    def test_ues_endpoint(self, mock_ues):
        mock_ues.return_value = {
            "totalItems": 1,
            "models": [
                TenantUEMapping(
                    identity_id="uuid-1",
                    imsi="208950123456789",
                    imei="860123123456789",
                    apn="sasetest",
                    tsg_id="1291887562",
                    tenant_name="Transatel demo",
                )
            ],
            "data": [],
        }
        response = client.get("/api/ues")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["apn"], "sasetest")

    @patch("app.Prisma5GClient.create_tenant_ue")
    def test_create_ue_endpoint(self, mock_create):
        mock_create.return_value = {
            "data": {
                "id": "new-sim-id-99",
                "imsi": "208950999999999",
                "imei": "860123999999999",
                "apn": "sasetest",
            }
        }
        payload = {
            "imsi": "208950999999999",
            "imei": "860123999999999",
            "apn": "sasetest",
            "tsg_id": "1291887562",
        }
        response = client.post("/api/ues", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["identity_id"], "new-sim-id-99")

    @patch("app.Prisma5GClient.delete_tenant_ue")
    def test_delete_ue_endpoint(self, mock_del):
        mock_del.return_value = {"status": "deleted"}
        response = client.delete("/api/ues/uuid-to-delete")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

    @patch("app.Prisma5GClient.register_ue_session")
    def test_register_session_endpoint(self, mock_sess):
        mock_sess.return_value = {"status_code": 202, "data": {"status": "accepted"}}
        payload = {
            "imsi": "208950999999999",
            "imei": "860123999999999",
            "apn": "sasetest",
            "ip_type": "IPv4",
            "ipv4_addr": "10.56.0.195",
        }
        response = client.post("/api/sessions/register", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status_code"], 202)

    def test_serve_index_html(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Prisma Access 5G SASE", response.text)

    def test_metrics_summary_endpoint(self):
        response = client.get("/api/metrics/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("total_5g_tenants", data["data"])
        self.assertIn("total_bandwidth_mbps", data["data"])
        self.assertIn("interconnects_count", data["data"])

    def test_metrics_throughput_endpoint(self):
        response = client.get("/api/metrics/throughput?time_range=24h&region=europe-west9")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["region"], "europe-west9")
        self.assertTrue(len(data["points"]) > 0)


if __name__ == "__main__":
    unittest.main()

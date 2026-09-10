"""Unit tests for Prisma SASE 5G client with mocked HTTP responses."""

import unittest
from unittest.mock import patch, MagicMock
import time

from src.config import Config, load_config
from src.auth import PANWAuthManager
from src.models import TenantUEMapping, UESession, UserGroup
from src.client import Prisma5GClient


class TestConfigAndModels(unittest.TestCase):
    """Test configuration loading and model serialization."""

    def test_config_validation(self):
        # Empty config should fail validation
        cfg = Config()
        with self.assertRaises(ValueError):
            cfg.validate()

        # Config with client credentials
        valid_cfg = Config(
            client_id="test_client",
            client_secret="test_secret",
            tsg_id="12345678",
        )
        valid_cfg.validate()  # Should not raise

        # Config with static token
        token_cfg = Config(auth_token="bearer_token_xyz")
        token_cfg.validate()  # Should not raise

    def test_tenant_ue_model(self):
        ue = TenantUEMapping(
            imsi="123456789012345",
            imei="987654321098765",
            apn="test.apn",
            tsg_id="1001",
        )
        payload = ue.to_request_payload()
        self.assertEqual(payload["imsi"], "123456789012345")
        self.assertEqual(payload["imei"], "987654321098765")
        self.assertEqual(payload["apn"], "test.apn")
        self.assertEqual(payload["tsg_id"], "1001")

        # Parsing from API dict
        api_data = {
            "id": "uuid-123",
            "imsi": "123456789012345",
            "imei": "987654321098765",
            "apn": "test.apn",
            "tsg_id": "1001",
        }
        parsed = TenantUEMapping.from_api_dict(api_data)
        self.assertEqual(parsed.identity_id, "uuid-123")
        self.assertEqual(parsed.imsi, "123456789012345")

    def test_ue_session_model(self):
        sess = UESession(
            imsi="123456789012345",
            imei="987654321098765",
            apn="test.apn",
            ip_type="IPV4",
            ipv4_addr="10.0.0.5",
        )
        payload = sess.to_request_payload()
        self.assertEqual(payload["ipType"], "IPV4")
        self.assertEqual(payload["ipv4Addr"], "10.0.0.5")
        self.assertIn("eventTime", payload)


class TestPrisma5GClient(unittest.TestCase):
    """Test client operations with mocked requests."""

    def setUp(self):
        self.config = Config(
            client_id="test_client_id",
            client_secret="test_secret",
            tsg_id="1886576124",
            api_base_url="https://stratacloudmanager.paloaltonetworks.com",
            auth_url="https://auth.apps.paloaltonetworks.com/am/oauth2/access_token",
        )
        self.client = Prisma5GClient(self.config)

    @patch("requests.post")
    def test_auth_token_fetch_and_caching(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "mock_jwt_access_token_12345",
            "expires_in": 900,
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_resp

        auth_mgr = PANWAuthManager(self.config)
        token1 = auth_mgr.get_access_token()
        self.assertEqual(token1, "mock_jwt_access_token_12345")
        self.assertEqual(mock_post.call_count, 1)

        # Second call should use cache without HTTP request
        token2 = auth_mgr.get_access_token()
        self.assertEqual(token2, "mock_jwt_access_token_12345")
        self.assertEqual(mock_post.call_count, 1)

    @patch.object(PANWAuthManager, "get_access_token", return_value="fake_token")
    @patch("requests.Session.request")
    def test_list_tenant_ues(self, mock_req, mock_auth):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"totalItems": 1, "data": []}'
        mock_resp.json.return_value = {
            "totalItems": 1,
            "data": [
                {
                    "identity_id": "id-abc-123",
                    "tsg_id": "1886576124",
                    "imei": "111111111111111",
                    "imsi": "222222222222222",
                    "apn": "internet.panw.com",
                }
            ],
        }
        mock_req.return_value = mock_resp

        res = self.client.list_tenant_ues(tsg_id="1886576124")
        self.assertEqual(res["totalItems"], 1)
        self.assertEqual(len(res["models"]), 1)
        self.assertEqual(res["models"][0].identity_id, "id-abc-123")

        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["url"], "https://stratacloudmanager.paloaltonetworks.com/mt/manage/5g/tenantUEInfo/list")
        self.assertEqual(kwargs["json"], {"tsg_id": "1886576124"})

    @patch.object(PANWAuthManager, "get_access_token", return_value="fake_token")
    @patch("requests.Session.request")
    def test_create_tenant_ue(self, mock_req, mock_auth):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "id": "new-ue-uuid-456",
                "tsg_id": "1886576124",
                "imei": "123456789012345",
                "imsi": "543210987654321",
                "apn": "custom.apn",
            }
        }
        mock_req.return_value = mock_resp

        res = self.client.create_tenant_ue(
            imsi="543210987654321",
            imei="123456789012345",
            apn="custom.apn",
            tsg_id="1886576124",
            root_tsg_id="1886576124",
        )
        self.assertEqual(res["data"]["id"], "new-ue-uuid-456")
        self.assertEqual(res["model"].identity_id, "new-ue-uuid-456")

        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["url"], "https://stratacloudmanager.paloaltonetworks.com/mt/manage/5g/tenantUEInfo")
        self.assertEqual(kwargs["json"]["imsi"], "543210987654321")

    @patch.object(PANWAuthManager, "get_access_token", return_value="fake_token")
    @patch("requests.Session.request")
    def test_delete_tenant_ue(self, mock_req, mock_auth):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "success"}
        mock_req.return_value = mock_resp

        res = self.client.delete_tenant_ue("uuid-delete-123")
        self.assertEqual(res["status"], "success")

        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args
        self.assertEqual(kwargs["method"], "DELETE")
        self.assertEqual(kwargs["url"], "https://stratacloudmanager.paloaltonetworks.com/mt/manage/5g/tenantUEInfo/uuid-delete-123")

    @patch.object(PANWAuthManager, "get_access_token", return_value="fake_token")
    @patch("requests.Session.request")
    def test_register_session_telemetry(self, mock_req, mock_auth):
        mock_resp = MagicMock()
        mock_resp.status_code = 202
        mock_resp.json.return_value = {"status": "accepted"}
        mock_req.return_value = mock_resp

        sess = UESession(
            imsi="123456789012345",
            imei="123456789012345",
            apn="internet.panw.com",
            ip_type="IPV4",
            ipv4_addr="10.10.10.10",
        )
        res = self.client.register_ue_session(sess)
        self.assertEqual(res["status_code"], 202)

        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["url"], "https://stratacloudmanager.paloaltonetworks.com/mt/manage/5g/register/ue")
        self.assertEqual(kwargs["json"][0]["ipv4Addr"], "10.10.10.10")

    @patch.object(PANWAuthManager, "get_access_token", return_value="fake_token")
    @patch("requests.Session.request")
    def test_create_user_group(self, mock_req, mock_auth):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"group_id": "grp-123", "group_name": "permissivev2"}
        mock_req.return_value = mock_resp

        res = self.client.create_user_group(
            group_name="permissivev2",
            tsg_id="1965438697",
            identity_ids=["id-sim-001"],
        )
        self.assertEqual(res["group_id"], "grp-123")

        args, kwargs = mock_req.call_args
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["json"]["group_name"], "permissivev2")
        self.assertEqual(kwargs["json"]["identity_id"], ["id-sim-001"])


if __name__ == "__main__":
    unittest.main()

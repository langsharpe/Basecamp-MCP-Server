"""Tests for campfire line operations (client methods + MCP tools)."""

import sys
import os
import unittest
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from basecamp_client import BasecampClient


# ---------------------------------------------------------------------------
# BasecampClient method tests (sync, using mocked requests)
# ---------------------------------------------------------------------------

class TestBasecampClientGetCampfireLine(unittest.TestCase):
    """Test BasecampClient.get_campfire_line."""

    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token',
            account_id='12345',
            user_agent='Test Agent',
            auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_campfire_line_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 500,
            "content": "Hello team!",
            "created_at": "2025-01-01T12:00:00Z",
        }
        mock_get.return_value = mock_response

        result = self.client.get_campfire_line("123", "456", "500")

        self.assertEqual(result["id"], 500)
        self.assertEqual(result["content"], "Hello team!")
        self.assertIn("buckets/123/chats/456/lines/500.json", mock_get.call_args[0][0])

    @patch('requests.get')
    def test_get_campfire_line_not_found(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.get_campfire_line("123", "456", "999")
        self.assertIn("404", str(ctx.exception))


class TestBasecampClientCreateCampfireLine(unittest.TestCase):
    """Test BasecampClient.create_campfire_line."""

    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token',
            account_id='12345',
            user_agent='Test Agent',
            auth_mode='oauth'
        )

    @patch('requests.post')
    def test_create_campfire_line_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 501,
            "content": "Hello from MCP!",
            "created_at": "2025-01-01T12:00:00Z",
        }
        mock_post.return_value = mock_response

        result = self.client.create_campfire_line("123", "456", "Hello from MCP!")

        self.assertEqual(result["id"], 501)
        self.assertEqual(result["content"], "Hello from MCP!")
        self.assertIn("buckets/123/chats/456/lines.json", mock_post.call_args[0][0])
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["content"], "Hello from MCP!")

    @patch('requests.post')
    def test_create_campfire_line_html(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 502,
            "content": "<strong>Important</strong> update",
        }
        mock_post.return_value = mock_response

        result = self.client.create_campfire_line("123", "456", "<strong>Important</strong> update")

        self.assertEqual(result["id"], 502)
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["content"], "<strong>Important</strong> update")

    @patch('requests.post')
    def test_create_campfire_line_failure(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.text = "Unprocessable Entity"
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.create_campfire_line("123", "456", "Bad message")
        self.assertIn("422", str(ctx.exception))


class TestBasecampClientDeleteCampfireLine(unittest.TestCase):
    """Test BasecampClient.delete_campfire_line."""

    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token',
            account_id='12345',
            user_agent='Test Agent',
            auth_mode='oauth'
        )

    @patch('requests.delete')
    def test_delete_campfire_line_success(self, mock_delete):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        result = self.client.delete_campfire_line("123", "456", "500")

        self.assertTrue(result)
        self.assertIn("buckets/123/chats/456/lines/500.json", mock_delete.call_args[0][0])

    @patch('requests.delete')
    def test_delete_campfire_line_not_found(self, mock_delete):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_delete.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.delete_campfire_line("123", "456", "999")
        self.assertIn("404", str(ctx.exception))


# ---------------------------------------------------------------------------
# FastMCP tool wrapper tests (async, using mocked client)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    """Create a mocked BasecampClient."""
    client = Mock(spec=BasecampClient)
    return client


@pytest.fixture
def patch_auth(mock_client):
    """Patch auth helpers to return the mock client."""
    with patch('basecamp_fastmcp._get_basecamp_client', return_value=mock_client):
        yield mock_client


class TestFastMCPGetCampfireLine:
    @pytest.mark.anyio
    async def test_get_campfire_line_success(self, patch_auth):
        patch_auth.get_campfire_line.return_value = {
            "id": 500,
            "content": "Hello team!",
            "created_at": "2025-01-01T12:00:00Z",
        }
        from basecamp_fastmcp import get_campfire_line
        result = await get_campfire_line("123", "456", "500")
        assert result["status"] == "success"
        assert result["campfire_line"]["id"] == 500

    @pytest.mark.anyio
    async def test_get_campfire_line_error(self, patch_auth):
        patch_auth.get_campfire_line.side_effect = Exception("Not found")
        from basecamp_fastmcp import get_campfire_line
        result = await get_campfire_line("123", "456", "999")
        assert "error" in result
        assert "Not found" in result["message"]

    @pytest.mark.anyio
    async def test_get_campfire_line_expired_token(self, patch_auth):
        patch_auth.get_campfire_line.side_effect = Exception("401 token expired")
        from basecamp_fastmcp import get_campfire_line
        result = await get_campfire_line("123", "456", "500")
        assert result["error"] == "OAuth token expired"

    @pytest.mark.anyio
    async def test_get_campfire_line_no_auth(self):
        with patch('basecamp_fastmcp._get_basecamp_client', return_value=None):
            with patch('basecamp_fastmcp.token_storage') as mock_ts:
                mock_ts.is_token_expired.return_value = True
                from basecamp_fastmcp import get_campfire_line
                result = await get_campfire_line("123", "456", "500")
                assert "error" in result


class TestFastMCPCreateCampfireLine:
    @pytest.mark.anyio
    async def test_create_campfire_line_success(self, patch_auth):
        patch_auth.create_campfire_line.return_value = {
            "id": 501,
            "content": "Hello from MCP!",
            "created_at": "2025-01-01T12:00:00Z",
        }
        from basecamp_fastmcp import create_campfire_line
        result = await create_campfire_line("123", "456", "Hello from MCP!")
        assert result["status"] == "success"
        assert result["campfire_line"]["id"] == 501
        assert "sent" in result["message"].lower()

    @pytest.mark.anyio
    async def test_create_campfire_line_error(self, patch_auth):
        patch_auth.create_campfire_line.side_effect = Exception("API error")
        from basecamp_fastmcp import create_campfire_line
        result = await create_campfire_line("123", "456", "Fail")
        assert "error" in result
        assert "API error" in result["message"]

    @pytest.mark.anyio
    async def test_create_campfire_line_expired_token(self, patch_auth):
        patch_auth.create_campfire_line.side_effect = Exception("401 token expired")
        from basecamp_fastmcp import create_campfire_line
        result = await create_campfire_line("123", "456", "Fail")
        assert result["error"] == "OAuth token expired"

    @pytest.mark.anyio
    async def test_create_campfire_line_no_auth(self):
        with patch('basecamp_fastmcp._get_basecamp_client', return_value=None):
            with patch('basecamp_fastmcp.token_storage') as mock_ts:
                mock_ts.is_token_expired.return_value = False
                from basecamp_fastmcp import create_campfire_line
                result = await create_campfire_line("123", "456", "No auth")
                assert "error" in result
                assert "auth" in result["error"].lower()


class TestFastMCPDeleteCampfireLine:
    @pytest.mark.anyio
    async def test_delete_campfire_line_success(self, patch_auth):
        patch_auth.delete_campfire_line.return_value = True
        from basecamp_fastmcp import delete_campfire_line
        result = await delete_campfire_line("123", "456", "500")
        assert result["status"] == "success"
        assert "deleted" in result["message"].lower()

    @pytest.mark.anyio
    async def test_delete_campfire_line_error(self, patch_auth):
        patch_auth.delete_campfire_line.side_effect = Exception("Not found")
        from basecamp_fastmcp import delete_campfire_line
        result = await delete_campfire_line("123", "456", "999")
        assert "error" in result
        assert "Not found" in result["message"]

    @pytest.mark.anyio
    async def test_delete_campfire_line_expired_token(self, patch_auth):
        patch_auth.delete_campfire_line.side_effect = Exception("401 token expired")
        from basecamp_fastmcp import delete_campfire_line
        result = await delete_campfire_line("123", "456", "500")
        assert result["error"] == "OAuth token expired"

    @pytest.mark.anyio
    async def test_delete_campfire_line_no_auth(self):
        with patch('basecamp_fastmcp._get_basecamp_client', return_value=None):
            with patch('basecamp_fastmcp.token_storage') as mock_ts:
                mock_ts.is_token_expired.return_value = True
                from basecamp_fastmcp import delete_campfire_line
                result = await delete_campfire_line("123", "456", "500")
                assert "error" in result


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Tests for create_message and update_message (client methods + MCP tools)."""

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

class TestBasecampClientCreateMessage(unittest.TestCase):
    """Test BasecampClient.create_message."""

    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token',
            account_id='12345',
            user_agent='Test Agent',
            auth_mode='oauth'
        )

    @patch('requests.post')
    def test_create_message_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 100,
            "subject": "Kickoff",
            "content": "<p>Welcome everyone!</p>",
            "status": "active",
        }
        mock_post.return_value = mock_response

        result = self.client.create_message("123", "456", "Kickoff", content="<p>Welcome everyone!</p>")

        self.assertEqual(result["id"], 100)
        self.assertEqual(result["subject"], "Kickoff")
        self.assertIn("buckets/123/message_boards/456/messages.json", mock_post.call_args[0][0])
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["subject"], "Kickoff")
        self.assertEqual(payload["status"], "active")
        self.assertEqual(payload["content"], "<p>Welcome everyone!</p>")

    @patch('requests.post')
    def test_create_message_minimal(self, mock_post):
        """Create a message with only the required subject field."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 101, "subject": "Quick note"}
        mock_post.return_value = mock_response

        result = self.client.create_message("123", "456", "Quick note")

        self.assertEqual(result["subject"], "Quick note")
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["subject"], "Quick note")
        self.assertEqual(payload["status"], "active")
        self.assertNotIn("content", payload)
        self.assertNotIn("category_id", payload)

    @patch('requests.post')
    def test_create_message_with_category(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 102, "subject": "FYI", "category_id": "789"}
        mock_post.return_value = mock_response

        result = self.client.create_message("123", "456", "FYI", category_id="789")

        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["category_id"], "789")

    @patch('requests.post')
    def test_create_message_failure(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.text = "Unprocessable Entity"
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.create_message("123", "456", "Bad message")
        self.assertIn("422", str(ctx.exception))


class TestBasecampClientUpdateMessage(unittest.TestCase):
    """Test BasecampClient.update_message."""

    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token',
            account_id='12345',
            user_agent='Test Agent',
            auth_mode='oauth'
        )

    @patch('requests.put')
    def test_update_message_subject(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 100, "subject": "Updated Title"}
        mock_put.return_value = mock_response

        result = self.client.update_message("123", "100", subject="Updated Title")

        self.assertEqual(result["subject"], "Updated Title")
        self.assertIn("buckets/123/messages/100.json", mock_put.call_args[0][0])
        self.assertEqual(mock_put.call_args[1]["json"], {"subject": "Updated Title"})

    @patch('requests.put')
    def test_update_message_content(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 100, "content": "<p>New content</p>"}
        mock_put.return_value = mock_response

        result = self.client.update_message("123", "100", content="<p>New content</p>")

        self.assertEqual(result["content"], "<p>New content</p>")
        self.assertEqual(mock_put.call_args[1]["json"], {"content": "<p>New content</p>"})

    @patch('requests.put')
    def test_update_message_multiple_fields(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 100,
            "subject": "New Subject",
            "content": "<p>New body</p>",
            "category_id": "999",
        }
        mock_put.return_value = mock_response

        result = self.client.update_message(
            "123", "100", subject="New Subject", content="<p>New body</p>", category_id="999"
        )

        payload = mock_put.call_args[1]["json"]
        self.assertEqual(payload["subject"], "New Subject")
        self.assertEqual(payload["content"], "<p>New body</p>")
        self.assertEqual(payload["category_id"], "999")

    def test_update_message_no_fields(self):
        """Should raise ValueError when no fields are provided."""
        with self.assertRaises(ValueError) as ctx:
            self.client.update_message("123", "100")
        self.assertIn("No fields provided", str(ctx.exception))

    @patch('requests.put')
    def test_update_message_failure(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_put.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.update_message("123", "999", subject="X")
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


class TestFastMCPCreateMessage:
    @pytest.mark.anyio
    async def test_create_message_success(self, patch_auth):
        patch_auth.create_message.return_value = {
            "id": 100,
            "subject": "Kickoff",
            "content": "<p>Welcome!</p>",
        }
        from basecamp_fastmcp import create_message
        result = await create_message("123", "456", "Kickoff", content="<p>Welcome!</p>")
        assert result["status"] == "success"
        assert result["message"]["id"] == 100
        assert "created" in result["summary"].lower()

    @pytest.mark.anyio
    async def test_create_message_minimal(self, patch_auth):
        patch_auth.create_message.return_value = {"id": 101, "subject": "Note"}
        from basecamp_fastmcp import create_message
        result = await create_message("123", "456", "Note")
        assert result["status"] == "success"
        assert result["message"]["subject"] == "Note"

    @pytest.mark.anyio
    async def test_create_message_error(self, patch_auth):
        patch_auth.create_message.side_effect = Exception("API error")
        from basecamp_fastmcp import create_message
        result = await create_message("123", "456", "Fail")
        assert "error" in result
        assert "API error" in result["message"]

    @pytest.mark.anyio
    async def test_create_message_expired_token(self, patch_auth):
        patch_auth.create_message.side_effect = Exception("401 token expired")
        from basecamp_fastmcp import create_message
        result = await create_message("123", "456", "Fail")
        assert result["error"] == "OAuth token expired"

    @pytest.mark.anyio
    async def test_create_message_no_auth(self):
        with patch('basecamp_fastmcp._get_basecamp_client', return_value=None):
            with patch('basecamp_fastmcp.token_storage') as mock_ts:
                mock_ts.is_token_expired.return_value = True
                from basecamp_fastmcp import create_message
                result = await create_message("123", "456", "No auth")
                assert "error" in result


class TestFastMCPUpdateMessage:
    @pytest.mark.anyio
    async def test_update_message_success(self, patch_auth):
        patch_auth.update_message.return_value = {
            "id": 100,
            "subject": "Updated",
            "content": "<p>New</p>",
        }
        from basecamp_fastmcp import update_message
        result = await update_message("123", "100", subject="Updated", content="<p>New</p>")
        assert result["status"] == "success"
        assert result["message"]["subject"] == "Updated"
        assert "updated" in result["summary"].lower()

    @pytest.mark.anyio
    async def test_update_message_no_fields(self, patch_auth):
        from basecamp_fastmcp import update_message
        result = await update_message("123", "100")
        assert "error" in result
        assert "at least one field" in result["message"].lower()

    @pytest.mark.anyio
    async def test_update_message_error(self, patch_auth):
        patch_auth.update_message.side_effect = Exception("Not found")
        from basecamp_fastmcp import update_message
        result = await update_message("123", "999", subject="X")
        assert "error" in result
        assert "Not found" in result["message"]

    @pytest.mark.anyio
    async def test_update_message_expired_token(self, patch_auth):
        patch_auth.update_message.side_effect = Exception("401 token expired")
        from basecamp_fastmcp import update_message
        result = await update_message("123", "100", subject="X")
        assert result["error"] == "OAuth token expired"

    @pytest.mark.anyio
    async def test_update_message_no_auth(self):
        with patch('basecamp_fastmcp._get_basecamp_client', return_value=None):
            with patch('basecamp_fastmcp.token_storage') as mock_ts:
                mock_ts.is_token_expired.return_value = False
                from basecamp_fastmcp import update_message
                result = await update_message("123", "100", subject="No auth")
                assert "error" in result
                assert "auth" in result["error"].lower()


if __name__ == '__main__':
    unittest.main(verbosity=2)

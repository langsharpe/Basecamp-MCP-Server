"""Tests for native Basecamp search (client method + MCP tool)."""

import sys
import os
import unittest
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from basecamp_client import BasecampClient


# ---------------------------------------------------------------------------
# BasecampClient method tests
# ---------------------------------------------------------------------------

class TestBasecampClientSearch(unittest.TestCase):
    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token', account_id='12345',
            user_agent='Test Agent', auth_mode='oauth'
        )

    @patch('requests.get')
    def test_search_basic(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "title": "Design meeting", "type": "Todo"},
            {"id": 2, "title": "Design review", "type": "Message"},
        ]
        mock_get.return_value = mock_response

        result = self.client.search("design")
        self.assertEqual(len(result), 2)
        self.assertIn("search.json", mock_get.call_args[0][0])
        params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1] if len(mock_get.call_args[0]) > 1 else mock_get.call_args[1].get("params")
        self.assertEqual(params["q"], "design")

    @patch('requests.get')
    def test_search_with_filters(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "title": "Bug fix", "type": "Todo"}]
        mock_get.return_value = mock_response

        result = self.client.search("bug", type="Todo", bucket_id="123", creator_id="42")
        self.assertEqual(len(result), 1)
        params = mock_get.call_args[1].get("params")
        self.assertEqual(params["type"], "Todo")
        self.assertEqual(params["bucket_id"], "123")
        self.assertEqual(params["creator_id"], "42")

    @patch('requests.get')
    def test_search_exclude_chat(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        self.client.search("hello", exclude_chat=1)
        params = mock_get.call_args[1].get("params")
        self.assertEqual(params["exclude_chat"], 1)

    @patch('requests.get')
    def test_search_pagination(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        self.client.search("test", page=3, per_page=25)
        params = mock_get.call_args[1].get("params")
        self.assertEqual(params["page"], 3)
        self.assertEqual(params["per_page"], 25)

    @patch('requests.get')
    def test_search_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.search("fail")
        self.assertIn("500", str(ctx.exception))


# ---------------------------------------------------------------------------
# FastMCP tool wrapper tests
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    return Mock(spec=BasecampClient)


@pytest.fixture
def patch_auth(mock_client):
    with patch('basecamp_fastmcp._get_basecamp_client', return_value=mock_client):
        yield mock_client


class TestFastMCPNativeSearch:
    @pytest.mark.anyio
    async def test_search_success(self, patch_auth):
        patch_auth.search.return_value = [
            {"id": 1, "title": "Result 1", "type": "Todo"},
            {"id": 2, "title": "Result 2", "type": "Message"},
        ]
        from basecamp_fastmcp import native_search
        result = await native_search("test query")
        assert result["status"] == "success"
        assert result["count"] == 2
        assert result["query"] == "test query"

    @pytest.mark.anyio
    async def test_search_compact(self, patch_auth):
        patch_auth.search.return_value = [
            {"id": 1, "title": "Result", "type": "Todo", "app_url": "http://x", "extra": "data"}
        ]
        from basecamp_fastmcp import native_search
        result = await native_search("test", compact=True)
        assert result["status"] == "success"
        assert "extra" not in result["results"][0]

    @pytest.mark.anyio
    async def test_search_error(self, patch_auth):
        patch_auth.search.side_effect = Exception("API error")
        from basecamp_fastmcp import native_search
        result = await native_search("fail")
        assert "error" in result
        assert "API error" in result["message"]

    @pytest.mark.anyio
    async def test_search_expired_token(self, patch_auth):
        patch_auth.search.side_effect = Exception("401 token expired")
        from basecamp_fastmcp import native_search
        result = await native_search("fail")
        assert result["error"] == "OAuth token expired"

    @pytest.mark.anyio
    async def test_search_no_auth(self):
        with patch('basecamp_fastmcp._get_basecamp_client', return_value=None):
            with patch('basecamp_fastmcp.token_storage') as mock_ts:
                mock_ts.is_token_expired.return_value = False
                from basecamp_fastmcp import native_search
                result = await native_search("query")
                assert "error" in result


if __name__ == '__main__':
    unittest.main(verbosity=2)

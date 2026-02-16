"""Tests for people management tools (client methods + MCP tools)."""

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

class TestBasecampClientGetPerson(unittest.TestCase):
    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token', account_id='12345',
            user_agent='Test Agent', auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_person_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "Alice", "email_address": "alice@example.com"}
        mock_get.return_value = mock_response

        result = self.client.get_person("1")
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "Alice")
        self.assertIn("people/1.json", mock_get.call_args[0][0])

    @patch('requests.get')
    def test_get_person_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.get_person("999")
        self.assertIn("404", str(ctx.exception))


class TestBasecampClientGetMyProfile(unittest.TestCase):
    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token', account_id='12345',
            user_agent='Test Agent', auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_my_profile_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 42, "name": "Me", "email_address": "me@example.com"}
        mock_get.return_value = mock_response

        result = self.client.get_my_profile()
        self.assertEqual(result["id"], 42)
        self.assertIn("my/profile.json", mock_get.call_args[0][0])

    @patch('requests.get')
    def test_get_my_profile_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            self.client.get_my_profile()


class TestBasecampClientGetProjectPeople(unittest.TestCase):
    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token', account_id='12345',
            user_agent='Test Agent', auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_project_people_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        mock_get.return_value = mock_response

        result = self.client.get_project_people("123")
        self.assertEqual(len(result), 2)
        self.assertIn("projects/123/people.json", mock_get.call_args[0][0])

    @patch('requests.get')
    def test_get_project_people_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            self.client.get_project_people("999")


class TestBasecampClientUpdateProjectAccess(unittest.TestCase):
    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token', account_id='12345',
            user_agent='Test Agent', auth_mode='oauth'
        )

    @patch('requests.put')
    def test_grant_access(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"granted": [{"id": 5, "name": "New User"}], "revoked": []}
        mock_put.return_value = mock_response

        result = self.client.update_project_access("123", grant=["5"])
        self.assertEqual(len(result["granted"]), 1)
        self.assertIn("projects/123/people/users.json", mock_put.call_args[0][0])
        self.assertEqual(mock_put.call_args[1]["json"]["grant"], ["5"])

    @patch('requests.put')
    def test_revoke_access(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"granted": [], "revoked": [{"id": 5}]}
        mock_put.return_value = mock_response

        result = self.client.update_project_access("123", revoke=["5"])
        self.assertEqual(len(result["revoked"]), 1)

    def test_no_params_raises(self):
        with self.assertRaises(ValueError):
            self.client.update_project_access("123")

    @patch('requests.put')
    def test_failure(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_put.return_value = mock_response

        with self.assertRaises(Exception):
            self.client.update_project_access("123", grant=["5"])


class TestBasecampClientGetPingablePeople(unittest.TestCase):
    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token', account_id='12345',
            user_agent='Test Agent', auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_pingable_people_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        mock_get.return_value = mock_response

        result = self.client.get_pingable_people()
        self.assertEqual(len(result), 2)
        self.assertIn("circles/people.json", mock_get.call_args[0][0])


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


class TestFastMCPGetPerson:
    @pytest.mark.anyio
    async def test_success(self, patch_auth):
        patch_auth.get_person.return_value = {"id": 1, "name": "Alice"}
        from basecamp_fastmcp import get_person
        result = await get_person("123", "1")
        assert result["status"] == "success"
        assert result["person"]["name"] == "Alice"

    @pytest.mark.anyio
    async def test_error(self, patch_auth):
        patch_auth.get_person.side_effect = Exception("Not found")
        from basecamp_fastmcp import get_person
        result = await get_person("123", "999")
        assert "error" in result

    @pytest.mark.anyio
    async def test_no_auth(self):
        with patch('basecamp_fastmcp._get_basecamp_client', return_value=None):
            with patch('basecamp_fastmcp.token_storage') as mock_ts:
                mock_ts.is_token_expired.return_value = True
                from basecamp_fastmcp import get_person
                result = await get_person("123", "1")
                assert "error" in result


class TestFastMCPGetMyProfile:
    @pytest.mark.anyio
    async def test_success(self, patch_auth):
        patch_auth.get_my_profile.return_value = {"id": 42, "name": "Me"}
        from basecamp_fastmcp import get_my_profile
        result = await get_my_profile()
        assert result["status"] == "success"
        assert result["person"]["id"] == 42

    @pytest.mark.anyio
    async def test_expired_token(self, patch_auth):
        patch_auth.get_my_profile.side_effect = Exception("401 token expired")
        from basecamp_fastmcp import get_my_profile
        result = await get_my_profile()
        assert result["error"] == "OAuth token expired"


class TestFastMCPGetProjectPeople:
    @pytest.mark.anyio
    async def test_success(self, patch_auth):
        patch_auth.get_project_people.return_value = [{"id": 1, "name": "Alice"}]
        from basecamp_fastmcp import get_project_people
        result = await get_project_people("123")
        assert result["status"] == "success"
        assert result["count"] == 1

    @pytest.mark.anyio
    async def test_compact(self, patch_auth):
        patch_auth.get_project_people.return_value = [
            {"id": 1, "name": "Alice", "email_address": "a@b.com", "extra": "field"}
        ]
        from basecamp_fastmcp import get_project_people
        result = await get_project_people("123", compact=True)
        assert result["status"] == "success"
        assert "extra" not in result["people"][0]


class TestFastMCPUpdateProjectAccess:
    @pytest.mark.anyio
    async def test_success(self, patch_auth):
        patch_auth.update_project_access.return_value = {"granted": [{"id": 5}], "revoked": []}
        from basecamp_fastmcp import update_project_access
        result = await update_project_access("123", grant=["5"])
        assert result["status"] == "success"

    @pytest.mark.anyio
    async def test_no_params(self, patch_auth):
        from basecamp_fastmcp import update_project_access
        result = await update_project_access("123")
        assert "error" in result
        assert "at least one" in result["message"].lower()


class TestFastMCPGetPingablePeople:
    @pytest.mark.anyio
    async def test_success(self, patch_auth):
        patch_auth.get_pingable_people.return_value = [{"id": 1, "name": "Alice"}]
        from basecamp_fastmcp import get_pingable_people
        result = await get_pingable_people()
        assert result["status"] == "success"
        assert result["count"] == 1


if __name__ == '__main__':
    unittest.main(verbosity=2)

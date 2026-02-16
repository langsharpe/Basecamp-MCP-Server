"""Tests for newly added MCP tool wrappers and their BasecampClient methods.

Covers: get_people, get_campfires, get_schedule, get_schedule_entries,
        get_comment, update_comment, delete_comment, get_todoset, get_todolist
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, AsyncMock

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from basecamp_client import BasecampClient
from compact_response import compact_item, compact_list


# ---------------------------------------------------------------------------
# BasecampClient method tests (sync, using mocked requests)
# ---------------------------------------------------------------------------

class TestBasecampClientPeople(unittest.TestCase):
    """Test BasecampClient.get_people."""

    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token',
            account_id='12345',
            user_agent='Test Agent',
            auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_people_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "name": "Alice", "email_address": "alice@example.com"},
            {"id": 2, "name": "Bob", "email_address": "bob@example.com"},
        ]
        mock_get.return_value = mock_response

        result = self.client.get_people()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Alice")
        mock_get.assert_called_once()
        self.assertIn("people.json", mock_get.call_args[0][0])

    @patch('requests.get')
    def test_get_people_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.get_people()
        self.assertIn("403", str(ctx.exception))


class TestBasecampClientCampfires(unittest.TestCase):
    """Test BasecampClient.get_campfires."""

    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token',
            account_id='12345',
            user_agent='Test Agent',
            auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_campfires_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 10, "title": "General Chat", "app_url": "https://example.com/chat"}
        ]
        mock_get.return_value = mock_response

        result = self.client.get_campfires("123")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "General Chat")
        self.assertIn("buckets/123/chats.json", mock_get.call_args[0][0])

    @patch('requests.get')
    def test_get_campfires_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.get_campfires("999")
        self.assertIn("404", str(ctx.exception))


class TestBasecampClientSchedule(unittest.TestCase):
    """Test BasecampClient.get_schedule and get_schedule_entries."""

    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token',
            account_id='12345',
            user_agent='Test Agent',
            auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_schedule_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 55,
            "title": "Schedule",
            "entries_count": 3,
        }
        mock_get.return_value = mock_response

        result = self.client.get_schedule("123")

        self.assertEqual(result["id"], 55)
        self.assertIn("projects/123/schedule.json", mock_get.call_args[0][0])

    @patch('requests.get')
    def test_get_schedule_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.get_schedule("123")
        self.assertIn("500", str(ctx.exception))


class TestBasecampClientComment(unittest.TestCase):
    """Test BasecampClient get_comment, update_comment, delete_comment."""

    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token',
            account_id='12345',
            user_agent='Test Agent',
            auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_comment_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 77,
            "content": "<p>Great work!</p>",
            "creator": {"id": 1, "name": "Alice"},
        }
        mock_get.return_value = mock_response

        result = self.client.get_comment("77", "123")

        self.assertEqual(result["id"], 77)
        self.assertIn("buckets/123/comments/77.json", mock_get.call_args[0][0])

    @patch('requests.get')
    def test_get_comment_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.get_comment("99", "123")
        self.assertIn("404", str(ctx.exception))

    @patch('requests.put')
    def test_update_comment_success(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 77,
            "content": "<p>Updated content</p>",
        }
        mock_put.return_value = mock_response

        result = self.client.update_comment("77", "123", "<p>Updated content</p>")

        self.assertEqual(result["content"], "<p>Updated content</p>")
        self.assertIn("buckets/123/comments/77.json", mock_put.call_args[0][0])
        self.assertEqual(mock_put.call_args[1]["json"], {"content": "<p>Updated content</p>"})

    @patch('requests.put')
    def test_update_comment_failure(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.text = "Unprocessable"
        mock_put.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.update_comment("77", "123", "")
        self.assertIn("422", str(ctx.exception))

    @patch('requests.delete')
    def test_delete_comment_success(self, mock_delete):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        result = self.client.delete_comment("77", "123")

        self.assertTrue(result)
        self.assertIn("buckets/123/comments/77.json", mock_delete.call_args[0][0])

    @patch('requests.delete')
    def test_delete_comment_failure(self, mock_delete):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_delete.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.delete_comment("99", "123")
        self.assertIn("404", str(ctx.exception))


class TestBasecampClientTodoset(unittest.TestCase):
    """Test BasecampClient.get_todoset."""

    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token',
            account_id='12345',
            user_agent='Test Agent',
            auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_todoset_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123",
            "dock": [
                {"name": "todoset", "id": "444"},
                {"name": "message_board", "id": "555"},
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.get_todoset("123")

        self.assertEqual(result["name"], "todoset")
        self.assertEqual(result["id"], "444")

    @patch('requests.get')
    def test_get_todoset_no_todoset_in_dock(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123",
            "dock": [
                {"name": "message_board", "id": "555"},
            ]
        }
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            self.client.get_todoset("123")


class TestBasecampClientTodolist(unittest.TestCase):
    """Test BasecampClient.get_todolist."""

    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token',
            account_id='12345',
            user_agent='Test Agent',
            auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_todolist_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "888",
            "title": "Sprint Backlog",
            "completed": False,
            "todos_url": "https://example.com/todos",
        }
        mock_get.return_value = mock_response

        result = self.client.get_todolist("888")

        self.assertEqual(result["title"], "Sprint Backlog")
        self.assertIn("todolists/888.json", mock_get.call_args[0][0])

    @patch('requests.get')
    def test_get_todolist_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.client.get_todolist("999")
        self.assertIn("404", str(ctx.exception))


# ---------------------------------------------------------------------------
# Compact response tests for new types (person, campfire, schedule_entry)
# ---------------------------------------------------------------------------

class TestCompactPerson:
    def test_person_compact(self):
        person = {
            "id": 1,
            "name": "Alice",
            "email_address": "alice@example.com",
            "admin": True,
            "avatar_url": "https://example.com/avatar.png",
            "created_at": "2025-01-01T00:00:00Z",
            "company": {"id": 10, "name": "Acme"},
            "time_zone": "America/Chicago",
        }
        result = compact_item(person, "person")
        assert result == {
            "id": 1,
            "name": "Alice",
            "email_address": "alice@example.com",
            "admin": True,
            "avatar_url": "https://example.com/avatar.png",
        }

    def test_person_missing_optional_fields(self):
        person = {"id": 2, "name": "Bob"}
        result = compact_item(person, "person")
        assert result == {"id": 2, "name": "Bob"}

    def test_person_list(self):
        people = [
            {"id": 1, "name": "Alice", "email_address": "a@e.com", "admin": True, "extra": "data"},
            {"id": 2, "name": "Bob", "email_address": "b@e.com", "admin": False, "extra": "data"},
        ]
        result = compact_list(people, "person")
        assert len(result) == 2
        assert result[0] == {"id": 1, "name": "Alice", "email_address": "a@e.com", "admin": True}
        assert result[1] == {"id": 2, "name": "Bob", "email_address": "b@e.com", "admin": False}


class TestCompactCampfire:
    def test_campfire_compact(self):
        campfire = {
            "id": 10,
            "title": "General Chat",
            "app_url": "https://example.com/chat/10",
            "created_at": "2025-01-01T00:00:00Z",
            "lines_url": "https://example.com/lines",
            "topic": "General",
        }
        result = compact_item(campfire, "campfire")
        assert result == {
            "id": 10,
            "title": "General Chat",
            "app_url": "https://example.com/chat/10",
        }

    def test_campfire_minimal(self):
        campfire = {"id": 5}
        result = compact_item(campfire, "campfire")
        assert result == {"id": 5}


class TestCompactScheduleEntry:
    def test_schedule_entry_compact(self):
        entry = {
            "id": 30,
            "title": "Team Standup",
            "starts_at": "2026-03-01T09:00:00Z",
            "ends_at": "2026-03-01T09:30:00Z",
            "all_day": False,
            "app_url": "https://example.com/schedule/30",
            "description": "Daily sync meeting",
            "creator": {"id": 1, "name": "Alice"},
            "bucket": {"id": 1, "name": "Project"},
        }
        result = compact_item(entry, "schedule_entry")
        assert result == {
            "id": 30,
            "title": "Team Standup",
            "starts_at": "2026-03-01T09:00:00Z",
            "ends_at": "2026-03-01T09:30:00Z",
            "all_day": False,
            "app_url": "https://example.com/schedule/30",
        }

    def test_schedule_entry_all_day(self):
        entry = {
            "id": 31,
            "title": "Company Holiday",
            "starts_at": "2026-12-25",
            "ends_at": "2026-12-25",
            "all_day": True,
            "app_url": "https://example.com/schedule/31",
        }
        result = compact_item(entry, "schedule_entry")
        assert result["all_day"] is True

    def test_schedule_entry_list(self):
        entries = [
            {"id": 1, "title": "A", "starts_at": "x", "ends_at": "y", "all_day": False, "extra": "z"},
            {"id": 2, "title": "B", "starts_at": "x", "ends_at": "y", "all_day": True, "extra": "z"},
        ]
        result = compact_list(entries, "schedule_entry")
        assert len(result) == 2
        assert "extra" not in result[0]
        assert "extra" not in result[1]


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


class TestFastMCPGetPeople:
    @pytest.mark.anyio
    async def test_get_people_success(self, patch_auth):
        patch_auth.get_people.return_value = [
            {"id": 1, "name": "Alice", "email_address": "a@e.com"},
            {"id": 2, "name": "Bob", "email_address": "b@e.com"},
        ]
        from basecamp_fastmcp import get_people
        result = await get_people()
        assert result["status"] == "success"
        assert result["count"] == 2
        assert len(result["people"]) == 2

    @pytest.mark.anyio
    async def test_get_people_compact(self, patch_auth):
        patch_auth.get_people.return_value = [
            {"id": 1, "name": "Alice", "email_address": "a@e.com", "admin": True, "extra": "x"},
        ]
        from basecamp_fastmcp import get_people
        result = await get_people(compact=True)
        assert result["status"] == "success"
        assert "extra" not in result["people"][0]
        assert result["people"][0]["name"] == "Alice"

    @pytest.mark.anyio
    async def test_get_people_error(self, patch_auth):
        patch_auth.get_people.side_effect = Exception("Network error")
        from basecamp_fastmcp import get_people
        result = await get_people()
        assert "error" in result
        assert "Network error" in result["message"]


class TestFastMCPGetCampfires:
    @pytest.mark.anyio
    async def test_get_campfires_success(self, patch_auth):
        patch_auth.get_campfires.return_value = [
            {"id": 10, "title": "Chat", "app_url": "https://example.com"}
        ]
        from basecamp_fastmcp import get_campfires
        result = await get_campfires("123")
        assert result["status"] == "success"
        assert result["count"] == 1

    @pytest.mark.anyio
    async def test_get_campfires_compact(self, patch_auth):
        patch_auth.get_campfires.return_value = [
            {"id": 10, "title": "Chat", "app_url": "https://example.com", "extra": "data"}
        ]
        from basecamp_fastmcp import get_campfires
        result = await get_campfires("123", compact=True)
        assert "extra" not in result["campfires"][0]

    @pytest.mark.anyio
    async def test_get_campfires_error(self, patch_auth):
        patch_auth.get_campfires.side_effect = Exception("fail")
        from basecamp_fastmcp import get_campfires
        result = await get_campfires("123")
        assert "error" in result


class TestFastMCPGetSchedule:
    @pytest.mark.anyio
    async def test_get_schedule_success(self, patch_auth):
        patch_auth.get_schedule.return_value = {"id": 55, "title": "Schedule"}
        from basecamp_fastmcp import get_schedule
        result = await get_schedule("123")
        assert result["status"] == "success"
        assert result["schedule"]["id"] == 55

    @pytest.mark.anyio
    async def test_get_schedule_error(self, patch_auth):
        patch_auth.get_schedule.side_effect = Exception("fail")
        from basecamp_fastmcp import get_schedule
        result = await get_schedule("123")
        assert "error" in result


class TestFastMCPGetScheduleEntries:
    @pytest.mark.anyio
    async def test_get_schedule_entries_success(self, patch_auth):
        patch_auth.get_schedule_entries.return_value = [
            {"id": 1, "title": "Standup", "starts_at": "2026-03-01", "ends_at": "2026-03-01"}
        ]
        from basecamp_fastmcp import get_schedule_entries
        result = await get_schedule_entries("123")
        assert result["status"] == "success"
        assert result["count"] == 1

    @pytest.mark.anyio
    async def test_get_schedule_entries_compact(self, patch_auth):
        patch_auth.get_schedule_entries.return_value = [
            {"id": 1, "title": "Standup", "starts_at": "x", "ends_at": "y", "all_day": False, "extra": "z"}
        ]
        from basecamp_fastmcp import get_schedule_entries
        result = await get_schedule_entries("123", compact=True)
        assert "extra" not in result["schedule_entries"][0]

    @pytest.mark.anyio
    async def test_get_schedule_entries_error(self, patch_auth):
        patch_auth.get_schedule_entries.side_effect = Exception("fail")
        from basecamp_fastmcp import get_schedule_entries
        result = await get_schedule_entries("123")
        assert "error" in result


class TestFastMCPGetComment:
    @pytest.mark.anyio
    async def test_get_comment_success(self, patch_auth):
        patch_auth.get_comment.return_value = {"id": 77, "content": "<p>Nice!</p>"}
        from basecamp_fastmcp import get_comment
        result = await get_comment("123", "77")
        assert result["status"] == "success"
        assert result["comment"]["id"] == 77

    @pytest.mark.anyio
    async def test_get_comment_error(self, patch_auth):
        patch_auth.get_comment.side_effect = Exception("Not found")
        from basecamp_fastmcp import get_comment
        result = await get_comment("123", "99")
        assert "error" in result


class TestFastMCPUpdateComment:
    @pytest.mark.anyio
    async def test_update_comment_success(self, patch_auth):
        patch_auth.update_comment.return_value = {"id": 77, "content": "<p>Updated</p>"}
        from basecamp_fastmcp import update_comment
        result = await update_comment("123", "77", "<p>Updated</p>")
        assert result["status"] == "success"
        assert "updated" in result["message"].lower()

    @pytest.mark.anyio
    async def test_update_comment_error(self, patch_auth):
        patch_auth.update_comment.side_effect = Exception("fail")
        from basecamp_fastmcp import update_comment
        result = await update_comment("123", "77", "x")
        assert "error" in result


class TestFastMCPDeleteComment:
    @pytest.mark.anyio
    async def test_delete_comment_success(self, patch_auth):
        patch_auth.delete_comment.return_value = True
        from basecamp_fastmcp import delete_comment
        result = await delete_comment("123", "77")
        assert result["status"] == "success"
        assert "deleted" in result["message"].lower()

    @pytest.mark.anyio
    async def test_delete_comment_error(self, patch_auth):
        patch_auth.delete_comment.side_effect = Exception("fail")
        from basecamp_fastmcp import delete_comment
        result = await delete_comment("123", "77")
        assert "error" in result


class TestFastMCPGetTodoset:
    @pytest.mark.anyio
    async def test_get_todoset_success(self, patch_auth):
        patch_auth.get_todoset.return_value = {"name": "todoset", "id": "444"}
        from basecamp_fastmcp import get_todoset
        result = await get_todoset("123")
        assert result["status"] == "success"
        assert result["todoset"]["id"] == "444"

    @pytest.mark.anyio
    async def test_get_todoset_error(self, patch_auth):
        patch_auth.get_todoset.side_effect = Exception("No todoset")
        from basecamp_fastmcp import get_todoset
        result = await get_todoset("123")
        assert "error" in result


class TestFastMCPGetTodolist:
    @pytest.mark.anyio
    async def test_get_todolist_success(self, patch_auth):
        patch_auth.get_todolist.return_value = {"id": "888", "title": "Sprint Backlog"}
        from basecamp_fastmcp import get_todolist
        result = await get_todolist("123", "888")
        assert result["status"] == "success"
        assert result["todolist"]["title"] == "Sprint Backlog"

    @pytest.mark.anyio
    async def test_get_todolist_error(self, patch_auth):
        patch_auth.get_todolist.side_effect = Exception("Not found")
        from basecamp_fastmcp import get_todolist
        result = await get_todolist("123", "999")
        assert "error" in result


class TestFastMCPAuthErrors:
    """Test that unauthenticated calls return proper error responses."""

    @pytest.mark.anyio
    async def test_get_people_no_auth(self):
        with patch('basecamp_fastmcp._get_basecamp_client', return_value=None):
            with patch('basecamp_fastmcp.token_storage') as mock_ts:
                mock_ts.is_token_expired.return_value = True
                from basecamp_fastmcp import get_people
                result = await get_people()
                assert "error" in result
                assert "expired" in result["error"].lower() or "auth" in result["error"].lower()

    @pytest.mark.anyio
    async def test_get_campfires_no_auth(self):
        with patch('basecamp_fastmcp._get_basecamp_client', return_value=None):
            with patch('basecamp_fastmcp.token_storage') as mock_ts:
                mock_ts.is_token_expired.return_value = False
                from basecamp_fastmcp import get_campfires
                result = await get_campfires("123")
                assert "error" in result
                assert "auth" in result["error"].lower()

    @pytest.mark.anyio
    async def test_get_todolist_expired_token(self):
        with patch('basecamp_fastmcp._get_basecamp_client', return_value=None):
            with patch('basecamp_fastmcp.token_storage') as mock_ts:
                mock_ts.is_token_expired.return_value = True
                from basecamp_fastmcp import get_todolist
                result = await get_todolist("123", "456")
                assert "expired" in result["error"].lower()


if __name__ == '__main__':
    unittest.main(verbosity=2)

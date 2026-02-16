"""Tests for todolist CRUD, groups, and todo repositioning (client methods + MCP tools)."""

import sys
import os
import unittest
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from basecamp_client import BasecampClient


# ---------------------------------------------------------------------------
# BasecampClient — Todolist CRUD
# ---------------------------------------------------------------------------

class TestBasecampClientCreateTodolist(unittest.TestCase):
    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token', account_id='12345',
            user_agent='Test Agent', auth_mode='oauth'
        )

    @patch('requests.post')
    @patch('requests.get')
    def test_create_todolist_success(self, mock_get, mock_post):
        # Mock get_project -> get_todoset
        project_resp = Mock()
        project_resp.status_code = 200
        project_resp.json.return_value = {
            "id": 123,
            "dock": [{"name": "todoset", "id": 456}]
        }
        mock_get.return_value = project_resp

        post_resp = Mock()
        post_resp.status_code = 201
        post_resp.json.return_value = {"id": 789, "name": "Sprint Backlog"}
        mock_post.return_value = post_resp

        result = self.client.create_todolist("123", "Sprint Backlog")
        self.assertEqual(result["id"], 789)
        self.assertEqual(result["name"], "Sprint Backlog")
        self.assertIn("buckets/123/todosets/456/todolists.json", mock_post.call_args[0][0])

    @patch('requests.post')
    @patch('requests.get')
    def test_create_todolist_with_description(self, mock_get, mock_post):
        project_resp = Mock()
        project_resp.status_code = 200
        project_resp.json.return_value = {"id": 123, "dock": [{"name": "todoset", "id": 456}]}
        mock_get.return_value = project_resp

        post_resp = Mock()
        post_resp.status_code = 201
        post_resp.json.return_value = {"id": 789, "name": "List", "description": "<p>Desc</p>"}
        mock_post.return_value = post_resp

        result = self.client.create_todolist("123", "List", description="<p>Desc</p>")
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["name"], "List")
        self.assertEqual(payload["description"], "<p>Desc</p>")

    @patch('requests.post')
    @patch('requests.get')
    def test_create_todolist_failure(self, mock_get, mock_post):
        project_resp = Mock()
        project_resp.status_code = 200
        project_resp.json.return_value = {"id": 123, "dock": [{"name": "todoset", "id": 456}]}
        mock_get.return_value = project_resp

        post_resp = Mock()
        post_resp.status_code = 422
        post_resp.text = "Unprocessable"
        mock_post.return_value = post_resp

        with self.assertRaises(Exception) as ctx:
            self.client.create_todolist("123", "Bad")
        self.assertIn("422", str(ctx.exception))


class TestBasecampClientUpdateTodolist(unittest.TestCase):
    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token', account_id='12345',
            user_agent='Test Agent', auth_mode='oauth'
        )

    @patch('requests.put')
    def test_update_todolist_success(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 789, "name": "Updated Name"}
        mock_put.return_value = mock_response

        result = self.client.update_todolist("123", "789", "Updated Name")
        self.assertEqual(result["name"], "Updated Name")
        self.assertIn("buckets/123/todolists/789.json", mock_put.call_args[0][0])

    @patch('requests.put')
    def test_update_todolist_with_description(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 789, "name": "N", "description": "<p>D</p>"}
        mock_put.return_value = mock_response

        self.client.update_todolist("123", "789", "N", description="<p>D</p>")
        payload = mock_put.call_args[1]["json"]
        self.assertEqual(payload["description"], "<p>D</p>")

    @patch('requests.put')
    def test_update_todolist_failure(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_put.return_value = mock_response

        with self.assertRaises(Exception):
            self.client.update_todolist("123", "999", "X")


class TestBasecampClientTrashTodolist(unittest.TestCase):
    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token', account_id='12345',
            user_agent='Test Agent', auth_mode='oauth'
        )

    @patch('requests.put')
    def test_trash_todolist_success(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        result = self.client.trash_todolist("123", "789")
        self.assertTrue(result)
        self.assertIn("buckets/123/recordings/789/status/trashed.json", mock_put.call_args[0][0])

    @patch('requests.put')
    def test_trash_todolist_failure(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_put.return_value = mock_response

        with self.assertRaises(Exception):
            self.client.trash_todolist("123", "999")


# ---------------------------------------------------------------------------
# BasecampClient — Todolist Groups
# ---------------------------------------------------------------------------

class TestBasecampClientTodolistGroups(unittest.TestCase):
    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token', account_id='12345',
            user_agent='Test Agent', auth_mode='oauth'
        )

    @patch('requests.get')
    def test_get_groups(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "title": "Group A"},
            {"id": 2, "title": "Group B"},
        ]
        mock_get.return_value = mock_response

        result = self.client.get_todolist_groups("123", "456")
        self.assertEqual(len(result), 2)
        self.assertIn("buckets/123/todolists/456/groups.json", mock_get.call_args[0][0])

    @patch('requests.get')
    def test_get_groups_with_status(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        self.client.get_todolist_groups("123", "456", status="archived")
        params = mock_get.call_args[1].get("params")
        self.assertEqual(params["status"], "archived")

    @patch('requests.post')
    def test_create_group(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 10, "title": "Phase 1"}
        mock_post.return_value = mock_response

        result = self.client.create_todolist_group("123", "456", "Phase 1")
        self.assertEqual(result["title"], "Phase 1")
        self.assertIn("buckets/123/todolists/456/groups.json", mock_post.call_args[0][0])
        self.assertEqual(mock_post.call_args[1]["json"]["name"], "Phase 1")

    @patch('requests.post')
    def test_create_group_with_color(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 10, "title": "Phase 1", "color": "blue"}
        mock_post.return_value = mock_response

        self.client.create_todolist_group("123", "456", "Phase 1", color="blue")
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["color"], "blue")

    @patch('requests.put')
    def test_reposition_group(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        result = self.client.reposition_todolist_group("123", "10", 3)
        self.assertTrue(result)
        self.assertIn("buckets/123/todolists/groups/10/position.json", mock_put.call_args[0][0])
        self.assertEqual(mock_put.call_args[1]["json"]["position"], 3)

    @patch('requests.put')
    def test_reposition_group_failure(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_put.return_value = mock_response

        with self.assertRaises(Exception):
            self.client.reposition_todolist_group("123", "999", 1)


# ---------------------------------------------------------------------------
# BasecampClient — Todo Repositioning
# ---------------------------------------------------------------------------

class TestBasecampClientRepositionTodo(unittest.TestCase):
    def setUp(self):
        self.client = BasecampClient(
            access_token='test_token', account_id='12345',
            user_agent='Test Agent', auth_mode='oauth'
        )

    @patch('requests.put')
    def test_reposition_todo(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        result = self.client.reposition_todo("123", "50", 2)
        self.assertTrue(result)
        self.assertIn("buckets/123/todos/50/position.json", mock_put.call_args[0][0])
        self.assertEqual(mock_put.call_args[1]["json"]["position"], 2)

    @patch('requests.put')
    def test_reposition_todo_with_parent(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        self.client.reposition_todo("123", "50", 1, parent_id="99")
        payload = mock_put.call_args[1]["json"]
        self.assertEqual(payload["position"], 1)
        self.assertEqual(payload["parent_id"], "99")

    @patch('requests.put')
    def test_reposition_todo_failure(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_put.return_value = mock_response

        with self.assertRaises(Exception):
            self.client.reposition_todo("123", "999", 1)


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


class TestFastMCPCreateTodolist:
    @pytest.mark.anyio
    async def test_success(self, patch_auth):
        patch_auth.create_todolist.return_value = {"id": 789, "name": "Sprint Backlog"}
        from basecamp_fastmcp import create_todolist
        result = await create_todolist("123", "Sprint Backlog")
        assert result["status"] == "success"
        assert result["todolist"]["name"] == "Sprint Backlog"
        assert "created" in result["message"].lower()

    @pytest.mark.anyio
    async def test_error(self, patch_auth):
        patch_auth.create_todolist.side_effect = Exception("Failed")
        from basecamp_fastmcp import create_todolist
        result = await create_todolist("123", "Bad")
        assert "error" in result

    @pytest.mark.anyio
    async def test_expired_token(self, patch_auth):
        patch_auth.create_todolist.side_effect = Exception("401 token expired")
        from basecamp_fastmcp import create_todolist
        result = await create_todolist("123", "X")
        assert result["error"] == "OAuth token expired"


class TestFastMCPUpdateTodolist:
    @pytest.mark.anyio
    async def test_success(self, patch_auth):
        patch_auth.update_todolist.return_value = {"id": 789, "name": "Updated"}
        from basecamp_fastmcp import update_todolist
        result = await update_todolist("123", "789", "Updated")
        assert result["status"] == "success"
        assert result["todolist"]["name"] == "Updated"

    @pytest.mark.anyio
    async def test_error(self, patch_auth):
        patch_auth.update_todolist.side_effect = Exception("Not found")
        from basecamp_fastmcp import update_todolist
        result = await update_todolist("123", "999", "X")
        assert "error" in result


class TestFastMCPTrashTodolist:
    @pytest.mark.anyio
    async def test_success(self, patch_auth):
        patch_auth.trash_todolist.return_value = True
        from basecamp_fastmcp import trash_todolist
        result = await trash_todolist("123", "789")
        assert result["status"] == "success"
        assert "trashed" in result["message"].lower()

    @pytest.mark.anyio
    async def test_error(self, patch_auth):
        patch_auth.trash_todolist.side_effect = Exception("Not found")
        from basecamp_fastmcp import trash_todolist
        result = await trash_todolist("123", "999")
        assert "error" in result


class TestFastMCPTodolistGroups:
    @pytest.mark.anyio
    async def test_get_groups(self, patch_auth):
        patch_auth.get_todolist_groups.return_value = [{"id": 1, "title": "Group A"}]
        from basecamp_fastmcp import get_todolist_groups
        result = await get_todolist_groups("123", "456")
        assert result["status"] == "success"
        assert result["count"] == 1

    @pytest.mark.anyio
    async def test_create_group(self, patch_auth):
        patch_auth.create_todolist_group.return_value = {"id": 10, "title": "Phase 1"}
        from basecamp_fastmcp import create_todolist_group
        result = await create_todolist_group("123", "456", "Phase 1")
        assert result["status"] == "success"
        assert "created" in result["message"].lower()

    @pytest.mark.anyio
    async def test_create_group_with_color(self, patch_auth):
        patch_auth.create_todolist_group.return_value = {"id": 10, "title": "P1", "color": "blue"}
        from basecamp_fastmcp import create_todolist_group
        result = await create_todolist_group("123", "456", "P1", color="blue")
        assert result["status"] == "success"

    @pytest.mark.anyio
    async def test_reposition_group(self, patch_auth):
        patch_auth.reposition_todolist_group.return_value = True
        from basecamp_fastmcp import reposition_todolist_group
        result = await reposition_todolist_group("123", "10", 3)
        assert result["status"] == "success"
        assert "3" in result["message"]


class TestFastMCPRepositionTodo:
    @pytest.mark.anyio
    async def test_reposition(self, patch_auth):
        patch_auth.reposition_todo.return_value = True
        from basecamp_fastmcp import reposition_todo
        result = await reposition_todo("123", "50", 2)
        assert result["status"] == "success"
        assert "2" in result["message"]

    @pytest.mark.anyio
    async def test_reposition_with_parent(self, patch_auth):
        patch_auth.reposition_todo.return_value = True
        from basecamp_fastmcp import reposition_todo
        result = await reposition_todo("123", "50", 1, parent_id="99")
        assert result["status"] == "success"
        assert "99" in result["message"]

    @pytest.mark.anyio
    async def test_reposition_error(self, patch_auth):
        patch_auth.reposition_todo.side_effect = Exception("Not found")
        from basecamp_fastmcp import reposition_todo
        result = await reposition_todo("123", "999", 1)
        assert "error" in result

    @pytest.mark.anyio
    async def test_no_auth(self):
        with patch('basecamp_fastmcp._get_basecamp_client', return_value=None):
            with patch('basecamp_fastmcp.token_storage') as mock_ts:
                mock_ts.is_token_expired.return_value = False
                from basecamp_fastmcp import reposition_todo
                result = await reposition_todo("123", "50", 1)
                assert "error" in result


if __name__ == '__main__':
    unittest.main(verbosity=2)

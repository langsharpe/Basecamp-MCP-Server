"""Tests for compact_response module."""

import pytest
from compact_response import compact_item, compact_list, _extract_assignee_names, _extract_creator_name


# --- Sample data fixtures ---

FULL_CARD = {
    "id": 123,
    "title": "Fix login bug",
    "content": "<p>Long HTML description here...</p>",
    "completed": False,
    "due_on": "2026-03-01",
    "app_url": "https://3.basecamp.com/999/buckets/1/cards/123",
    "status": "active",
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-02-10T14:30:00Z",
    "creator": {"id": 10, "name": "Alice", "email_address": "alice@example.com"},
    "bucket": {"id": 1, "name": "Project Alpha", "type": "Project"},
    "parent": {"id": 50, "title": "Backlog", "type": "Kanban::Column"},
    "assignees": [
        {"id": 10, "name": "Alice", "email_address": "alice@example.com"},
        {"id": 20, "name": "Bob", "email_address": "bob@example.com"},
    ],
    "comments_count": 5,
    "steps_count": 3,
}

FULL_TODO = {
    "id": 456,
    "title": "Write tests",
    "content": "<p>Unit and integration tests</p>",
    "completed": True,
    "due_on": "2026-02-28",
    "app_url": "https://3.basecamp.com/999/buckets/1/todos/456",
    "status": "active",
    "creator": {"id": 10, "name": "Alice"},
    "assignees": [{"id": 20, "name": "Bob"}],
}

FULL_MESSAGE = {
    "id": 789,
    "subject": "Weekly Update",
    "content": "<h1>This week</h1><p>Lots of progress...</p>",
    "created_at": "2026-02-01T09:00:00Z",
    "app_url": "https://3.basecamp.com/999/buckets/1/messages/789",
    "creator": {"id": 10, "name": "Alice", "email_address": "alice@example.com"},
    "bucket": {"id": 1, "name": "Project Alpha"},
}

FULL_COMMENT = {
    "id": 321,
    "content": "<p>Looks good to me!</p>",
    "created_at": "2026-02-05T11:00:00Z",
    "app_url": "https://3.basecamp.com/999/buckets/1/comments/321",
    "creator": {"id": 20, "name": "Bob"},
}

FULL_PROJECT = {
    "id": 1,
    "name": "Project Alpha",
    "description": "Our main project",
    "app_url": "https://3.basecamp.com/999/projects/1",
    "status": "active",
    "created_at": "2025-01-01T00:00:00Z",
    "dock": [{"id": 100, "name": "message_board"}],
    "purpose": "topic",
}


# --- compact_item tests ---

class TestCompactItem:
    def test_card(self):
        result = compact_item(FULL_CARD, "card")
        assert result == {
            "id": 123,
            "title": "Fix login bug",
            "completed": False,
            "due_on": "2026-03-01",
            "app_url": "https://3.basecamp.com/999/buckets/1/cards/123",
            "assignee_names": ["Alice", "Bob"],
        }

    def test_todo(self):
        result = compact_item(FULL_TODO, "todo")
        assert result == {
            "id": 456,
            "title": "Write tests",
            "completed": True,
            "due_on": "2026-02-28",
            "app_url": "https://3.basecamp.com/999/buckets/1/todos/456",
            "assignee_names": ["Bob"],
        }

    def test_message(self):
        result = compact_item(FULL_MESSAGE, "message")
        assert result == {
            "id": 789,
            "subject": "Weekly Update",
            "created_at": "2026-02-01T09:00:00Z",
            "app_url": "https://3.basecamp.com/999/buckets/1/messages/789",
            "creator_name": "Alice",
        }

    def test_comment(self):
        result = compact_item(FULL_COMMENT, "comment")
        assert result == {
            "id": 321,
            "created_at": "2026-02-05T11:00:00Z",
            "app_url": "https://3.basecamp.com/999/buckets/1/comments/321",
            "creator_name": "Bob",
            "content": "<p>Looks good to me!</p>",
        }

    def test_project(self):
        result = compact_item(FULL_PROJECT, "project")
        assert result == {
            "id": 1,
            "name": "Project Alpha",
            "description": "Our main project",
            "app_url": "https://3.basecamp.com/999/projects/1",
        }

    def test_unknown_resource_type(self):
        result = compact_item({"id": 1, "title": "test", "extra": "data"}, "unknown_type")
        assert result == {}

    def test_non_dict_input(self):
        assert compact_item("not a dict", "card") == "not a dict"

    def test_missing_fields_graceful(self):
        # Card with only id, no other expected fields
        result = compact_item({"id": 999}, "card")
        assert result == {"id": 999}

    def test_card_no_assignees(self):
        card = {"id": 1, "title": "Solo task", "app_url": "https://example.com"}
        result = compact_item(card, "card")
        assert "assignee_names" not in result
        assert result["title"] == "Solo task"

    def test_comment_content_truncation(self):
        long_content = "x" * 300
        comment = {"id": 1, "content": long_content, "created_at": "2026-01-01"}
        result = compact_item(comment, "comment")
        assert result["content"] == "x" * 200 + "..."
        assert len(result["content"]) == 203

    def test_comment_short_content_not_truncated(self):
        comment = {"id": 1, "content": "short", "created_at": "2026-01-01"}
        result = compact_item(comment, "comment")
        assert result["content"] == "short"

    def test_campfire_line_content_truncation(self):
        long_content = "y" * 250
        line = {"id": 1, "content": long_content, "created_at": "2026-01-01"}
        result = compact_item(line, "campfire_line")
        assert result["content"] == "y" * 200 + "..."

    def test_step_with_assignees(self):
        step = {
            "id": 1,
            "title": "Step 1",
            "completed": False,
            "due_on": "2026-03-01",
            "assignees": [{"id": 10, "name": "Carol"}],
        }
        result = compact_item(step, "step")
        assert result == {
            "id": 1,
            "title": "Step 1",
            "completed": False,
            "due_on": "2026-03-01",
            "assignee_names": ["Carol"],
        }

    def test_document_with_creator(self):
        doc = {
            "id": 1,
            "title": "Design Doc",
            "created_at": "2026-01-01",
            "app_url": "https://example.com",
            "creator": {"id": 5, "name": "Dave"},
            "content": "<p>Very long document...</p>",
        }
        result = compact_item(doc, "document")
        assert result == {
            "id": 1,
            "title": "Design Doc",
            "created_at": "2026-01-01",
            "app_url": "https://example.com",
            "creator_name": "Dave",
        }


# --- compact_list tests ---

class TestCompactList:
    def test_empty_list(self):
        assert compact_list([], "card") == []

    def test_list_of_cards(self):
        cards = [FULL_CARD, {"id": 2, "title": "Card 2", "completed": True}]
        result = compact_list(cards, "card")
        assert len(result) == 2
        assert result[0]["id"] == 123
        assert result[0]["title"] == "Fix login bug"
        assert "assignee_names" in result[0]
        assert result[1]["id"] == 2
        assert result[1]["title"] == "Card 2"

    def test_non_list_input(self):
        assert compact_list("not a list", "card") == "not a list"


# --- Helper function tests ---

class TestExtractAssigneeNames:
    def test_multiple_assignees(self):
        item = {"assignees": [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]}
        assert _extract_assignee_names(item) == ["A", "B"]

    def test_no_assignees_key(self):
        assert _extract_assignee_names({"id": 1}) == []

    def test_empty_assignees(self):
        assert _extract_assignee_names({"assignees": []}) == []

    def test_assignee_without_name(self):
        item = {"assignees": [{"id": 1}]}
        assert _extract_assignee_names(item) == []

    def test_assignees_not_list(self):
        item = {"assignees": "invalid"}
        assert _extract_assignee_names(item) == []


class TestExtractCreatorName:
    def test_creator_present(self):
        assert _extract_creator_name({"creator": {"id": 1, "name": "Alice"}}) == "Alice"

    def test_no_creator(self):
        assert _extract_creator_name({"id": 1}) is None

    def test_creator_without_name(self):
        assert _extract_creator_name({"creator": {"id": 1}}) is None

    def test_creator_not_dict(self):
        assert _extract_creator_name({"creator": "invalid"}) is None

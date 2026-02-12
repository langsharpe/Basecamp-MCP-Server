"""
Compact response formatter for Basecamp MCP tools.

Filters full Basecamp API responses down to essential fields for AI agents,
reducing context window usage by ~90%.

Usage:
    from compact_response import compact_list

    cards = client.get_cards(project_id, column_id)
    if compact:
        cards = compact_list(cards, "card")
"""

from typing import Any, Dict, List, Optional


# Fields to keep for each resource type in compact mode
COMPACT_FIELDS = {
    "project":       ["id", "name", "description", "app_url"],
    "todo":          ["id", "title", "completed", "due_on", "app_url"],
    "todolist":      ["id", "title", "completed", "app_url"],
    "card":          ["id", "title", "completed", "due_on", "app_url"],
    "column":        ["id", "title", "cards_count"],
    "step":          ["id", "title", "completed", "due_on"],
    "message":       ["id", "subject", "created_at", "app_url"],
    "comment":       ["id", "created_at", "app_url"],
    "forward":       ["id", "subject", "created_at", "app_url"],
    "reply":         ["id", "created_at", "app_url"],
    "document":      ["id", "title", "created_at", "app_url"],
    "upload":        ["id", "title", "filename", "created_at", "app_url"],
    "campfire_line": ["id", "created_at"],
    "event":         ["id", "action", "created_at"],
    "recording":     ["id", "title", "type", "created_at", "app_url"],
    "webhook":       ["id", "payload_url", "active"],
    "card_table":    ["id", "title"],
}

# Resource types that should include assignee names
_ASSIGNEE_TYPES = {"todo", "card", "step"}

# Resource types that should include creator name
_CREATOR_TYPES = {"message", "comment", "forward", "reply", "document", "upload"}

# Resource types that should include truncated content
_CONTENT_TYPES = {"comment", "campfire_line"}

_CONTENT_MAX_LENGTH = 200


def _extract_assignee_names(item: Dict[str, Any]) -> List[str]:
    """Extract assignee names from nested assignees/assignee fields."""
    names = []
    assignees = item.get("assignees")
    if isinstance(assignees, list):
        for assignee in assignees:
            if isinstance(assignee, dict) and "name" in assignee:
                names.append(assignee["name"])
    return names


def _extract_creator_name(item: Dict[str, Any]) -> Optional[str]:
    """Extract creator name from nested creator field."""
    creator = item.get("creator")
    if isinstance(creator, dict):
        return creator.get("name")
    return None


def compact_item(item: Dict[str, Any], resource_type: str) -> Dict[str, Any]:
    """Filter a single item to only compact fields.

    Args:
        item: Full API response item
        resource_type: Key into COMPACT_FIELDS (e.g. "card", "todo")

    Returns:
        Dict with only the essential fields
    """
    if not isinstance(item, dict):
        return item

    fields = COMPACT_FIELDS.get(resource_type, [])
    result = {}

    for field in fields:
        if field in item:
            result[field] = item[field]

    if resource_type in _ASSIGNEE_TYPES:
        names = _extract_assignee_names(item)
        if names:
            result["assignee_names"] = names

    if resource_type in _CREATOR_TYPES:
        name = _extract_creator_name(item)
        if name:
            result["creator_name"] = name

    if resource_type in _CONTENT_TYPES:
        content = item.get("content")
        if isinstance(content, str):
            if len(content) > _CONTENT_MAX_LENGTH:
                result["content"] = content[:_CONTENT_MAX_LENGTH] + "..."
            else:
                result["content"] = content

    return result


def compact_list(items: List[Any], resource_type: str) -> List[Dict[str, Any]]:
    """Filter a list of items to only compact fields.

    Args:
        items: List of full API response items
        resource_type: Key into COMPACT_FIELDS

    Returns:
        List of filtered items
    """
    if not isinstance(items, list):
        return items
    return [compact_item(item, resource_type) for item in items]

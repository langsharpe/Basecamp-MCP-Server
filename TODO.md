~~Quick Wins: Client Methods Already Exist, No MCP Tool Wrapper~~ DONE

All 9 methods now have `@mcp.tool()` wrappers in `basecamp_fastmcp.py`:

| Client Method | MCP Tool | Status |
|---|---|---|
| `get_people()` | `get_people(compact)` | Done |
| `get_campfires(project_id)` | `get_campfires(project_id, compact)` | Done |
| `get_schedule(project_id)` | `get_schedule(project_id)` | Done |
| `get_schedule_entries(project_id)` | `get_schedule_entries(project_id, compact)` | Done |
| `get_comment(comment_id, bucket_id)` | `get_comment(project_id, comment_id)` | Done |
| `update_comment(comment_id, bucket_id, content)` | `update_comment(project_id, comment_id, content)` | Done |
| `delete_comment(comment_id, bucket_id)` | `delete_comment(project_id, comment_id)` | Done |
| `get_todoset(project_id)` | `get_todoset(project_id)` | Done |
| `get_todolist(todolist_id)` | `get_todolist(project_id, todolist_id)` | Done |

Also added compact field mappings for `person`, `campfire`, and `schedule_entry` in `compact_response.py`.

High Priority: Commonly Needed Features

#### ~~1. **Messages -- Create & Update**~~ DONE
- `POST /buckets/{id}/message_boards/{id}/messages.json` -- **Create a message** ✅
- `PUT /buckets/{id}/messages/{id}.json` -- **Update a message** ✅

Added `create_message(project_id, message_board_id, subject, content, category_id)` and `update_message(project_id, message_id, subject, content, category_id)` to both `basecamp_client.py` and `basecamp_fastmcp.py`. Tests in `tests/test_messages.py`.

#### ~~2. **Campfire -- Send & Delete Lines**~~ DONE
- `POST /buckets/{id}/chats/{id}/lines.json` -- **Send a campfire message** ✅
- `GET /buckets/{id}/chats/{id}/lines/{id}.json` -- Get a specific line ✅
- `DELETE /buckets/{id}/chats/{id}/lines/{id}.json` -- Delete a line ✅

Added `get_campfire_line(project_id, campfire_id, line_id)`, `create_campfire_line(project_id, campfire_id, content)`, and `delete_campfire_line(project_id, campfire_id, line_id)` to both `basecamp_client.py` and `basecamp_fastmcp.py`. Tests in `tests/test_campfire.py`.

#### ~~3. **People Management**~~ DONE
- `GET /people/{id}.json` -- **Get a specific person** ✅
- `GET /projects/{id}/people.json` -- **Get project members** ✅
- `PUT /projects/{id}/people/users.json` -- **Manage project access** (grant/revoke) ✅
- `GET /circles/people.json` -- Get pingable people ✅
- `GET /my/profile.json` -- **Get current user profile** ✅

Added `get_person`, `get_my_profile`, `get_project_people`, `update_project_access`, and `get_pingable_people` to both `basecamp_client.py` and `basecamp_fastmcp.py`. Tests in `tests/test_people.py`.

#### ~~5. **Native Basecamp Search**~~ DONE
- `GET /search.json?q=...` -- **Server-side search** ✅

Added `search(query, type, bucket_id, creator_id, file_type, exclude_chat, page, per_page)` to `basecamp_client.py` and `native_search(...)` MCP tool to `basecamp_fastmcp.py`. Supports filtering by type, project, creator, file type, and pagination. Tests in `tests/test_search.py`.

#### ~~9. **To-do Lists CRUD**~~ DONE
- `POST /buckets/{id}/todosets/{id}/todolists.json` -- **Create a todolist** ✅
- `PUT /buckets/{id}/todolists/{id}.json` -- **Update a todolist** ✅
- Trash a todolist (via recording status) ✅

Added `create_todolist`, `update_todolist`, `trash_todolist` to both `basecamp_client.py` and `basecamp_fastmcp.py`. Tests in `tests/test_todolists.py`.

#### ~~10. **To-do List Groups**~~ DONE
- `GET /buckets/{id}/todolists/{id}/groups.json` -- List groups ✅
- `POST /buckets/{id}/todolists/{id}/groups.json` -- Create a group ✅
- `PUT /buckets/{id}/todolists/groups/{id}/position.json` -- Reposition a group ✅

Added `get_todolist_groups`, `create_todolist_group`, `reposition_todolist_group` to both `basecamp_client.py` and `basecamp_fastmcp.py`. Also added `todolist_group` compact field mapping. Tests in `tests/test_todolists.py`.

#### ~~11. **To-do Repositioning**~~ DONE
- `PUT /buckets/{id}/todos/{id}/position.json` -- **Reposition a to-do** (move between lists too) ✅

Added `reposition_todo(project_id, todo_id, position, parent_id)` to both `basecamp_client.py` and `basecamp_fastmcp.py`. Supports both repositioning within a list and moving to a different list via `parent_id`. Tests in `tests/test_todolists.py`.

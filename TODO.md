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

#### 2. **Campfire -- Send & Delete Lines** (currently read-only)
- `POST /buckets/{id}/chats/{id}/lines.json` -- **Send a campfire message**
- `GET /buckets/{id}/chats/{id}/lines/{id}.json` -- Get a specific line
- `DELETE /buckets/{id}/chats/{id}/lines/{id}.json` -- Delete a line

#### 3. **People Management**
- `GET /people/{id}.json` -- **Get a specific person**
- `GET /projects/{id}/people.json` -- **Get project members**
- `PUT /projects/{id}/people/users.json` -- **Manage project access** (grant/revoke)
- `GET /circles/people.json` -- Get pingable people
- `GET /my/profile.json` -- **Get current user profile

#### 5. **Native Basecamp Search**
- `GET /search.json?q=...` -- **Server-side search** (currently using custom client-side search)

#### 9. **To-do Lists CRUD** (currently only listing)
- `POST /buckets/{id}/todosets/{id}/todolists.json` -- **Create a todolist**
- `PUT /buckets/{id}/todolists/{id}.json` -- **Update a todolist**
- Trash a todolist (via recording status)

#### 10. **To-do List Groups** (sub-sections within todolists)
- `GET /buckets/{id}/todolists/{id}/groups.json` -- List groups
- `POST` -- Create a group
- `PUT .../position.json` -- Reposition a group

#### 11. **To-do Repositioning**
- `PUT /buckets/{id}/todos/{id}/position.json` -- **Reposition a to-do** (move between lists too)

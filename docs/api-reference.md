# Mirror API Reference

Base URL: `http://localhost:8000/api`

## Authentication

### POST /auth/register
Create a new account.
```json
Request:  { "email": "user@example.com", "name": "User", "password": "secret" }
Response: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

### POST /auth/login
```json
Request:  { "email": "user@example.com", "password": "secret" }
Response: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

### POST /auth/refresh
```json
Request:  { "refresh_token": "..." }
Response: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

## Chat (WebSocket)

### WS /chat/ws?token={access_token}

**Client → Server:**
```json
{ "type": "message", "content": "Hello", "conversation_id": null }
{ "type": "ping" }
```

**Server → Client:**
```json
{ "type": "message", "content": "...", "sender": "mirror", "timestamp": "...", "metadata": { "conversation_id": "...", "flow_active": false } }
{ "type": "message", "content": "...", "flow_prompt": { "flow_id": "check_in", "step": "mood", "prompt": "...", "input_type": "slider", "min_val": 1, "max_val": 10 } }
{ "type": "pong" }
```

### GET /chat/conversations?limit=20
List conversations. Requires auth.

### GET /chat/conversations/{id}/messages?limit=50
Get messages for a conversation. Requires auth.

## Dashboard

### GET /dashboard/summary
Full dashboard data. Requires auth.

### GET /dashboard/mood-trends?days=30
Mood chart data. Requires auth.

### GET /dashboard/life-areas
Current life area scores. Requires auth.

### GET /dashboard/patterns
Detected behavioral patterns. Requires auth.

### GET /dashboard/habits
Active habits with streaks. Requires auth.

## Psychology

### POST /habits
Create a new habit. Requires auth.
```json
Request: { "name": "Pushups", "anchor": "After coffee", "tiny_behavior": "2 pushups", "life_area": "physical" }
Response: { "id": "...", "name": "Pushups" }
```

### POST /habits/{id}/log
Log habit completion. Requires auth.
```json
Request: { "completed": true, "version_done": "tiny" }
Response: { "status": "ok", "habit_id": "...", "streak": 5, "total_completions": 12 }
```

### POST /suggestions/{id}/feedback
Rate a suggestion. Requires auth.
```json
Request: { "status": "completed", "effectiveness_rating": 4 }
Response: { "status": "ok", "suggestion_id": "..." }
```

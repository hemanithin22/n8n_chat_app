# Flask Chat Application with n8n Integration

A Flask-based multi-chat application that integrates with n8n webhooks for AI-powered conversations. Users can create multiple chat sessions, switch between them, and maintain separate conversation histories.

## Features

- 🔐 Simple username-based authentication
- 💬 Multiple chat sessions per user
- 📝 Persistent chat history stored in PostgreSQL
- 🤖 n8n webhook integration for AI responses
- 🎨 Clean and responsive web interface
- 🔄 Real-time chat switching
- 📊 Chat management (create, rename, delete)

## Project Structure

```
flask_chat_app/
├── app.py                      # Main Flask application
├── database.py                 # PostgreSQL database connection
├── requirements.txt            # Python dependencies
├── test_chat_history.py       # Database testing utility
├── data/                       # JSON data storage
│   ├── chats.json             # Chat sessions metadata
│   ├── users.json             # User information
│   └── webhooks.json          # n8n webhook configuration
├── static/                     # Static assets
│   ├── css/                   # Stylesheets
│   └── js/                    # JavaScript files
└── templates/                  # HTML templates
    ├── chatinterface.html     # Main chat interface
    ├── login.html             # Login page
    └── webhookmanagement.html # Webhook configuration page
```

## Requirements

- Python 3.7+
- PostgreSQL database
- n8n instance (for AI responses)

## Installation

1. **Clone the repository**
   ```bash
   cd /home/nithin/chatn8n/flask_chat_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=n8n
   DB_USER=postgres
   DB_PASSWORD=your_password
   SECRET_KEY=your_secret_key_here
   ```

4. **Initialize the database**
   Ensure PostgreSQL is running and the `n8n_chat_histories` table exists:
   ```sql
   CREATE TABLE IF NOT EXISTS n8n_chat_histories (
       id SERIAL PRIMARY KEY,
       session_id VARCHAR(255) NOT NULL,
       message JSONB NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

5. **Start the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## Configuration

### Database Connection

The application uses PostgreSQL to store chat histories. Configure the connection in your `.env` file:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=n8n
DB_USER=postgres
DB_PASSWORD=your_password
```

### n8n Webhook Setup

1. Navigate to the Webhook Management page after logging in
2. Add your n8n webhook URL
3. The webhook should accept POST requests with the following structure:
   ```json
   {
     "message": "user message",
     "session_id": "unique-session-id",
     "user_id": "user-id"
   }
   ```

4. The n8n workflow should save both user and AI messages to the database

## API Documentation

### Authentication

All chat-related endpoints require authentication via session cookies.

### Chat Management Endpoints

#### GET /api/chats
Get all chats for the current logged-in user.

**Response:**
```json
{
  "chats": [
    {
      "id": "chat-uuid-1",
      "user_id": "user-uuid",
      "session_id": "session-uuid",
      "title": "Chat 1",
      "created_at": "2025-10-07T17:00:00",
      "updated_at": "2025-10-07T17:30:00"
    }
  ],
  "total": 1
}
```

#### POST /api/chats
Create a new chat session.

**Request Body (optional):**
```json
{
  "title": "My New Chat"
}
```

**Response:**
```json
{
  "message": "Chat created successfully.",
  "chat": {
    "id": "chat-uuid",
    "user_id": "user-uuid",
    "session_id": "new-session-uuid",
    "title": "My New Chat",
    "created_at": "2025-10-07T19:00:00",
    "updated_at": "2025-10-07T19:00:00"
  }
}
```

#### PUT /api/chats/<chat_id>
Update a chat (rename or switch to it).

**Switch to a chat:**
```json
{
  "action": "switch"
}
```

**Rename a chat:**
```json
{
  "title": "New Chat Title"
}
```

#### DELETE /api/chats/<chat_id>
Delete a chat session.

**Note:** Chat history in the database is NOT deleted, only the chat metadata.

### Chat History

#### GET /api/chat/history
Get chat history for current active chat or a specific chat.

**Query Parameters:**
- `chat_id` (optional): Get history for a specific chat

**Response:**
```json
{
  "chat_id": "chat-uuid",
  "session_id": "session-uuid",
  "history": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "assistant",
      "content": "Hi there!"
    }
  ],
  "total_messages": 2
}
```

## Usage Examples

### Using cURL

```bash
# 1. Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john"}' \
  -c cookies.txt

# 2. List chats
curl http://localhost:5000/api/chats -b cookies.txt

# 3. Create new chat
curl -X POST http://localhost:5000/api/chats \
  -H "Content-Type: application/json" \
  -d '{"title": "Project Ideas"}' \
  -b cookies.txt

# 4. Send message (uses active chat)
curl -X POST http://localhost:5000/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}' \
  -b cookies.txt

# 5. Get chat history
curl http://localhost:5000/api/chat/history -b cookies.txt

# 6. Switch to another chat
curl -X PUT http://localhost:5000/api/chats/other-chat-uuid \
  -H "Content-Type: application/json" \
  -d '{"action": "switch"}' \
  -b cookies.txt

# 7. Delete a chat
curl -X DELETE http://localhost:5000/api/chats/chat-uuid -b cookies.txt
```

## How It Works

### Login Flow
1. User logs in with a username
2. System checks if user has any existing chats
3. If no chats exist → Creates a default "New Chat"
4. If chats exist → Uses the most recently updated chat
5. Session stores: `user_id`, `chat_id`, `session_id`

### Sending Messages
1. User sends a message via `/chat/send`
2. System uses the current active chat's `session_id`
3. Message is sent to the n8n webhook with `session_id`
4. n8n saves both user message and AI response to the database
5. Chat's `updated_at` timestamp is updated

### Multiple Chats
- Each user can have unlimited chat sessions
- Each chat has a unique `session_id`
- Chat history is tied to `session_id`
- Users can switch between chats
- Only one chat is active at a time (stored in Flask session)

## Data Structure

### User (users.json)
```json
{
  "id": "user-uuid",
  "username": "john",
  "created_at": "2025-10-07T16:00:00",
  "last_login": "2025-10-07T17:00:00"
}
```

### Chat (chats.json)
```json
{
  "id": "chat-uuid",
  "user_id": "user-uuid",
  "session_id": "session-uuid",
  "title": "My Chat",
  "created_at": "2025-10-07T16:00:00",
  "updated_at": "2025-10-07T17:00:00"
}
```

### Chat History (PostgreSQL - n8n_chat_histories)
```sql
id | session_id     | message (JSONB)
---|----------------|------------------
1  | session-uuid   | {"type": "human", "content": "Hello", ...}
2  | session-uuid   | {"type": "ai", "content": "Hi!", ...}
```

## Troubleshooting

### Chat History Not Loading

1. **Check browser console for errors**
   - Open Developer Tools (F12)
   - Look for error messages in the Console tab

2. **Verify database connection**
   ```bash
   python -c "from database import test_connection; print('DB OK' if test_connection() else 'DB FAIL')"
   ```

3. **Check environment variables**
   - Ensure `.env` file exists with correct credentials
   - Verify PostgreSQL is running and accessible

4. **Test with specific session_id**
   ```bash
   python test_chat_history.py
   ```

### Database Connection Issues

1. **Verify psycopg2 is installed**
   ```bash
   pip list | grep psycopg2
   ```

2. **Check PostgreSQL service**
   ```bash
   sudo systemctl status postgresql
   ```

3. **Test database credentials**
   ```bash
   psql -h localhost -U postgres -d n8n
   ```

### Webhook Not Responding

1. Ensure n8n is running and accessible
2. Check webhook URL in Webhook Management page
3. Verify n8n workflow is active and configured correctly
4. Check Flask app console for webhook request errors

## Development

### Testing Database Connection
```bash
python -c "from database import test_connection; test_connection()"
```

### Viewing Current Chats
```bash
cat data/chats.json
```

### Viewing Registered Users
```bash
cat data/users.json
```

### Enabling Debug Mode
In `app.py`, set:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## Security Notes

⚠️ **Important:** This application uses a simplified authentication system suitable for development. For production use, consider implementing:

- Proper password hashing and authentication
- HTTPS/SSL encryption
- CSRF protection
- Rate limiting
- Input validation and sanitization
- Session timeout
- Database connection pooling

## Dependencies

- **Flask** - Web framework
- **psycopg2-binary** - PostgreSQL adapter
- **requests** - HTTP library for webhook communication
- **python-dotenv** - Environment variable management

## License

This project is provided as-is for educational and development purposes.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check browser console and Flask logs for errors
4. Verify database and n8n connectivity

---

**Built with Flask 🐍 | Powered by n8n 🤖**

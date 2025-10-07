import json
import os
import requests
import uuid
from functools import wraps
from flask import Flask, jsonify, redirect, render_template, request, url_for, session
from dotenv import load_dotenv
from database import get_chat_history, test_connection

# Load environment variables from .env file
load_dotenv()

# Initialize Flask App
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Define the path for the data file
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
WEBHOOK_FILE = os.path.join(DATA_DIR, 'webhooks.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CHATS_FILE = os.path.join(DATA_DIR, 'chats.json')

# --- Helper Functions ---

def ensure_data_file():
    """Ensures the data directory and data files exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(WEBHOOK_FILE):
        with open(WEBHOOK_FILE, 'w') as f:
            json.dump({"webhooks": []}, f)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({"users": []}, f)
    if not os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, 'w') as f:
            json.dump({"chats": []}, f)
        with open(USERS_FILE, 'w') as f:
            json.dump({"users": []}, f)

def read_webhooks():
    """Reads all webhooks from the JSON file."""
    ensure_data_file()
    try:
        with open(WEBHOOK_FILE, 'r') as f:
            data = json.load(f)
            # Handle old format migration
            if "active_webhook" in data:
                # Migrate old format to new format
                old_webhook = data.get("active_webhook")
                if old_webhook:
                    webhooks = [{"id": str(uuid.uuid4()), "name": "Default Webhook", "url": old_webhook}]
                else:
                    webhooks = []
                data = {"webhooks": webhooks}
                with open(WEBHOOK_FILE, 'w') as f:
                    json.dump(data, f, indent=4)
            return data.get("webhooks", [])
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def write_webhooks(webhooks):
    """Writes the webhooks list to the JSON file."""
    ensure_data_file()
    with open(WEBHOOK_FILE, 'w') as f:
        json.dump({"webhooks": webhooks}, f, indent=4)

def get_webhook_by_id(webhook_id):
    """Gets a specific webhook by its ID."""
    webhooks = read_webhooks()
    for webhook in webhooks:
        if webhook.get("id") == webhook_id:
            return webhook
    return None

def read_users():
    """Reads all users from the JSON file."""
    ensure_data_file()
    try:
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("users", [])
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def write_users(users):
    """Writes the users list to the JSON file."""
    ensure_data_file()
    with open(USERS_FILE, 'w') as f:
        json.dump({"users": users}, f, indent=4)

def get_user_by_username(username):
    """Gets a specific user by username."""
    users = read_users()
    for user in users:
        if user.get("username").lower() == username.lower():
            return user
    return None

def add_user(username):
    """Adds a new user to the users list."""
    from datetime import datetime
    users = read_users()
    
    # Check if user already exists
    existing_user = get_user_by_username(username)
    if existing_user:
        # Update last login
        for user in users:
            if user.get("username").lower() == username.lower():
                user['last_login'] = datetime.now().isoformat()
                break
    else:
        # Add new user
        new_user = {
            "id": str(uuid.uuid4()),
            "username": username,
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat()
        }
        users.append(new_user)
    
    write_users(users)
    return get_user_by_username(username)

def read_chats():
    """Reads all chats from the JSON file."""
    ensure_data_file()
    try:
        with open(CHATS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("chats", [])
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def write_chats(chats):
    """Writes the chats list to the JSON file."""
    ensure_data_file()
    with open(CHATS_FILE, 'w') as f:
        json.dump({"chats": chats}, f, indent=4)

def get_user_chats(user_id):
    """Gets all chats for a specific user."""
    chats = read_chats()
    return [chat for chat in chats if chat.get("user_id") == user_id]

def get_chat_by_id(chat_id):
    """Gets a specific chat by its ID."""
    chats = read_chats()
    for chat in chats:
        if chat.get("id") == chat_id:
            return chat
    return None

def create_new_chat(user_id, title=None):
    """Creates a new chat for a user."""
    from datetime import datetime
    chats = read_chats()
    
    # Generate a new session_id for this chat
    session_id = str(uuid.uuid4())
    
    # If no title provided, generate one with date and time
    if not title:
        user_chats_count = len(get_user_chats(user_id))
        now = datetime.now()
        # Format: Chat-1 (Jan 7, 22:30)
        formatted_date = now.strftime("%b %-d, %H:%M") if os.name != 'nt' else now.strftime("%b %d, %H:%M").replace(" 0", " ")
        title = f"Chat-{user_chats_count + 1} ({formatted_date})"
    
    new_chat = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_id": session_id,
        "title": title,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    chats.append(new_chat)
    write_chats(chats)
    return new_chat

def update_chat(chat_id, updates):
    """Updates a chat's information."""
    from datetime import datetime
    chats = read_chats()
    
    for chat in chats:
        if chat.get("id") == chat_id:
            if "title" in updates:
                chat["title"] = updates["title"]
            chat["updated_at"] = datetime.now().isoformat()
            write_chats(chats)
            return chat
    
    return None

def delete_chat(chat_id):
    """Deletes a chat."""
    chats = read_chats()
    initial_length = len(chats)
    chats = [c for c in chats if c.get("id") != chat_id]
    
    if len(chats) < initial_length:
        write_chats(chats)
        return True
    return False

# --- Authentication Decorator ---

def login_required(f):
    """Decorator to ensure user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Main Routes ---

@app.route('/')
def index():
    """Redirects the root URL to the chat interface."""
    return redirect(url_for('chat_interface'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login - GET shows the form, POST processes the login."""
    if request.method == 'GET':
        # If already logged in, redirect to chat
        if 'username' in session:
            return redirect(url_for('chat_interface'))
        return render_template('login.html')
    
    # POST request - process login
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({"error": "Username is required."}), 400
    
    username = data['username'].strip()
    if len(username) < 2:
        return jsonify({"error": "Username must be at least 2 characters long."}), 400
    
    # Add or update user in the users.json file
    user = add_user(username)
    
    # Store username in session
    session['username'] = username
    session['user_id'] = user.get('id')
    
    # Get user's chats or create a default one
    user_chats = get_user_chats(user.get('id'))
    if not user_chats:
        # Create a default chat for new users
        default_chat = create_new_chat(user.get('id'))
        session['chat_id'] = default_chat['id']
        session['session_id'] = default_chat['session_id']
    else:
        # Use the most recent chat (last updated)
        latest_chat = sorted(user_chats, key=lambda x: x.get('updated_at', ''), reverse=True)[0]
        session['chat_id'] = latest_chat['id']
        session['session_id'] = latest_chat['session_id']
    
    return jsonify({"message": "Login successful.", "username": username}), 200

@app.route('/logout')
def logout():
    """Logs out the current user."""
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat_interface():
    """Renders the main chat interface page."""
    return render_template('chatinterface.html')

@app.route('/webhooks')
@login_required
def webhook_management():
    """Renders the webhook management page."""
    return render_template('webhookmanagement.html')

# --- API Routes ---

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """API endpoint to get all registered users."""
    users = read_users()
    return jsonify({"users": users, "total": len(users)}), 200

@app.route('/api/chats', methods=['GET'])
@login_required
def get_chats():
    """API endpoint to get all chats for the current user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not found in session."}), 401
    
    chats = get_user_chats(user_id)
    return jsonify({"chats": chats, "total": len(chats)}), 200

@app.route('/api/chats', methods=['POST'])
@login_required
def create_chat():
    """API endpoint to create a new chat."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not found in session."}), 401
    
    data = request.get_json() or {}
    title = data.get('title')
    
    new_chat = create_new_chat(user_id, title)
    
    # Set this as the active chat
    session['chat_id'] = new_chat['id']
    session['session_id'] = new_chat['session_id']
    
    return jsonify({"message": "Chat created successfully.", "chat": new_chat}), 201

@app.route('/api/chats/<chat_id>', methods=['PUT'])
@login_required
def update_chat_endpoint(chat_id):
    """API endpoint to update a chat (e.g., rename or switch to it)."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not found in session."}), 401
    
    # Verify the chat belongs to the user
    chat = get_chat_by_id(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found."}), 404
    
    if chat.get("user_id") != user_id:
        return jsonify({"error": "Unauthorized."}), 403
    
    data = request.get_json() or {}
    
    # Check if this is a "switch to" request
    if data.get('action') == 'switch':
        session['chat_id'] = chat_id
        session['session_id'] = chat['session_id']
        return jsonify({"message": "Switched to chat successfully.", "chat": chat}), 200
    
    # Otherwise, update the chat
    updates = {}
    if 'title' in data:
        updates['title'] = data['title']
    
    updated_chat = update_chat(chat_id, updates)
    if updated_chat:
        return jsonify({"message": "Chat updated successfully.", "chat": updated_chat}), 200
    
    return jsonify({"error": "Failed to update chat."}), 500

@app.route('/api/chats/<chat_id>/rename', methods=['PUT'])
@login_required
def rename_chat_endpoint(chat_id):
    """API endpoint specifically for renaming a chat."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not found in session."}), 401
    
    # Verify the chat belongs to the user
    chat = get_chat_by_id(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found."}), 404
    
    if chat.get("user_id") != user_id:
        return jsonify({"error": "Unauthorized."}), 403
    
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Missing 'title' in request body."}), 400
    
    new_title = data['title'].strip()
    if not new_title:
        return jsonify({"error": "Title cannot be empty."}), 400
    
    if len(new_title) > 100:
        return jsonify({"error": "Title must be 100 characters or less."}), 400
    
    # Update the chat title
    updated_chat = update_chat(chat_id, {"title": new_title})
    if updated_chat:
        return jsonify({"message": "Chat renamed successfully.", "chat": updated_chat}), 200
    
    return jsonify({"error": "Failed to rename chat."}), 500

@app.route('/api/chats/<chat_id>', methods=['DELETE'])
@login_required
def delete_chat_endpoint(chat_id):
    """API endpoint to delete a chat."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not found in session."}), 401
    
    # Verify the chat belongs to the user
    chat = get_chat_by_id(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found."}), 404
    
    if chat.get("user_id") != user_id:
        return jsonify({"error": "Unauthorized."}), 403
    
    # Delete the chat
    if delete_chat(chat_id):
        # If this was the active chat, clear the session
        if session.get('chat_id') == chat_id:
            session.pop('chat_id', None)
            session.pop('session_id', None)
        
        return jsonify({"message": "Chat deleted successfully."}), 200
    
    return jsonify({"error": "Failed to delete chat."}), 500

@app.route('/api/webhooks', methods=['GET'])
def get_webhooks():
    """API endpoint to get all webhooks."""
    webhooks = read_webhooks()
    return jsonify({"webhooks": webhooks}), 200

@app.route('/api/webhooks', methods=['POST'])
def create_webhook():
    """API endpoint to create a new webhook."""
    data = request.get_json()
    if not data or 'name' not in data or 'url' not in data:
        return jsonify({"error": "Missing 'name' or 'url' in request body."}), 400
    
    webhooks = read_webhooks()
    new_webhook = {
        "id": str(uuid.uuid4()),
        "name": data['name'],
        "url": data['url']
    }
    webhooks.append(new_webhook)
    write_webhooks(webhooks)
    return jsonify({"message": "Webhook created successfully.", "webhook": new_webhook}), 201

@app.route('/api/webhooks/<webhook_id>', methods=['PUT'])
def update_webhook(webhook_id):
    """API endpoint to update an existing webhook."""
    data = request.get_json()
    if not data or ('name' not in data and 'url' not in data):
        return jsonify({"error": "Missing 'name' or 'url' in request body."}), 400
    
    webhooks = read_webhooks()
    webhook_found = False
    
    for webhook in webhooks:
        if webhook.get("id") == webhook_id:
            if 'name' in data:
                webhook['name'] = data['name']
            if 'url' in data:
                webhook['url'] = data['url']
            webhook_found = True
            break
    
    if not webhook_found:
        return jsonify({"error": "Webhook not found."}), 404
    
    write_webhooks(webhooks)
    return jsonify({"message": "Webhook updated successfully.", "webhook": webhook}), 200

@app.route('/api/webhooks/<webhook_id>', methods=['DELETE'])
def delete_webhook(webhook_id):
    """API endpoint to delete a webhook."""
    webhooks = read_webhooks()
    initial_length = len(webhooks)
    webhooks = [w for w in webhooks if w.get("id") != webhook_id]
    
    if len(webhooks) == initial_length:
        return jsonify({"error": "Webhook not found."}), 404
    
    write_webhooks(webhooks)
    return jsonify({"message": "Webhook deleted successfully."}), 200

# Legacy API endpoints for backward compatibility (deprecated)
@app.route('/api/webhook', methods=['GET'])
def get_webhook():
    """API endpoint to get the first webhook (legacy support)."""
    webhooks = read_webhooks()
    if webhooks and len(webhooks) > 0:
        return jsonify({"webhook_url": webhooks[0]['url']})
    return jsonify({"webhook_url": None}), 404

@app.route('/api/webhook', methods=['POST'])
def update_webhook_legacy():
    """API endpoint to add or update the webhook URL (legacy support)."""
    data = request.get_json()
    if not data or 'webhook_url' not in data:
        return jsonify({"error": "Missing 'webhook_url' in request body."}), 400
    
    new_url = data['webhook_url']
    webhooks = read_webhooks()
    
    if webhooks and len(webhooks) > 0:
        # Update first webhook
        webhooks[0]['url'] = new_url
    else:
        # Create new webhook
        webhooks.append({
            "id": str(uuid.uuid4()),
            "name": "Default Webhook",
            "url": new_url
        })
    
    write_webhooks(webhooks)
    return jsonify({"message": "Webhook updated successfully.", "webhook_url": new_url}), 200

@app.route('/api/webhook', methods=['DELETE'])
def delete_webhook_legacy():
    """API endpoint to remove all webhooks (legacy support)."""
    write_webhooks([])
    return jsonify({"message": "Webhook deleted successfully."}), 200

@app.route('/api/chat/history', methods=['GET'])
@login_required
def get_chat_history_api():
    """API endpoint to retrieve chat history for the current or specified chat."""
    # Allow getting history for a specific chat_id via query parameter
    chat_id = request.args.get('chat_id')
    
    if chat_id:
        # Get history for specific chat
        user_id = session.get('user_id')
        chat = get_chat_by_id(chat_id)
        
        if not chat:
            return jsonify({"error": "Chat not found."}), 404
        
        if chat.get("user_id") != user_id:
            return jsonify({"error": "Unauthorized."}), 403
        
        session_id = chat['session_id']
    else:
        # Get history for current active chat
        if 'session_id' not in session:
            return jsonify({"history": [], "message": "No active chat found."}), 200
        
        session_id = session['session_id']
        chat_id = session.get('chat_id')
    
    try:
        # Get raw history from database
        raw_history = get_chat_history(session_id)
        
        # Transform the history to frontend-friendly format
        formatted_history = []
        for msg in raw_history:
            message_data = msg.get('message', {})
            
            # Handle different message formats
            if isinstance(message_data, dict):
                msg_type = message_data.get('type', '')
                msg_content = message_data.get('content', '')
                
                # Map database types to frontend roles
                if msg_type == 'human':
                    role = 'user'
                elif msg_type == 'ai':
                    role = 'assistant'
                else:
                    # Skip unknown message types
                    continue
                
                formatted_history.append({
                    'role': role,
                    'content': msg_content
                })
        
        return jsonify({
            "chat_id": chat_id,
            "session_id": session_id,
            "history": formatted_history,
            "total_messages": len(formatted_history)
        }), 200
        
    except Exception as e:
        # Log the error and return empty history
        print(f"Error loading chat history: {e}")
        return jsonify({
            "chat_id": chat_id,
            "session_id": session_id,
            "history": [],
            "total_messages": 0,
            "error": f"Could not load chat history: {str(e)}"
        }), 200

@app.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    """Handles sending a user's message to the configured webhook."""
    user_data = request.get_json()
    if not user_data or 'message' not in user_data:
        return jsonify({"error": "Invalid request. 'message' field is required."}), 400

    user_message = user_data['message']
    webhook_id = user_data.get('webhook_id')  # Optional webhook ID
    
    # Get the webhook to use
    if webhook_id:
        webhook = get_webhook_by_id(webhook_id)
        if not webhook:
            return jsonify({"error": "Selected webhook not found. Please select a valid webhook."}), 404
        webhook_url = webhook['url']
    else:
        # Use the first webhook if no specific one is selected
        webhooks = read_webhooks()
        if not webhooks or len(webhooks) == 0:
            return jsonify({"error": "No webhook is configured. Please set one in the Webhook Management page."}), 400
        webhook_url = webhooks[0]['url']

    # Ensure user has an active chat
    if 'session_id' not in session or 'chat_id' not in session:
        # Create a new chat if none exists
        user_id = session.get('user_id')
        new_chat = create_new_chat(user_id)
        session['chat_id'] = new_chat['id']
        session['session_id'] = new_chat['session_id']
    
    session_id = session['session_id']
    chat_id = session.get('chat_id')
    username = session.get('username', 'Anonymous')
    
    # Update the chat's updated_at timestamp
    if chat_id:
        update_chat(chat_id, {})

    payload = {
        "user_message": user_message,
        "session_id": session_id,
        "username": username
    }
    
    try:
        # Send the message to the external webhook URL
        # n8n will handle saving the chat history
        response = requests.post(webhook_url, json=payload, timeout=120)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        
        webhook_response = response.json()
        if 'reply' not in webhook_response:
             return jsonify({"error": "Webhook response is missing the 'reply' key."}), 500

        return jsonify({"reply": webhook_response['reply']})

    except requests.exceptions.Timeout:
        return jsonify({"error": "The request to the webhook timed out."}), 504
    except requests.exceptions.RequestException as e:
        # This catches connection errors, invalid URLs, etc.
        return jsonify({"error": f"Webhook call failed. Please check the URL and ensure the endpoint is running. Details: {e}"}), 500
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to decode JSON response from the webhook."}), 500


# --- Main Execution ---

if __name__ == '__main__':
    app.run(debug=True, port=5000)

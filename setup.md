# Setup Guide - Flask Chat Application with n8n Integration

This guide will walk you through the complete setup process from cloning the repository to running the application.

## Prerequisites

Before starting, ensure you have the following installed on your system:

- **Python 3.7+** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **PostgreSQL** - [Download PostgreSQL](https://www.postgresql.org/download/)
- **n8n instance** (for AI responses) - [n8n Installation Guide](https://docs.n8n.io/getting-started/installation/)

## Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/hemanithin22/n8n_chat_app

# Navigate to the project directory
cd n8n_chat_app
```

## Step 2: Create Python Virtual Environment

Creating a virtual environment is recommended to isolate project dependencies.

### On Windows (PowerShell):
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If execution policy error occurs, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### On Windows (Command Prompt):
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat
```

### On macOS/Linux:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

**Note:** You should see `(venv)` in your terminal prompt when the virtual environment is active.

## Step 3: Install Dependencies

With the virtual environment activated, install the required Python packages:

```bash
# Install all dependencies from requirements.txt
pip install -r requirements.txt

# Alternatively, install packages individually:
# pip install Flask psycopg2-binary requests python-dotenv
```

### Verify Installation
```bash
# Check installed packages
pip list

# Should show:
# Flask, psycopg2-binary, requests, python-dotenv, and their dependencies
```

## Step 4: Environment Configuration

Create a `.env` file in the project root directory with your database and application configuration:

```bash
# Create .env file (Windows PowerShell)
New-Item -Path ".env" -ItemType File

# Create .env file (macOS/Linux/Git Bash)
touch .env
```

Add the following content to your `.env` file:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=n8n
DB_USER=postgres
DB_PASSWORD=your_postgres_password_here

# Flask Configuration
SECRET_KEY=your_secret_key_here_make_it_long_and_random

# Optional: Flask Environment
FLASK_ENV=development
FLASK_DEBUG=True
```

### Generate a Secret Key
You can generate a secure secret key using Python:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Step 5: Database Setup

### 5.1 Start PostgreSQL Service

**Windows:**
```powershell
# Start PostgreSQL service
net start postgresql-x64-14  # Replace with your PostgreSQL version
```

**macOS:**
```bash
# Using Homebrew
brew services start postgresql

# Or using pg_ctl
pg_ctl -D /usr/local/var/postgres start
```

**Linux (Ubuntu/Debian):**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql  # To start on boot
```

### 5.2 Create Database and Table

Connect to PostgreSQL and create the required database and table:

```bash
# Connect to PostgreSQL
psql -U postgres -h localhost

# Or if you have a different username:
# psql -U your_username -h localhost
```

In the PostgreSQL prompt, run:

```sql
-- Create database (if it doesn't exist)
CREATE DATABASE n8n;

-- Connect to the database
\c n8n;

-- Create the chat histories table
CREATE TABLE IF NOT EXISTS n8n_chat_histories (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an index for better performance
CREATE INDEX IF NOT EXISTS idx_session_id ON n8n_chat_histories(session_id);
CREATE INDEX IF NOT EXISTS idx_created_at ON n8n_chat_histories(created_at);

-- Exit PostgreSQL
\q
```

### 5.3 Test Database Connection

Test if your Python application can connect to the database:

```bash
# Test database connection
python -c "from database import test_connection; print('✅ Database connection successful!' if test_connection() else '❌ Database connection failed!')"
```

## Step 6: Initialize Data Files

The application uses JSON files for storing user and chat metadata. These will be created automatically when you first run the app, but you can create them manually:

```bash
# Create data directory if it doesn't exist
mkdir -p data

# Create empty JSON files (Windows PowerShell)
'{"users": []}' | Out-File -FilePath "data\users.json" -Encoding UTF8
'{"chats": []}' | Out-File -FilePath "data\chats.json" -Encoding UTF8
'{"webhooks": []}' | Out-File -FilePath "data\webhooks.json" -Encoding UTF8

# Create empty JSON files (macOS/Linux/Git Bash)
echo '{"users": []}' > data/users.json
echo '{"chats": []}' > data/chats.json
echo '{"webhooks": []}' > data/webhooks.json
```

## Step 7: Configure n8n (Optional)

If you have an n8n instance running, you can configure it to work with this chat application:

1. **Start your n8n instance**
2. **Create a webhook workflow** that:
   - Receives POST requests from the chat application
   - Processes the message (e.g., sends to AI service)
   - Saves both user and AI messages back to the database
3. **Note your webhook URL** for later configuration

## Step 8: Run the Application

With everything set up, you can now run the Flask application:

```bash
# Make sure virtual environment is activated
# You should see (venv) in your prompt

# Run the application
python app.py
```

You should see output similar to:
```
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://[your-ip]:5000
```

## Step 9: Access the Application

1. **Open your web browser**
2. **Navigate to:** `http://localhost:5000`
3. **Login with any username** (no password required for development)
4. **Configure n8n webhook** (if available) via the Webhook Management page

## Step 10: Verify Everything Works

### Test Basic Functionality:

1. **Login** with a username
2. **Send a test message** in the chat interface
3. **Check if chat history loads** properly
4. **Create a new chat** and switch between chats
5. **Check database** for stored messages:

```bash
# Connect to database and check data
psql -U postgres -d n8n -c "SELECT session_id, message->>'content', created_at FROM n8n_chat_histories ORDER BY created_at DESC LIMIT 5;"
```

## Troubleshooting

### Common Issues and Solutions:

#### 1. Virtual Environment Issues
```bash
# If activation fails on Windows PowerShell:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Recreate virtual environment if corrupted:
rmdir /s venv  # Windows
rm -rf venv    # macOS/Linux
python -m venv venv
```

#### 2. Database Connection Issues
```bash
# Check if PostgreSQL is running:
# Windows:
net start | findstr postgresql

# macOS/Linux:
ps aux | grep postgres

# Test connection manually:
psql -U postgres -h localhost -d n8n
```

#### 3. Python Import Issues
```bash
# Ensure virtual environment is activated
# Check Python path:
python -c "import sys; print(sys.prefix)"

# Should point to your venv directory
```

#### 4. Port Already in Use
```bash
# If port 5000 is busy, change port in app.py:
# app.run(debug=True, host='0.0.0.0', port=5001)
```

#### 5. Permission Issues (macOS/Linux)
```bash
# If you get permission errors:
sudo chown -R $USER:$USER .
chmod +x app.py
```

## Development Tips

### Useful Commands:

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Deactivate virtual environment
deactivate

# Install new packages and update requirements
pip install package_name
pip freeze > requirements.txt

# Run with different port
python app.py --port 5001

# View logs in real-time
tail -f app.log  # If you add logging to the app
```

### IDE Setup:

1. **VS Code:** Select Python interpreter from your virtual environment
   - `Ctrl+Shift+P` → "Python: Select Interpreter" → Choose `venv/Scripts/python.exe`

2. **PyCharm:** Configure project interpreter to use your virtual environment

## Production Deployment

For production deployment, consider:

1. **Use environment variables** for all configuration
2. **Set up proper logging**
3. **Use a production WSGI server** (e.g., Gunicorn)
4. **Configure HTTPS/SSL**
5. **Set up database connection pooling**
6. **Implement proper authentication**

### Example Production Command:
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## Next Steps

1. **Configure your n8n workflow** to process chat messages
2. **Customize the chat interface** styling and functionality
3. **Add more features** like file uploads, message search, etc.
4. **Set up monitoring and logging** for production use

---

## Quick Start Summary

For experienced developers, here's the quick setup:

```bash
# 1. Clone and navigate
git clone https://github.com/hemanithin22/n8n_chat_app && cd n8n_chat_app

# 2. Set up virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env  # Edit with your settings

# 5. Set up database
psql -U postgres -c "CREATE DATABASE n8n;"
psql -U postgres -d n8n -f setup.sql  # If you have a setup.sql file

# 6. Run application
python app.py
```

**🎉 Your Flask Chat Application should now be running at http://localhost:5000!**

---

**Need help?** Check the main README.md for detailed API documentation and troubleshooting guides.
"""
Database module for chat history management.
Uses existing PostgreSQL database with n8n_chat_histories table.

NOTE: This module only READS chat history.
All chat messages are saved by n8n, not by this application.
"""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'n8n'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', ''),
}


def get_db_connection():
    """
    Creates and returns a connection to the PostgreSQL database.
    
    Returns:
        psycopg2.connection: Database connection object
    
    Raises:
        psycopg2.Error: If connection fails
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise


def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all chat messages for a given session_id, ordered by id.
    
    Args:
        session_id (str): The session identifier for the chat
    
    Returns:
        list: A list of message dictionaries, each containing:
              - id: The database record ID
              - session_id: The session identifier
              - message: The parsed JSON message object
              
    Example:
        >>> get_chat_history("abc-123")
        [
            {
                "id": 1,
                "session_id": "abc-123",
                "message": {
                    "type": "human",
                    "content": "Hello, create a class /celcom_notification",
                    "additional_kwargs": {},
                    "response_metadata": {}
                }
            },
            {
                "id": 2,
                "session_id": "abc-123",
                "message": {
                    "type": "ai",
                    "content": "Here is the generated class structure...",
                    "additional_kwargs": {},
                    "response_metadata": {}
                }
            }
        ]
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query all messages for the session, ordered by id
        query = """
            SELECT id, session_id, message
            FROM n8n_chat_histories
            WHERE session_id = %s
            ORDER BY id ASC
        """
        cursor.execute(query, (session_id,))
        
        rows = cursor.fetchall()
        
        # Parse JSON message strings back to dictionaries
        result = []
        for row in rows:
            message_dict = dict(row)
            # Parse the JSON string in the message column
            if isinstance(message_dict['message'], str):
                try:
                    message_dict['message'] = json.loads(message_dict['message'])
                except json.JSONDecodeError as e:
                    print(f"Error parsing message JSON for id {row['id']}: {e}")
                    # Keep the original string if parsing fails
                    pass
            result.append(message_dict)
        
        return result
        
    except psycopg2.Error as e:
        print(f"Error retrieving chat history: {e}")
        return []
        
    except Exception as e:
        print(f"Unexpected error retrieving chat history: {e}")
        return []
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def test_connection() -> bool:
    """
    Tests the database connection.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import json
import logging
import traceback

router = APIRouter()

# Configure more detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store WebSocket connections for users and admin
user_connections: Dict[str, WebSocket] = {}  # Maps user_id to WebSocket connection
admin_connection: WebSocket = None  # The WebSocket connection for the admin

@router.websocket("/ws/chat/{user_id}")
async def websocket_user(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for user chat
    Handles incoming messages from users and routes them to admin
    """
    logger.info(f"User {user_id} attempting to connect")
    
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        logger.info(f"User {user_id} WebSocket connection accepted")
        
        # Store the user's WebSocket connection
        user_connections[user_id] = websocket
        logger.info(f"User {user_id} added to connections. Total users: {len(user_connections)}")
        
        # Notify admin about new user connection if admin is connected
        if admin_connection:
            try:
                await admin_connection.send_text(json.dumps({
                    "type": "user_connected",
                    "user_id": user_id
                }))
                logger.info(f"Notified admin about user {user_id} connection")
            except Exception as e:
                logger.error(f"Error notifying admin about user connection: {e}")
        
        while True:
            # Receive message from user
            data = await websocket.receive_text()
            logger.debug(f"Received message from user {user_id}: {data}")
            
            # Prepare message for admin
            message_data = {
                "type": "user_message",
                "user_id": user_id,
                "message": data
            }
            
            # Send message to admin if connected
            if admin_connection:
                try:
                    await admin_connection.send_text(json.dumps(message_data))
                    logger.debug(f"Forwarded message from user {user_id} to admin")
                except Exception as e:
                    logger.error(f"Error sending user message to admin: {e}")
    
    except WebSocketDisconnect:
        logger.warning(f"User {user_id} WebSocket disconnected")
    except Exception as e:
        logger.error(f"Unexpected error in user WebSocket: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Remove user from connections
        if user_id in user_connections:
            del user_connections[user_id]
        
        # Notify admin about user disconnection if admin is connected
        if admin_connection:
            try:
                await admin_connection.send_text(json.dumps({
                    "type": "user_disconnected",
                    "user_id": user_id
                }))
            except Exception as e:
                logger.error(f"Error notifying admin about user disconnection: {e}")
        
        # Ensure the connection is closed
        try:
            await websocket.close()
        except Exception:
            pass

@router.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    """
    WebSocket endpoint for admin chat
    Handles incoming messages from admin and routes them to specific users
    """
    global admin_connection
    
    logger.info("Admin attempting to connect")
    
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        logger.info("Admin WebSocket connection accepted")
        
        # Set global admin connection
        admin_connection = websocket
        
        # Send initial list of connected users to admin
        try:
            await websocket.send_text(json.dumps({
                "type": "initial_users",
                "users": list(user_connections.keys())
            }))
            logger.info(f"Sent initial user list to admin: {list(user_connections.keys())}")
        except Exception as e:
            logger.error(f"Error sending initial users to admin: {e}")
        
        while True:
            # Receive message from admin
            data = await websocket.receive_text()
            logger.debug(f"Received message from admin: {data}")
            
            # Parse the message
            try:
                message_data = json.loads(data)
                
                # Ensure the message has the correct format
                if message_data.get("type") == "admin_message":
                    user_id = message_data.get("user_id")
                    message = message_data.get("message")
                    
                    # Send message to specific user
                    if user_id and message and user_id in user_connections:
                        try:
                            await user_connections[user_id].send_text(
                                json.dumps({
                                    "type": "admin_message",
                                    "message": message
                                })
                            )
                            logger.debug(f"Sent admin message to user {user_id}")
                        except Exception as e:
                            logger.error(f"Error sending admin message to user {user_id}: {e}")
            except json.JSONDecodeError:
                # Handle invalid JSON
                logger.error("Received invalid JSON from admin")
    
    except WebSocketDisconnect:
        logger.warning("Admin WebSocket disconnected")
    except Exception as e:
        logger.error(f"Unexpected error in admin WebSocket: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Reset admin connection
        admin_connection = None
        
        # Ensure the connection is closed
        try:
            await websocket.close()
        except Exception:
            pass
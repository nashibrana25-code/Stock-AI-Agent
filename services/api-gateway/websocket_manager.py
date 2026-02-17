"""
WebSocket manager for real-time updates to clients

Handles real-time communication between the AI agent and web clients
"""
from typing import List, Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
import json
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Active connections: {user_id: [websockets]}
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
        # Subscriptions: {symbol: set(user_ids)}
        self.stock_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new client"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"Client {user_id} connected. Total connections: {self._count_connections()}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a client"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                # Remove all subscriptions
                for symbol in list(self.stock_subscriptions.keys()):
                    self.stock_subscriptions[symbol].discard(user_id)
        
        logger.info(f"Client {user_id} disconnected. Total connections: {self._count_connections()}")
    
    def subscribe_to_stock(self, user_id: str, symbol: str):
        """Subscribe user to stock updates"""
        if symbol not in self.stock_subscriptions:
            self.stock_subscriptions[symbol] = set()
        
        self.stock_subscriptions[symbol].add(user_id)
        logger.info(f"User {user_id} subscribed to {symbol}")
    
    def unsubscribe_from_stock(self, user_id: str, symbol: str):
        """Unsubscribe user from stock updates"""
        if symbol in self.stock_subscriptions:
            self.stock_subscriptions[symbol].discard(user_id)
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to a specific user"""
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to {user_id}: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws, user_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)
    
    async def broadcast_stock_update(self, symbol: str, data: dict):
        """Broadcast stock update to subscribers"""
        if symbol in self.stock_subscriptions:
            message = {
                "type": "stock_update",
                "symbol": symbol,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for user_id in self.stock_subscriptions[symbol]:
                await self.send_personal_message(message, user_id)
    
    async def broadcast_prediction_update(self, predictions: dict):
        """Broadcast new AI predictions"""
        message = {
            "type": "prediction_update",
            "predictions": predictions,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_all(message)
    
    async def broadcast_recommendation_update(self, recommendation: dict):
        """Broadcast new recommendations"""
        message = {
            "type": "recommendation_update",
            "recommendation": recommendation,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_all(message)
    
    async def send_alert(self, user_id: str, alert: dict):
        """Send alert to specific user"""
        message = {
            "type": "alert",
            "alert": alert,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_personal_message(message, user_id)
    
    def _count_connections(self) -> int:
        """Count total active connections"""
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_connections": self._count_connections(),
            "total_users": len(self.active_connections),
            "stock_subscriptions": {
                symbol: len(users) 
                for symbol, users in self.stock_subscriptions.items()
            }
        }


# Global connection manager
manager = ConnectionManager()

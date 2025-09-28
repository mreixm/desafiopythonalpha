
import json
import asyncio
from typing import List, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from app.config import get_settings
from app.models.data_models import WebSocketMessage, WebSocketMessageType, SheetData
from app.utils.logger import get_logger

logger = get_logger("websocket_service")


class WebSocketManager:
    
    def __init__(self):
        self.settings = get_settings()
        self._active_connections: Set[WebSocket] = set()
        self._connection_lock = asyncio.Lock()
    
    @property
    def connection_count(self) -> int:
        return len(self._active_connections)
    
    async def connect(self, websocket: WebSocket) -> bool:

        try:
            if self.connection_count >= self.settings.max_connections:
                logger.warning(f"Limite de conexões atingido: {self.settings.max_connections}")
                await websocket.close(code=1008, reason="Server full")
                return False
            
            await websocket.accept()
            
            async with self._connection_lock:
                self._active_connections.add(websocket)
            
            logger.info(f"Nova conexão WebSocket aceita. Total: {self.connection_count}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao conectar WebSocket: {e}")
            return False
    
    async def disconnect(self, websocket: WebSocket, reason: str = "Client disconnected") -> None:
        try:
            async with self._connection_lock:
                if websocket in self._active_connections:
                    self._active_connections.remove(websocket)
                    logger.info(f"Conexão WebSocket removida ({reason}). Total: {self.connection_count}")
                    
        except Exception as e:
            logger.error(f"Erro ao desconectar WebSocket: {e}")
    
    async def broadcast_data_update(self, sheet_data: SheetData) -> int:
        if not self._active_connections:
            return 0
        
        message = WebSocketMessage(
            type=WebSocketMessageType.DATA_UPDATE,
            data=[record.data for record in sheet_data.records],
            timestamp=sheet_data.timestamp
        )
        
        return await self._broadcast_message(message)
    
    async def send_initial_data(self, websocket: WebSocket, sheet_data: SheetData) -> bool:
        message = WebSocketMessage(
            type=WebSocketMessageType.INITIAL_DATA,
            data=[record.data for record in sheet_data.records],
            timestamp=sheet_data.timestamp
        )
        
        return await self._send_message(websocket, message)
    
    async def broadcast_error(self, error_message: str) -> int:
        message = WebSocketMessage(
            type=WebSocketMessageType.ERROR,
            error=error_message
        )
        
        return await self._broadcast_message(message)
    
    async def _broadcast_message(self, message: WebSocketMessage) -> int:
        if not self._active_connections:
            return 0
        
        connections = list(self._active_connections)
        message_json = message.json()
        
        successful_sends = 0
        failed_connections = []
        
        for websocket in connections:
            try:
                await websocket.send_text(message_json)
                successful_sends += 1
                
            except WebSocketDisconnect:
                failed_connections.append(websocket)
                logger.debug("Conexão WebSocket desconectada durante broadcast")
                
            except Exception as e:
                failed_connections.append(websocket)
                logger.warning(f"Erro ao enviar mensagem via WebSocket: {e}")
        
        if failed_connections:
            async with self._connection_lock:
                for failed_conn in failed_connections:
                    self._active_connections.discard(failed_conn)
            
            logger.info(f"Removidas {len(failed_connections)} conexões inválidas")
        
        logger.debug(f"Broadcast enviado para {successful_sends}/{len(connections)} conexões")
        return successful_sends
    
    async def _send_message(self, websocket: WebSocket, message: WebSocketMessage) -> bool:

        try:
            await websocket.send_text(message.json())
            return True
            
        except WebSocketDisconnect:
            await self.disconnect(websocket, "Connection lost during send")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para WebSocket específico: {e}")
            await self.disconnect(websocket, f"Send error: {e}")
            return False
    
    async def handle_client_message(self, websocket: WebSocket, message: str) -> None:
        try:
            if message.strip().lower() == "ping":
                pong_message = WebSocketMessage(
                    type=WebSocketMessageType.PONG,
                    message="pong"
                )
                await self._send_message(websocket, pong_message)
                
        except Exception as e:
            logger.error(f"Erro ao processar mensagem do cliente: {e}")
    
    async def cleanup_stale_connections(self) -> int:
        if not self._active_connections:
            return 0
        
        connections = list(self._active_connections)
        stale_connections = []
        
        for websocket in connections:
            try:
                ping_message = WebSocketMessage(
                    type=WebSocketMessageType.PING,
                    message="health_check"
                )
                await asyncio.wait_for(
                    self._send_message(websocket, ping_message),
                    timeout=5.0
                )
                
            except (asyncio.TimeoutError, Exception):
                stale_connections.append(websocket)
        
        if stale_connections:
            async with self._connection_lock:
                for stale_conn in stale_connections:
                    self._active_connections.discard(stale_conn)
            
            logger.info(f"Limpeza: {len(stale_connections)} conexões stale removidas")
        
        return len(stale_connections)
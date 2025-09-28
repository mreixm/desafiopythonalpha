from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.models.data_models import APIResponse, HealthCheck
from app.services.sheet_service import SheetService, SheetServiceError
from app.services.websocket_service import WebSocketManager
from app.utils.logger import get_logger

logger = get_logger("api_routes")

sheet_service = SheetService()
websocket_manager = WebSocketManager()

templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def read_root(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Erro ao carregar página principal: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    try:
        return HealthCheck(
            status="healthy",
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        raise HTTPException(status_code=500, detail="Sistema indisponível")


@router.get("/api/data", response_model=APIResponse, tags=["Data"])
async def get_data():
    try:
        logger.info("Requisição de dados via API REST")
        
        sheet_data = await sheet_service.fetch_sheet_data()
        
        data_list = [record.data for record in sheet_data.records]
        
        return APIResponse(
            success=True,
            data=data_list,
            message="Dados obtidos com sucesso",
            total_records=sheet_data.total_records,
            timestamp=sheet_data.timestamp
        )
        
    except SheetServiceError as e:
        logger.error(f"Erro do serviço de planilha: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Erro ao buscar dados da planilha"
        )
        
    except Exception as e:
        logger.error(f"Erro inesperado na API de dados: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Erro interno do servidor"
        )


@router.get("/api/stats", tags=["Data"])
async def get_stats():
    try:
        cached_data = sheet_service.get_cached_data()
        
        return {
            "websocket_connections": websocket_manager.connection_count,
            "cached_records": cached_data.total_records if cached_data else 0,
            "last_update": cached_data.timestamp if cached_data else None,
            "system_status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter estatísticas")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if not await websocket_manager.connect(websocket):
        logger.warning("Conexão WebSocket rejeitada")
        return
    
    try:
        cached_data = sheet_service.get_cached_data()
        if cached_data:
            await websocket_manager.send_initial_data(websocket, cached_data)
        
        while True:
            try:
                message = await websocket.receive_text()
                await websocket_manager.handle_client_message(websocket, message)
                
            except WebSocketDisconnect:
                break
                
            except Exception as e:
                logger.error(f"Erro na comunicação WebSocket: {e}")
                break
    
    except Exception as e:
        logger.error(f"Erro crítico no WebSocket: {e}")
    
    finally:
        await websocket_manager.disconnect(websocket)


async def notify_data_update(sheet_data):
    try:
        if websocket_manager.connection_count > 0:
            sent_count = await websocket_manager.broadcast_data_update(sheet_data)
            logger.info(f"Notificação enviada para {sent_count} clientes")
        
    except Exception as e:
        logger.error(f"Erro ao notificar clientes: {e}")


async def notify_error(error_message: str):
    try:
        if websocket_manager.connection_count > 0:
            sent_count = await websocket_manager.broadcast_error(error_message)
            logger.info(f"Notificação de erro enviada para {sent_count} clientes")
            
    except Exception as e:
        logger.error(f"Erro ao notificar erro para clientes: {e}")
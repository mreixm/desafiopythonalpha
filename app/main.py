import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.api.routes import router, notify_data_update, notify_error, sheet_service
from app.utils.logger import setup_logging, get_logger

settings = get_settings()
setup_logging()
logger = get_logger("main")

scheduler: AsyncIOScheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando aplicação Desafio Python Alpha")
    
    try:
        logger.info("Carregando dados iniciais...")
        initial_data = await sheet_service.fetch_sheet_data()
        logger.info(f"Dados iniciais carregados: {initial_data.total_records} registros")
        
        await setup_scheduler()
        logger.info("Scheduler configurado e iniciado")
        
        logger.info("✅ Aplicação iniciada com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante inicialização: {e}")
    
    yield
    
    logger.info("Finalizando aplicação...")
    
    try:
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler finalizado")
            
    except Exception as e:
        logger.error(f"Erro durante finalização: {e}")
    
    logger.info("👋 Aplicação finalizada")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan
    )
    
    if settings.debug:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    app.include_router(router)
    
    return app


async def setup_scheduler():
    global scheduler
    
    try:
        scheduler = AsyncIOScheduler()
        
        scheduler.add_job(
            update_data_job,
            'interval',
            seconds=settings.update_interval_seconds,
            id='update_sheet_data',
            name='Atualização automática da planilha',
            max_instances=1  
        )
        
        scheduler.add_job(
            cleanup_websockets_job,
            'interval',
            minutes=5,
            id='cleanup_websockets',
            name='Limpeza de conexões WebSocket',
            max_instances=1
        )
        
        scheduler.start()
        logger.info(f"Scheduler configurado - Intervalo: {settings.update_interval_seconds}s")
        
    except Exception as e:
        logger.error(f"Erro ao configurar scheduler: {e}")
        raise


async def update_data_job():
    try:
        logger.debug("Executando atualização automática...")
        
        new_data = await sheet_service.fetch_sheet_data()
        
        if sheet_service.has_data_changed(new_data):
            logger.info("Dados modificados, notificando clientes")
            await notify_data_update(new_data)
        else:
            logger.debug("Nenhuma alteração nos dados")
            
    except Exception as e:
        logger.error(f"Erro na atualização automática: {e}")
        await notify_error(f"Erro na atualização: {str(e)}")


async def cleanup_websockets_job():
    try:
        from app.api.routes import websocket_manager
        
        cleaned = await websocket_manager.cleanup_stale_connections()
        if cleaned > 0:
            logger.info(f"Limpeza WebSocket: {cleaned} conexões removidas")
            
    except Exception as e:
        logger.error(f"Erro na limpeza de WebSockets: {e}")


app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Iniciando servidor em {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
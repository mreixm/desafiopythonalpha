import asyncio
from typing import List, Dict, Any, Optional
import httpx
from app.config import get_settings
from app.models.data_models import SheetData, SheetRecord
from app.utils.data_processor import DataProcessor
from app.utils.logger import get_logger

logger = get_logger("sheet_service")


class SheetServiceError(Exception):
    pass


class SheetService:
    
    def __init__(self):
        self.settings = get_settings()
        self.data_processor = DataProcessor()
        self._last_data: Optional[SheetData] = None
    
    async def fetch_sheet_data(self) -> SheetData:
        try:
            logger.info("Iniciando busca de dados da planilha")
            
            timeout = httpx.Timeout(self.settings.request_timeout)
            
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                csv_content = await self._fetch_with_retry(client)
                
                processed_data = await self._process_csv_data(csv_content)
                
                sheet_data = SheetData(
                    records=[SheetRecord(data=record) for record in processed_data],
                    total_records=len(processed_data)
                )
                
                self._last_data = sheet_data
                
                logger.info(f"Dados obtidos com sucesso: {sheet_data.total_records} registros")
                return sheet_data
                
        except Exception as e:
            logger.error(f"Erro ao buscar dados da planilha: {e}")
            raise SheetServiceError(f"Falha ao obter dados: {e}")
    
    async def _fetch_with_retry(self, client: httpx.AsyncClient) -> str:
        last_error = None
        
        for attempt in range(1, self.settings.max_retries + 1):
            try:
                logger.debug(f"Tentativa {attempt}/{self.settings.max_retries}")
                
                response = await client.get(self.settings.sheet_url)
                
                if response.status_code == 307 and 'location' in response.headers:
                    redirect_url = response.headers['location']
                    logger.debug(f"Seguindo redirect para: {redirect_url}")
                    response = await client.get(redirect_url)
                
                response.raise_for_status()
                
                logger.debug(f"Resposta recebida: {len(response.text)} caracteres")
                return response.text
                
            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Tentativa {attempt} falhou (erro de rede): {e}")
                
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(f"Tentativa {attempt} falhou (HTTP {e.response.status_code}): {e}")
                
            except Exception as e:
                last_error = e
                logger.warning(f"Tentativa {attempt} falhou (erro inesperado): {e}")
            
            if attempt < self.settings.max_retries:
                wait_time = 2 ** attempt  # 2, 4, 8 segundos
                logger.debug(f"Aguardando {wait_time}s antes da próxima tentativa")
                await asyncio.sleep(wait_time)
        
        raise SheetServiceError(f"Todas as {self.settings.max_retries} tentativas falharam. Último erro: {last_error}")
    
    async def _process_csv_data(self, csv_content: str) -> List[Dict[str, Any]]:
        try:
            loop = asyncio.get_event_loop()
            
            raw_data = await loop.run_in_executor(
                None, 
                self.data_processor.parse_csv_content, 
                csv_content
            )
            
            processed_data = await loop.run_in_executor(
                None,
                self.data_processor.clean_and_format_data,
                raw_data
            )
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Erro no processamento de dados CSV: {e}")
            raise SheetServiceError(f"Falha no processamento: {e}")
    
    def get_cached_data(self) -> Optional[SheetData]:
        return self._last_data
    
    def has_data_changed(self, new_data: SheetData) -> bool:
        if not self._last_data:
            return True
        
        if self._last_data.total_records != new_data.total_records:
            return True
        
        old_records = [record.data for record in self._last_data.records]
        new_records = [record.data for record in new_data.records]
        
        return old_records != new_records
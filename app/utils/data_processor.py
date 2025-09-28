
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger("data_processor")


class DataProcessor:
    
    DATE_INDICATORS = ['data', 'date', 'created', 'updated', 'timestamp']
    NUMERIC_INDICATORS = ['valor', 'price', 'amount', 'total', 'quantidade', 'qtd', 'preco']
    
    @staticmethod
    def parse_csv_content(csv_content: str) -> List[Dict[str, Any]]:
        try:
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            raw_data = list(reader)
            logger.info(f"CSV parseado com sucesso: {len(raw_data)} registros brutos")
            
            return raw_data
            
        except Exception as e:
            logger.error(f"Erro ao fazer parse do CSV: {e}")
            raise ValueError(f"CSV inválido: {e}")
    
    @classmethod
    def clean_and_format_data(cls, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not raw_data:
            logger.warning("Nenhum dado para processar")
            return []
        
        try:
            processed_data = []
            
            for i, record in enumerate(raw_data):
                try:
                    if cls._is_empty_record(record):
                        continue
                    
                    processed_record = {}
                    for key, value in record.items():
                        clean_key = cls._clean_column_name(key)
                        clean_value = cls._process_field_value(clean_key, value)
                        processed_record[clean_key] = clean_value
                    
                    processed_data.append(processed_record)
                    
                except Exception as e:
                    logger.warning(f"Erro ao processar registro {i}: {e}")
                    continue
            
            logger.info(f"Dados processados com sucesso: {len(processed_data)} registros válidos")
            return processed_data
            
        except Exception as e:
            logger.error(f"Erro crítico no processamento de dados: {e}")
            return []
    
    @staticmethod
    def _is_empty_record(record: Dict[str, Any]) -> bool:
        return all(
            not value or str(value).strip() == '' 
            for value in record.values()
        )
    
    @staticmethod
    def _clean_column_name(column_name: str) -> str:
        if not column_name:
            return "unnamed_column"
        return str(column_name).strip()
    
    @classmethod
    def _process_field_value(cls, field_name: str, value: Any) -> str:
        if value is None or str(value).strip() == '':
            return ''
        
        clean_value = str(value).strip()
        field_lower = field_name.lower()
        
        if any(date_indicator in field_lower for date_indicator in cls.DATE_INDICATORS):
            formatted_date = cls._try_format_date(clean_value)
            if formatted_date:
                return formatted_date
        
        elif any(num_indicator in field_lower for num_indicator in cls.NUMERIC_INDICATORS):
            formatted_number = cls._try_format_number(clean_value)
            if formatted_number:
                return formatted_number
        
        return clean_value
    
    @staticmethod
    def _try_format_date(value: str) -> Optional[str]:
        date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
        
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(value, date_format)
                return parsed_date.strftime('%d/%m/%Y')
            except ValueError:
                continue
        
        logger.debug(f"Não foi possível formatar como data: {value}")
        return None
    
    @staticmethod
    def _try_format_number(value: str) -> Optional[str]:
        try:
            numeric_chars = ''.join(c for c in value if c.isdigit() or c in '.,')
            
            if not numeric_chars:
                return None
            
            numeric_value = numeric_chars.replace(',', '.')
            float_value = float(numeric_value)
            
            return f"R$ {float_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
        except (ValueError, TypeError):
            logger.debug(f"Não foi possível formatar como número: {value}")
            return None
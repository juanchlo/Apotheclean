
import pytest
from unittest.mock import Mock, call
from sqlalchemy.exc import OperationalError
from tenacity import RetryError

from src.infraestructure.resilience import retry_db_operation

class MockService:
    """Clase mock para probar el decorador."""
    def __init__(self):
        self.intentos = 0
        self.mock_method = Mock()

    @retry_db_operation
    def operacion_inestable(self):
        self.intentos += 1
        self.mock_method()
        if self.intentos < 3:
            raise OperationalError("Connection dropped", params=None, orig=None)
        return "Exito"

    @retry_db_operation
    def operacion_siempre_falla(self):
        self.intentos += 1
        self.mock_method()
        raise OperationalError("Connection dropped forever", params=None, orig=None)

    @retry_db_operation
    def operacion_error_no_manejado(self):
        self.intentos += 1
        self.mock_method()
        raise ValueError("Error de negocio")


class TestResilience:
    """Tests para el módulo de resiliencia."""

    def test_retry_db_operation_exito_eventual(self):
        """Verifica que reintenta hasta tener éxito (máx 3 veces)."""
        service = MockService()
        
        # Debe fallar 2 veces y pasar a la 3ra
        resultado = service.operacion_inestable()
        
        assert resultado == "Exito"
        assert service.intentos == 3
        assert service.mock_method.call_count == 3

    def test_retry_db_operation_max_retries_exceeded(self):
        """Verifica que lanza RetryError después de agotarlos intentos."""
        service = MockService()
        
        # Debe lanzar RetryError después de 3 intentos
        with pytest.raises(RetryError):
            service.operacion_siempre_falla()
        
        assert service.intentos == 3
        # Tenacity llama al método 3 veces
        assert service.mock_method.call_count == 3

    def test_retry_db_operation_no_atrapa_otros_errores(self):
        """Verifica que no atrapa excepciones que no sean OperationalError."""
        service = MockService()
        
        # Debe lanzar ValueError inmediatamente
        with pytest.raises(ValueError):
            service.operacion_error_no_manejado()
        
        assert service.intentos == 1
        assert service.mock_method.call_count == 1

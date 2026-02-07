"""
Módulo para manejar la resiliencia en operaciones de base de datos.
Provee decoradores para reintentar transacciones fallidas por errores de conexión.
"""

import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

def log_retry_attempt(retry_state):
    """Loguea cada intento de reintento."""
    logger.warning(
        f"Reintentando operación de BD debido a error de conexión (Intento {retry_state.attempt_number}): {retry_state.outcome.exception()}"
    )

# Decorador reutilizable para operaciones de base de datos
retry_db_operation = retry(
    # Reintentar solo si es un OperationalError (conexión, deadlock, etc.)
    retry=retry_if_exception_type(OperationalError),
    # Máximo 3 intentos
    stop=stop_after_attempt(3),
    # Espera exponencial: 1s, 2s, 4s...
    wait=wait_exponential(multiplier=1, min=1, max=10),
    # Loguear cada reintento
    before_sleep=log_retry_attempt,
    # No reraise=True por defecto deja que tenacity propague la última excepción
)

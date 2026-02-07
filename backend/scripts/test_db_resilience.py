import sys
import logging
from sqlalchemy.exc import OperationalError
from tenacity import RetryError

# Configurar logging para ver los reintentos
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_resilience")

# Importar el decorador
# Asegurarse de estar en el root del proyecto para ejecutar: python -m scripts.test_db_resilience
try:
    from src.infraestructure.resilience import retry_db_operation
except ImportError:
    # Fallback si se ejecuta directamente desde scripts/
    sys.path.append('.')
    from src.infraestructure.resilience import retry_db_operation


class MockRepo:
    def __init__(self):
        self.intentos = 0

    @retry_db_operation
    def operacion_inestable(self):
        self.intentos += 1
        logger.info(f"Ejecutando operación (Intento {self.intentos})")
        
        if self.intentos < 3:
            logger.warning("Simulando fallo de conexión...")
            raise OperationalError("Connection dropped", params=None, orig=None)
        
        logger.info("Operación exitosa!")
        return "Exito"


def run_test():
    print("\n--- Test de Resiliencia de DB ---\n")
    
    repo = MockRepo()
    
    try:
        resultado = repo.operacion_inestable()
        print(f"\nResultado final: {resultado}")
        
        if repo.intentos == 3:
            print("TEST PASSED: La operación se reintentó 3 veces y tuvo éxito al final.")
        else:
            print(f"TEST FAILED: Se esperaban 3 intentos, ocurrieron {repo.intentos}.")
            
    except RetryError:
        print("TEST FAILED: Se agotaron los reintentos sin éxito.")
    except Exception as e:
        print(f"TEST FAILED: Excepción no esperada: {e}")


if __name__ == "__main__":
    run_test()

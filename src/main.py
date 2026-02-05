"""
Punto de entrada principal de la aplicación Apotheclean.
"""

import os
import sys
from pathlib import Path

# Agregar src al path para permitir imports absolutos
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv

# Cargar variables de entorno desde .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from infraestructure.api.app import crear_app


def main():
    """
    Inicializa y ejecuta el servidor Flask.

    Lee la configuración de variables de entorno:
        - JWT_SECRET_KEY: Clave secreta para tokens JWT (requerida)
        - FLASK_HOST: Host del servidor (default: 0.0.0.0)
        - FLASK_PORT: Puerto del servidor (default: 5000)
        - FLASK_DEBUG: Modo debug (default: False)
    """
    # Verificar que JWT_SECRET_KEY esté configurada
    if not os.getenv("JWT_SECRET_KEY"):
        print("ERROR: La variable de entorno JWT_SECRET_KEY es requerida")
        print("Ejemplo: JWT_SECRET_KEY='mi_clave_secreta' uv run python -m src.main")
        return

    # Crear aplicación
    app = crear_app()

    # Configuración del servidor
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    print(f"\n{'='*50}")
    print("  APOTHECLEAN API")
    print(f"{'='*50}")
    print(f"  Servidor: http://{host}:{port}")
    print(f"  Modo debug: {debug}")
    print(f"{'='*50}\n")

    # Ejecutar servidor
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()

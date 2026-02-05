"""
Configuración global de pytest.

Agrega el directorio src al path para permitir imports absolutos en los tests.
"""

import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

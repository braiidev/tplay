"""Pone la raíz del repo en sys.path para que los tests importen `player`.

Sin esto, `pytest` pelado falla con `ModuleNotFoundError: No module named
'player'` (6 errores de colección). `python3 -m pytest` sí funcionaba porque
mete '' en sys.path[0], pero cualquier otra forma de correr los tests —el
runner de un editor, un CI, o el propio e2e de instalación— fallaba. pyproject
declara el paquete como instalable, así que también funciona instalado.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

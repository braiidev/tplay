"""Permite `python -m player`, que es lo que documentaba el README.

El README decía `python3 -m player` pero el archivo no existía, así que el
comando fallaba con "No module named player.__main__". Ahora hay entry point de
consola (tplay, vía pyproject [project.scripts]) y también -m.
"""

from . import main

if __name__ == "__main__":
    main()

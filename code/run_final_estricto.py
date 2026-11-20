"""
Revisión (20/11/2026), pedido B.2: corre run_final.py (a5cb66c3424f) sin cambios con el adaptador ESTRICTO
(ivol_adapter_estricto.py: OI >= 100 para que una opción de EE.UU. sea pata). framework.py 221320a15437 sin tocar.
Mismos argumentos que run_final.py.
"""
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ivol_adapter_estricto

sys.modules["ivol_adapter"] = ivol_adapter_estricto
runpy.run_path(str(Path(__file__).parent / "run_final.py"), run_name="__main__")

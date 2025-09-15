"""Docling Tool - Document Processing Package.

Este pacote fornece ferramentas para processamento em lote de documentos
usando a biblioteca docling, com interfaces CLI e GUI.
"""

__version__ = "1.0.0"
__author__ = "eduoncode"

# Exportar funções principais
from .main import build_converter, ensure_dir, process_file, run, setup_logging

__all__ = [
    "build_converter",
    "ensure_dir", 
    "process_file",
    "run",
    "setup_logging"
]

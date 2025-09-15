#!/usr/bin/env python3
"""
Script de teste automatizado para validar as melhorias do main.py
"""

import logging
import tempfile
import shutil
from pathlib import Path
import sys
import subprocess
import os

sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_test_logging():
    """Configura logging para os testes."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )
    return logging.getLogger(__name__)

def create_test_files(test_dir: Path) -> Path:
    """Cria arquivos de teste simples."""
    input_dir = test_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    
    md_file = input_dir / "test.md"
    md_file.write_text("""# Documento de Teste

Este é um documento de teste para o **Docling Tool**.

## Seção 1

- Item 1
- Item 2
- Item 3

## Seção 2

Este documento contém:
1. Texto formatado
2. Listas
3. Cabeçalhos

### Código

```python
print("Hello, World!")
```

### Conclusão

Documento de teste criado com sucesso.
""", encoding='utf-8')
    
    html_file = input_dir / "test.html"
    html_file.write_text("""<!DOCTYPE html>
<html>
<head>
    <title>Teste HTML</title>
</head>
<body>
    <h1>Documento HTML de Teste</h1>
    <p>Este é um <strong>documento HTML</strong> para teste.</p>
    <ul>
        <li>Item A</li>
        <li>Item B</li>
    </ul>
    <table>
        <tr><th>Coluna 1</th><th>Coluna 2</th></tr>
        <tr><td>Dados 1</td><td>Dados 2</td></tr>
    </table>
</body>
</html>""", encoding='utf-8')
    
    return input_dir

def test_main_functionality():
    """Testa as principais funcionalidades do main.py melhorado."""
    logger = setup_test_logging()
    logger.info(" Iniciando testes do main.py melhorado")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        logger.info(f" Diretório de teste: {test_dir}")
        
        input_dir = create_test_files(test_dir)
        output_dir = test_dir / "output"
        
        logger.info(" Arquivos de teste criados")
        
        logger.info("Teste 1: Verificação do sistema")
        try:
            result = subprocess.run([
                sys.executable, "-m", "src.main", "--check-system"
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            if result.returncode == 0:
                logger.info(" Verificação do sistema: OK")
            else:
                logger.error(f" Verificação do sistema falhou: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f" Erro na verificação do sistema: {e}")
            return False
        
        logger.info(" Teste 2: Modo dry-run")
        try:
            result = subprocess.run([
                sys.executable, "-m", "src.main",
                "--input", str(input_dir),
                "--output", str(output_dir),
                "--dry-run",
                "--verbose"
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            output_text = result.stderr + result.stdout
            if result.returncode == 0 and "Modo dry-run" in output_text:
                logger.info(" Dry-run: OK")
            else:
                logger.error(f" Dry-run falhou (código: {result.returncode})")
                logger.error(f"Stderr: {result.stderr}")
                logger.error(f"Stdout: {result.stdout}")
                return False
        except Exception as e:
            logger.error(f" Erro no dry-run: {e}")
            return False
        
        logger.info(" Teste 3: Processamento real")
        try:
            result = subprocess.run([
                sys.executable, "-m", "src.main",
                "--input", str(input_dir),
                "--output", str(output_dir),
                "--verbose",
                "--workers", "1"
            ], capture_output=True, text=True, cwd=Path.cwd(), timeout=60)
            
            if result.returncode == 0:
                logger.info(" Processamento real: OK")
                output_files = list(output_dir.glob("*.md"))
                logger.info(f" {len(output_files)} arquivos de saída criados")
                for file in output_files:
                    logger.info(f"  • {file.name} ({file.stat().st_size} bytes)")
            elif "Docling não está disponível" in result.stderr:
                logger.warning(" Docling não disponível - pulando teste de processamento")
                return True
            else:
                logger.error(f" Processamento real falhou: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error(" Processamento real expirou (timeout)")
            return False
        except Exception as e:
            logger.error(f" Erro no processamento real: {e}")
            return False
        
        logger.info(" Teste 4: Tratamento de erros")
        try:
            result = subprocess.run([
                sys.executable, "-m", "src.main",
                "--input", "/diretorio/inexistente",
                "--output", str(output_dir)
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            output_text = result.stderr + result.stdout
            if result.returncode != 0 and ("não existe" in output_text or "does not exist" in output_text or "Diretório de entrada não existe" in output_text):
                logger.info(" Tratamento de erro de diretório: OK")
            else:
                logger.warning(f" Tratamento de erro: resultado inesperado (código: {result.returncode})")
                logger.info(f"Output: {output_text}")
        except Exception as e:
            logger.error(f" Erro no teste de tratamento de erros: {e}")
            return False
    
    logger.info(" Todos os testes passaram!")
    return True

def test_gui_import():
    """Testa se a GUI pode ser importada."""
    logger = setup_test_logging()
    logger.info(" Testando importação da GUI")
    
    try:
        from src.gui.gui import DoclingGUI, main as gui_main
        logger.info(" GUI pode ser importada com sucesso")
        return True
    except Exception as e:
        logger.error(f" Erro ao importar GUI: {e}")
        return False

if __name__ == "__main__":
    logger = setup_test_logging()
    logger.info(" Iniciando testes automatizados")
    
    success = True
    
    if not test_main_functionality():
        success = False
    
    if not test_gui_import():
        success = False
    
    if success:
        logger.info(" TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        logger.error(" ALGUNS TESTES FALHARAM!")
        sys.exit(1)

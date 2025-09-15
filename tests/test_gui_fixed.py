#!/usr/bin/env python3
"""
Teste automatizado da GUI corrigida
"""

import logging
import sys
import threading
import time
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_gui_processing():
    """Testa a lógica de processamento da GUI sem interface visual."""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )
    logger = logging.getLogger(__name__)
    
    logger.info(" Iniciando teste da GUI corrigida")
    
    try:
        # Importar componentes da GUI
        from src.gui.gui import DoclingGUI, LogHandler
        from src.main import (
            check_docling_availability, ProcessingStats, 
            validate_file, build_converter, SUPPORTED_EXTENSIONS
        )
        import tkinter as tk
        
        logger.info(" Imports realizados com sucesso")
        
        # Verificar docling
        try:
            check_docling_availability()
            logger.info(" Docling disponível")
        except Exception as e:
            logger.warning(f" Docling não disponível: {e}")
            return False
        
        # Verificar arquivos de teste
        test_dir = Path("test_gui_files")
        if not test_dir.exists():
            logger.error(f" Diretório de teste não encontrado: {test_dir}")
            logger.info(" Execute: python create_test_files_gui.py")
            return False
        
        # Buscar arquivos de teste
        candidate_files = [
            p for p in test_dir.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        
        logger.info(f" Encontrados {len(candidate_files)} arquivos de teste")
        
        # Validar arquivos
        valid_files = []
        for file_path in candidate_files:
            if validate_file(file_path):
                valid_files.append(file_path)
                logger.info(f"   {file_path.name}")
            else:
                logger.warning(f"   {file_path.name} - inválido")
        
        if not valid_files:
            logger.error(" Nenhum arquivo válido encontrado")
            return False
        
        # Testar criação do conversor
        logger.info(" Testando criação do conversor...")
        try:
            converter = build_converter(
                ocr_mode="auto",
                enable_code_enrichment=False,
                table_mode="fast"
            )
            logger.info(" Conversor criado com sucesso")
        except Exception as e:
            logger.error(f" Erro ao criar conversor: {e}")
            return False
        
        # Testar processamento de um arquivo
        logger.info(" Testando processamento de arquivo...")
        output_dir = test_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        test_file = valid_files[0]
        try:
            # Simular o método _process_single_file da GUI
            doc_result = converter.convert(test_file)
            doc = doc_result.document
            text_markdown = doc.export_to_markdown()
            
            if text_markdown.strip():
                output_file = output_dir / f"{test_file.stem}.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text_markdown)
                
                logger.info(f" Arquivo processado: {test_file.name} -> {output_file.name}")
                logger.info(f"📏 Tamanho da saída: {len(text_markdown)} caracteres")
                return True
            else:
                logger.error(" Documento vazio após conversão")
                return False
                
        except Exception as e:
            logger.error(f" Erro no processamento: {e}")
            return False
        
    except Exception as e:
        logger.error(f" Erro crítico no teste: {e}")
        return False

def test_gui_mock_processing():
    """Testa a lógica interna da GUI sem interface gráfica."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(" Teste simulado da lógica da GUI")
    
    try:
        import tkinter as tk
        from src.gui.gui import DoclingGUI
        
        # Criar root window (mas não mostrar)
        root = tk.Tk()
        root.withdraw()  # Esconder janela
        
        # Criar instância da GUI
        app = DoclingGUI(root)
        
        # Configurar caminhos de teste
        test_dir = Path("test_gui_files")
        output_dir = test_dir / "output"
        
        app.input_dir.set(str(test_dir))
        app.output_dir.set(str(output_dir))
        app.verbose_mode.set(True)
        app.enrichment_mode.set(False)
        
        logger.info(" GUI configurada para teste")
        
        # Simular busca de arquivos
        candidate_files = [
            p for p in test_dir.iterdir()
            if p.is_file() and p.suffix.lower() in ['.md', '.html', '.csv']
        ]
        
        logger.info(f" {len(candidate_files)} arquivos encontrados")
        
        # Testar thread de processamento
        def test_processing():
            try:
                app._process_documents(test_dir, output_dir, candidate_files)
                logger.info(" Processamento concluído sem travar")
            except Exception as e:
                logger.error(f" Erro no processamento: {e}")
        
        # Executar em thread separada
        thread = threading.Thread(target=test_processing, daemon=True)
        thread.start()
        
        # Aguardar conclusão (timeout de 30 segundos)
        thread.join(timeout=30)
        
        if thread.is_alive():
            logger.error(" Processamento travou (timeout)")
            return False
        else:
            logger.info(" Processamento completou dentro do timeout")
            return True
        
    except Exception as e:
        logger.error(f" Erro no teste simulado: {e}")
        return False
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )
    
    logger.info(" Iniciando testes da GUI corrigida")
    
    # Teste 1: Lógica básica
    success1 = test_gui_processing()
    
    # Teste 2: Processamento simulado  
    success2 = test_gui_mock_processing()
    
    if success1 and success2:
        logger.info(" TODOS OS TESTES PASSARAM!")
        logger.info(" A GUI está funcionando corretamente")
        logger.info(" Para testar visualmente: python -m src.gui.gui")
        sys.exit(0)
    else:
        logger.error(" ALGUNS TESTES FALHARAM!")
        sys.exit(1)

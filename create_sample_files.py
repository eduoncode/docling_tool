#!/usr/bin/env python3
"""Exemplo simples para testar a GUI do Docling Tool."""

import tempfile
from pathlib import Path

def create_sample_files():
    """Cria arquivos de exemplo para testar a GUI."""
    # Criar diretório temporário
    temp_dir = Path(tempfile.mkdtemp(prefix="docling_test_"))
    
    # Criar diretório de entrada
    input_dir = temp_dir / "sample_input"
    input_dir.mkdir()
    
    # Criar arquivos de exemplo
    files_to_create = {
        "sample1.txt": "Este é um arquivo de texto de exemplo.\nEle contém múltiplas linhas.",
        "sample2.pdf": "Conteúdo simulado de PDF (na realidade seria binário)",
        "sample3.docx": "Conteúdo simulado de DOCX (na realidade seria binário)",
        "readme.md": "# Documento de Exemplo\n\nEste é um arquivo Markdown de exemplo."
    }
    
    for filename, content in files_to_create.items():
        file_path = input_dir / filename
        file_path.write_text(content, encoding="utf-8")
        print(f"Created: {file_path}")
    
    # Criar diretório de saída
    output_dir = temp_dir / "sample_output"
    output_dir.mkdir()
    
    print(f"\nSample files created in: {temp_dir}")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    return input_dir, output_dir

if __name__ == "__main__":
    print("Creating sample files for Docling Tool GUI testing...")
    input_dir, output_dir = create_sample_files()
    
    print("\nTo test the GUI:")
    print("1. Run: python -m src.gui.gui")
    print(f"2. Set input directory to: {input_dir}")
    print(f"3. Set output directory to: {output_dir}")
    print("4. Click 'Start Processing'")
    print("\nNote: The processing may fail if 'docling' package is not installed,")
    print("but you can still test the GUI interface functionality.")

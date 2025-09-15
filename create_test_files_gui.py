#!/usr/bin/env python3
"""
Script para criar arquivos de teste para a GUI do Docling Tool
"""

import tempfile
from pathlib import Path

def create_test_files() -> Path:
    """Cria arquivos de teste em um diretório temporário."""
    
    # Criar diretório temporário que persiste
    test_dir = Path.cwd() / "test_gui_files"
    test_dir.mkdir(exist_ok=True)
    
    print(f" Criando arquivos de teste em: {test_dir}")
    
    # Arquivo Markdown
    md_file = test_dir / "teste.md"
    md_file.write_text("""# Documento de Teste para GUI

Este é um **documento de teste** para verificar se a GUI do Docling Tool está funcionando corretamente.

## Características do Teste

-  Texto em português
-  Formatação Markdown
-  Emojis e símbolos especiais
-  Listas e estruturas

### Lista de Verificação

1.  Arquivo criado
2.  Processamento na GUI
3.  Arquivo de saída gerado

### Código de Exemplo

```python
def teste_gui():
    print("Testando a GUI do Docling Tool")
    return "Sucesso!"
```

**Fim do documento de teste.**
""", encoding='utf-8')
    
    # Arquivo HTML
    html_file = test_dir / "teste.html"
    html_file.write_text("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Teste HTML para GUI</title>
</head>
<body>
    <h1>Documento HTML de Teste</h1>
    
    <p>Este é um documento <strong>HTML</strong> para testar a GUI do Docling Tool.</p>
    
    <h2>Lista de Funcionalidades</h2>
    <ul>
        <li>Conversão de HTML para Markdown</li>
        <li>Processamento via GUI</li>
        <li>Logs em tempo real</li>
    </ul>
    
    <h2>Tabela de Teste</h2>
    <table border="1">
        <tr>
            <th>Recurso</th>
            <th>Status</th>
        </tr>
        <tr>
            <td>Importação HTML</td>
            <td> OK</td>
        </tr>
        <tr>
            <td>Conversão</td>
            <td> Testando</td>
        </tr>
    </table>
    
    <p><em>Arquivo de teste criado com sucesso!</em></p>
</body>
</html>""", encoding='utf-8')
    
    # Arquivo CSV
    csv_file = test_dir / "teste.csv"
    csv_file.write_text("""Nome,Idade,Cidade
João,25,São Paulo
Maria,30,Rio de Janeiro
Pedro,35,Belo Horizonte
Ana,28,Porto Alegre
""", encoding='utf-8')
    
    print(f" Criados arquivos de teste:")
    for file in test_dir.iterdir():
        if file.is_file():
            size = file.stat().st_size
            print(f"  • {file.name} ({size} bytes)")
    
    print(f"\n Para testar a GUI:")
    print(f"1. Execute: python -m src.gui.gui")
    print(f"2. Input Directory: {test_dir}")
    print(f"3. Output Directory: {test_dir / 'output'}")
    print(f"4. Clique em 'Start Processing'")
    
    return test_dir

if __name__ == "__main__":
    create_test_files()

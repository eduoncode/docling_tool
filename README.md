# docling_tool

Script para processar documentos e extrair Markdown usando `docling`.

Melhorias aplicadas ao script original:

- Estrutura modular (funções reutilizáveis)
- Logging configurável
- CLI com argparse
- Testes unitários com pytest (mock)

Requisitos
---------

- Python 3.8+
- pacote `docling` (instalar conforme instruções do seu ambiente)
- pytest (para rodar testes)

Uso rápido
---------

Executar o script:

```bash
python process.py --input documentos_entrada --output textos_saida
```

Ativar verbose:

```bash
python process.py -v
```

Testes
------

Instalar pytest e executar:

```bash
pip install pytest
pytest -q
```

"""Processamento em lote de documentos usando docling.

Melhorias aplicadas:
- organização em funções
- tipagem estática mínima
- logging em vez de print
- interface de linha de comando com argparse
- função run(argv) para facilitar testes
"""

from __future__ import annotations

import argparse
import logging
import sys
import tempfile
from pathlib import Path
from typing import Any, List, Optional


logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_converter(ocr_mode: str = "always") -> Any:
    """Cria e configura o DocumentConverter do docling.

    Args:
        ocr_mode: valor para ConversionConfig.ocr_config['run'] (ex: 'always', 'auto', 'never')
    """
    # Importar localmente para permitir que o módulo seja importado em ambientes
    # sem o pacote `docling` instalado (útil para testes que mockam o builder).
    from docling.converter import ConversionConfig, DocumentConverter  # type: ignore

    config = ConversionConfig(ocr_config={"run": ocr_mode})
    return DocumentConverter(config=config)


def process_file(converter: DocumentConverter, input_path: Path, output_dir: Path) -> Path:
    """Processa um único arquivo e grava o resultado em Markdown.

    Retorna o caminho do arquivo gravado.
    """
    logger.debug("Processing: %s", input_path)
    doc = converter.convert(input_path)
    text_markdown = doc.to_markdown()

    nome_arquivo_saida = f"{input_path.stem}.md"
    path_output_file = output_dir / nome_arquivo_saida

    # Cria arquivo temporario
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmpf:
        tmpf.write(text_markdown)
        tmp_name = Path(tmpf.name)

    tmp_name.replace(path_output_file)
    logger.info("-> Resultado salvo em: %s", path_output_file)
    return path_output_file


def run(argv: Optional[List[str]] = None) -> int:
    """Ponto de entrada. Recebe argv (lista) semelhante a sys.argv[1:].

    Retorna 0 em sucesso, >0 em erro.
    """
    parser = argparse.ArgumentParser(description="Processa documentos e extrai Markdown usando docling.")
    parser.add_argument("--input", "-i", type=Path, default=Path("entry_files"), help="Diretório de entrada")
    parser.add_argument("--output", "-o", type=Path, default=Path("textos_saida"), help="Diretório de saída")
    parser.add_argument("--ocr", type=str, default="always", help="Modo OCR (ex: always, auto, never)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Ativa logging DEBUG")

    args = parser.parse_args(argv)

    setup_logging(args.verbose)

    input_dir: Path = args.input
    output_dir: Path = args.output

    ensure_dir(input_dir)
    ensure_dir(output_dir)

    logger.info("Diretório de entrada: '%s'", str(input_dir.resolve()))
    logger.info("Diretório de saída: '%s'", str(output_dir.resolve()))

    # Verificar se há arquivos a processar antes de criar o conversor.
    files_to_process = [p for p in input_dir.iterdir() if p.is_file() and not p.name.startswith('.')]
    if not files_to_process:
        logger.info("Nenhum arquivo no diretório de entrada: %s", input_dir)
        logger.info("-" * 30)
        logger.info("Nenhum arquivo processado.")
        return 0

    try:
        converter = build_converter(ocr_mode=args.ocr)
    except Exception:
        logger.exception("Falha ao construir o conversor docling")
        return 2

    any_processed = False
    for path in sorted(files_to_process):

        logger.info("Processando: %s", path.name)
        try:
            process_file(converter, path, output_dir)
            any_processed = True
        except Exception:
            logger.exception("Erro ao processar %s", path.name)

    logger.info("-" * 30)
    if any_processed:
        logger.info("Processamento em lote concluído!")
        return 0
    else:
        logger.info("Nenhum arquivo processado.")
        return 0


if __name__ == "__main__":
    raise SystemExit(run())

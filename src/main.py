from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed, Future
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import psutil
import signal

# Verificação robusta de importações do docling
DOCLING_AVAILABLE = False
DOCLING_ERROR = None

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat, DocumentStream
    from docling.datamodel.pipeline_options import (
        EasyOcrOptions, 
        PdfPipelineOptions, 
        TableFormerMode
    )
    from docling.utils.model_downloader import download_models
    DOCLING_AVAILABLE = True
except ImportError as e:
    DOCLING_ERROR = str(e)
    DocumentConverter = None


logger = logging.getLogger(__name__)

# Constantes melhoradas
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".pptx", ".md", ".html", ".xhtml", 
    ".csv", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"
}

DEFAULT_MAX_WORKERS = min(4, (os.cpu_count() or 1))
DEFAULT_TIMEOUT = 300  # 5 minutos por arquivo
DEFAULT_MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
DEFAULT_MAX_PAGES = 1000

@dataclass
class ProcessingStats:
    """Estatísticas de processamento."""
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    
    @property
    def duration(self) -> float:
        """Duração total do processamento."""
        return self.end_time - self.start_time if self.end_time > 0 else time.time() - self.start_time
    
    @property
    def success_rate(self) -> float:
        """Taxa de sucesso."""
        if self.total_files == 0:
            return 0.0
        return (self.successful / self.total_files) * 100


class DoclingError(Exception):
    """Exceção base para erros do Docling."""
    pass


class DocumentProcessingError(DoclingError):
    """Erro específico de processamento de documento."""
    pass


class ConfigurationError(DoclingError):
    """Erro de configuração."""
    pass


def setup_logging(verbose: bool = False, log_file: Optional[Path] = None) -> None:
    """
    Configura o sistema de logging com suporte a arquivo e formatação melhorada.
    
    Args:
        verbose: Se True, habilita logging DEBUG
        log_file: Caminho para arquivo de log (opcional)
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Formatador detalhado
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # Configurar logger root
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.setLevel(level)
    
    # Handler para arquivo se especificado
    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)  # Sempre DEBUG no arquivo
            root_logger.addHandler(file_handler)
            logger.info(f" Log file: {log_file}")
        except Exception as e:
            logger.warning(f" Não foi possível criar arquivo de log {log_file}: {e}")


def check_docling_availability() -> None:
    """
    Verifica se o docling está disponível e funcional.
    
    Raises:
        ConfigurationError: Se o docling não estiver disponível
    """
    if not DOCLING_AVAILABLE:
        error_msg = (
            f" Docling não está disponível: {DOCLING_ERROR}\n"
            " Para instalar: pip install docling\n"
            " Documentação: https://github.com/DS4SD/docling"
        )
        logger.error(error_msg)
        raise ConfigurationError(error_msg)
    
    logger.debug(" Docling está disponível e importado com sucesso")


def check_system_resources() -> Dict[str, Any]:
    """
    Verifica recursos do sistema disponíveis.
    
    Returns:
        Dicionário com informações de recursos
    """
    cpu_count = os.cpu_count() or 1
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    resources = {
        'cpu_count': cpu_count,
        'memory_total_gb': memory.total / (1024**3),
        'memory_available_gb': memory.available / (1024**3),
        'memory_percent': memory.percent,
        'disk_free_gb': disk.free / (1024**3)
    }
    
    logger.info(f" Sistema: {cpu_count} CPUs, "
               f"{resources['memory_available_gb']:.1f}GB RAM disponível "
               f"({resources['memory_percent']:.1f}% em uso)")
    
    # Avisos sobre recursos limitados
    if resources['memory_available_gb'] < 2:
        logger.warning(" Pouca memória disponível (<2GB). Considere usar menos workers.")
    
    if resources['disk_free_gb'] < 1:
        logger.warning(" Pouco espaço em disco (<1GB).")
    
    return resources


def ensure_dir(path: Path) -> None:
    """
    Cria diretório garantindo que existe e é acessível.
    
    Args:
        path: Caminho do diretório
        
    Raises:
        ConfigurationError: Se não conseguir criar o diretório
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f" Diretório garantido: {path}")
        
        # Verificar permissões
        if not os.access(path, os.W_OK):
            raise ConfigurationError(f"Sem permissão de escrita em: {path}")
            
    except Exception as e:
        error_msg = f"Erro ao criar diretório {path}: {e}"
        logger.error(f" {error_msg}")
        raise ConfigurationError(error_msg)


def validate_file(file_path: Path, max_size: int = DEFAULT_MAX_FILE_SIZE) -> bool:
    """
    Valida se um arquivo pode ser processado.
    
    Args:
        file_path: Caminho do arquivo
        max_size: Tamanho máximo em bytes
        
    Returns:
        True se o arquivo é válido
    """
    try:
        if not file_path.exists():
            logger.debug(f" Arquivo não existe: {file_path}")
            return False
            
        if not file_path.is_file():
            logger.debug(f" Não é um arquivo: {file_path}")
            return False
            
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.debug(f" Extensão não suportada: {file_path}")
            return False
            
        file_size = file_path.stat().st_size
        if file_size > max_size:
            logger.warning(f" Arquivo muito grande ({file_size / (1024**2):.1f}MB): {file_path}")
            return False
            
        if file_size == 0:
            logger.warning(f" Arquivo vazio: {file_path}")
            return False
            
        logger.debug(f" Arquivo válido: {file_path} ({file_size / (1024**2):.1f}MB)")
        return True
        
    except Exception as e:
        logger.error(f" Erro ao validar {file_path}: {e}")
        return False


def build_converter(
    ocr_mode: str = "always",
    enable_table_structure: bool = True,
    table_mode: str = "accurate",
    artifacts_path: Optional[Path] = None,
    enable_remote_services: bool = False,
    enable_code_enrichment: bool = False,
    enable_formula_enrichment: bool = False,
    enable_picture_classification: bool = False,
    enable_picture_description: bool = False
) -> DocumentConverter:
    """
    Cria e configura o DocumentConverter do docling com opções avançadas.
    
    Args:
        ocr_mode: Modo OCR ('always', 'auto', 'never')
        enable_table_structure: Habilitar reconhecimento de estrutura de tabelas
        table_mode: Modo TableFormer ('fast' ou 'accurate')
        artifacts_path: Caminho para modelos locais
        enable_remote_services: Permitir serviços remotos
        enable_code_enrichment: Enriquecer blocos de código
        enable_formula_enrichment: Enriquecer fórmulas
        enable_picture_classification: Classificar imagens
        enable_picture_description: Descrever imagens
        
    Returns:
        DocumentConverter configurado
        
    Raises:
        ConfigurationError: Se houver erro na configuração
    """
    try:
        logger.debug(f" Construindo conversor: OCR={ocr_mode}, tabela={enable_table_structure}")
        
        # Configurações de OCR
        if ocr_mode == "always":
            ocr_options = EasyOcrOptions(force_full_page_ocr=True)
        elif ocr_mode == "never":
            ocr_options = EasyOcrOptions(force_full_page_ocr=False)
        else:  # auto
            ocr_options = EasyOcrOptions()

        # Configurações de pipeline PDF
        pipeline_options = PdfPipelineOptions(
            do_ocr=(ocr_mode != "never"),
            ocr_options=ocr_options,
            do_table_structure=enable_table_structure,
            artifacts_path=str(artifacts_path) if artifacts_path else None,
            enable_remote_services=enable_remote_services
        )
        
        # Configurações de enriquecimento
        if enable_code_enrichment:
            pipeline_options.do_code_enrichment = True
            logger.debug(" Code enrichment habilitado")
            
        if enable_formula_enrichment:
            pipeline_options.do_formula_enrichment = True
            logger.debug(" Formula enrichment habilitado")
            
        if enable_picture_classification:
            pipeline_options.do_picture_classification = True
            logger.debug(" Picture classification habilitado")
            
        if enable_picture_description:
            pipeline_options.do_picture_description = True
            logger.debug(" Picture description habilitado")

        # Configurações de TableFormer
        if enable_table_structure:
            if table_mode == "fast":
                pipeline_options.table_structure_options.mode = TableFormerMode.FAST
                logger.debug(" TableFormer modo: FAST")
            else:
                pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
                logger.debug(" TableFormer modo: ACCURATE")
            
            # Opcionalmente desabilitar cell matching para melhor qualidade
            pipeline_options.table_structure_options.do_cell_matching = True

        # Criar conversor
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        logger.info(" Conversor criado com sucesso")
        return converter
        
    except Exception as e:
        error_msg = f"Erro ao criar conversor: {e}"
        logger.error(f" {error_msg}")
        raise ConfigurationError(error_msg)


def download_models_if_needed(force: bool = False) -> bool:
    """
    Baixa modelos do docling se necessário.
    
    Args:
        force: Forçar download mesmo se modelos existem
        
    Returns:
        True se modelos estão disponíveis
    """
    try:
        if force:
            logger.info(" Forçando download de modelos...")
            download_models()
            logger.info(" Modelos baixados com sucesso")
            return True
        else:
            logger.debug(" Verificando disponibilidade de modelos...")
            # Aqui você pode adicionar lógica para verificar se os modelos existem
            return True
            
    except Exception as e:
        logger.warning(f" Erro ao baixar modelos: {e}")
        return False


def process_file(
    input_path: Path, 
    output_dir: Path, 
    ocr_mode: str,
    max_pages: int = DEFAULT_MAX_PAGES,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    timeout: int = DEFAULT_TIMEOUT,
    enable_enrichment: bool = False,
    retry_count: int = 2
) -> Tuple[Path, Dict[str, Any]]:
    """
    Processa um único arquivo com retry e estatísticas detalhadas.

    Args:
        input_path: Caminho do arquivo de entrada
        output_dir: Diretório de saída
        ocr_mode: Modo OCR
        max_pages: Número máximo de páginas
        max_file_size: Tamanho máximo do arquivo
        timeout: Timeout em segundos
        enable_enrichment: Habilitar recursos de enriquecimento
        retry_count: Número de tentativas em caso de falha

    Returns:
        Tuple com caminho do arquivo de saída e estatísticas

    Raises:
        DocumentProcessingError: Se falhar no processamento
    """
    start_time = time.time()
    stats = {
        'file_size': 0,
        'pages_processed': 0,
        'processing_time': 0,
        'retry_attempts': 0,
        'errors': []
    }
    
    try:
        # Validar arquivo
        if not validate_file(input_path, max_file_size):
            raise DocumentProcessingError(f"Arquivo inválido: {input_path}")
        
        stats['file_size'] = input_path.stat().st_size
        
        logger.info(f" Processando: {input_path.name} ({stats['file_size'] / (1024**2):.1f}MB)")
        
        # Criar conversor específico para este processo
        converter = build_converter(
            ocr_mode=ocr_mode,
            enable_code_enrichment=enable_enrichment,
            enable_formula_enrichment=enable_enrichment,
            enable_picture_classification=enable_enrichment
        )
        
        # Tentativas com retry
        last_error = None
        for attempt in range(retry_count + 1):
            try:
                if attempt > 0:
                    stats['retry_attempts'] = attempt
                    logger.warning(f" Tentativa {attempt + 1}/{retry_count + 1}: {input_path.name}")
                    time.sleep(min(2 ** attempt, 10))  # Backoff exponencial
                
                # Processar com limite de páginas e timeout
                if input_path.suffix.lower() == '.pdf':
                    doc_result = converter.convert(
                        input_path, 
                        max_num_pages=max_pages,
                        max_file_size=max_file_size
                    )
                else:
                    doc_result = converter.convert(input_path)
                
                doc = doc_result.document
                
                # Estatísticas do documento
                if hasattr(doc, 'pages'):
                    stats['pages_processed'] = len(doc.pages)
                    logger.debug(f" {stats['pages_processed']} páginas processadas")
                
                # Exportar para markdown
                logger.debug(f" Exportando para Markdown: {input_path.name}")
                text_markdown = doc.export_to_markdown()
                
                if not text_markdown.strip():
                    raise DocumentProcessingError("Documento vazio após processamento")
                
                # Salvar arquivo
                output_filename = f"{input_path.stem}.md"
                path_output_file = output_dir / output_filename
                
                # Usar arquivo temporário para escrita atômica
                with tempfile.NamedTemporaryFile(
                    mode="w", 
                    encoding="utf-8", 
                    delete=False, 
                    dir=output_dir,
                    prefix=f"{input_path.stem}_",
                    suffix=".md.tmp"
                ) as tmpf:
                    tmpf.write(text_markdown)
                    tmp_path = Path(tmpf.name)

                # Mover arquivo temporário para destino final
                tmp_path.replace(path_output_file)
                
                # Calcular estatísticas finais
                stats['processing_time'] = time.time() - start_time
                output_size = path_output_file.stat().st_size
                
                logger.info(
                    f" Sucesso: {input_path.name} -> {path_output_file.name} "
                    f"({output_size / 1024:.1f}KB, {stats['processing_time']:.1f}s)"
                )
                
                return path_output_file, stats
                
            except Exception as e:
                last_error = e
                error_msg = f"Tentativa {attempt + 1} falhou: {str(e)}"
                stats['errors'].append(error_msg)
                logger.debug(f" {error_msg}")
                
                if attempt == retry_count:
                    break
        
        # Se chegou aqui, todas as tentativas falharam
        stats['processing_time'] = time.time() - start_time
        error_msg = f"Falha após {retry_count + 1} tentativas: {last_error}"
        logger.error(f" {input_path.name}: {error_msg}")
        raise DocumentProcessingError(error_msg)
        
    except Exception as e:
        stats['processing_time'] = time.time() - start_time
        if not isinstance(e, DocumentProcessingError):
            error_msg = f"Erro inesperado processando {input_path.name}: {e}"
            logger.error(f" {error_msg}")
            raise DocumentProcessingError(error_msg)
        raise


def signal_handler(signum, frame):
    """Handler para sinais de interrupção."""
    logger.warning(f" Sinal {signum} recebido. Finalizando processamento...")
    # Aqui você pode adicionar lógica de limpeza se necessário
    sys.exit(1)


def run(argv: Optional[List[str]] = None) -> int:
    """
    Ponto de entrada principal com validação robusta e logging detalhado.
    
    Returns:
        Código de saída (0=sucesso, 1=sucesso parcial, 2=falha total)
    """
    parser = argparse.ArgumentParser(
        description="Processa documentos e extrai Markdown usando docling.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s --input docs/ --output markdown/
  %(prog)s -i files/ -o out/ --ocr auto --workers 8 --verbose
  %(prog)s --download-models
  %(prog)s --enrichment --table-mode accurate --max-pages 50
        """
    )
    
    # Argumentos de entrada/saída
    parser.add_argument(
        "--input", "-i", 
        type=Path, 
        default=Path("entry_files"), 
        help="Diretório de entrada (padrão: entry_files)"
    )
    parser.add_argument(
        "--output", "-o", 
        type=Path, 
        default=Path("output_texts"), 
        help="Diretório de saída (padrão: output_texts)"
    )
    
    # Configurações de processamento
    parser.add_argument(
        "--ocr", 
        type=str, 
        default="always", 
        choices=["always", "auto", "never"], 
        help="Modo OCR (padrão: always)"
    )
    parser.add_argument(
        "--workers", "-w", 
        type=int, 
        default=DEFAULT_MAX_WORKERS, 
        help=f"Número de processos paralelos (padrão: {DEFAULT_MAX_WORKERS})"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=DEFAULT_TIMEOUT, 
        help=f"Timeout por arquivo em segundos (padrão: {DEFAULT_TIMEOUT})"
    )
    
    # Limites de arquivo
    parser.add_argument(
        "--max-file-size", 
        type=int, 
        default=DEFAULT_MAX_FILE_SIZE, 
        help=f"Tamanho máximo de arquivo em bytes (padrão: {DEFAULT_MAX_FILE_SIZE})"
    )
    parser.add_argument(
        "--max-pages", 
        type=int, 
        default=DEFAULT_MAX_PAGES, 
        help=f"Número máximo de páginas por documento (padrão: {DEFAULT_MAX_PAGES})"
    )
    
    # Configurações avançadas
    parser.add_argument(
        "--enrichment", 
        action="store_true", 
        help="Habilitar recursos de enriquecimento (código, fórmulas, imagens)"
    )
    parser.add_argument(
        "--table-mode", 
        choices=["fast", "accurate"], 
        default="accurate", 
        help="Modo TableFormer (padrão: accurate)"
    )
    parser.add_argument(
        "--disable-tables", 
        action="store_true", 
        help="Desabilitar reconhecimento de estrutura de tabelas"
    )
    parser.add_argument(
        "--artifacts-path", 
        type=Path, 
        help="Caminho para modelos locais"
    )
    parser.add_argument(
        "--remote-services", 
        action="store_true", 
        help="Permitir uso de serviços remotos"
    )
    
    # Configurações de retry e robustez
    parser.add_argument(
        "--retry", 
        type=int, 
        default=2, 
        help="Número de tentativas em caso de falha (padrão: 2)"
    )
    parser.add_argument(
        "--continue-on-error", 
        action="store_true", 
        help="Continuar processamento mesmo com erros"
    )
    
    # Logging e debug
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Ativa logging DEBUG"
    )
    parser.add_argument(
        "--log-file", 
        type=Path, 
        help="Arquivo para salvar logs"
    )
    parser.add_argument(
        "--quiet", "-q", 
        action="store_true", 
        help="Modo silencioso (apenas erros)"
    )
    
    # Utilitários
    parser.add_argument(
        "--download-models", 
        action="store_true", 
        help="Baixar modelos e sair"
    )
    parser.add_argument(
        "--check-system", 
        action="store_true", 
        help="Verificar recursos do sistema e sair"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Simular processamento sem executar"
    )

    args = parser.parse_args(argv)
    
    # Configurar logging
    if args.quiet:
        setup_logging(verbose=False, log_file=args.log_file)
        logging.getLogger().setLevel(logging.ERROR)
    else:
        setup_logging(args.verbose, args.log_file)
    
    # Configurar handlers de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(" Iniciando Docling Tool")
    logger.info(f" Argumentos: {' '.join(sys.argv[1:])}")
    
    try:
        # Verificar disponibilidade do docling
        check_docling_availability()
        
        # Verificar recursos do sistema
        if args.check_system:
            check_system_resources()
            return 0
        
        # Baixar modelos se solicitado
        if args.download_models:
            logger.info("Baixando modelos do docling...")
            download_models_if_needed(force=True)
            return 0
        
        # Verificar recursos do sistema
        resources = check_system_resources()
        
        # Ajustar número de workers baseado nos recursos
        if args.workers > resources['cpu_count']:
            logger.warning(f" Reduzindo workers de {args.workers} para {resources['cpu_count']} (CPUs disponíveis)")
            args.workers = resources['cpu_count']
        
        if resources['memory_available_gb'] < 2 and args.workers > 2:
            logger.warning(" Reduzindo workers devido à memória limitada")
            args.workers = 2
        
        # Validar diretórios
        input_dir: Path = args.input.resolve()
        output_dir: Path = args.output.resolve()
        
        if not input_dir.exists():
            logger.error(f" Diretório de entrada não existe: {input_dir}")
            return 2
        
        ensure_dir(output_dir)
        
        logger.info(f" Entrada: {input_dir}")
        logger.info(f" Saída: {output_dir}")
        
        # Buscar e validar arquivos
        logger.info(" Buscando arquivos para processar...")
        
        all_files = list(input_dir.rglob("*"))
        candidate_files = [
            p for p in all_files
            if p.is_file() and not p.name.startswith('.') and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        
        logger.info(f" Encontrados {len(candidate_files)} arquivos candidatos")
        
        # Validar arquivos
        files_to_process = []
        for file_path in sorted(candidate_files):
            if validate_file(file_path, args.max_file_size):
                files_to_process.append(file_path)
        
        stats = ProcessingStats(
            total_files=len(files_to_process),
            start_time=time.time()
        )
        
        if not files_to_process:
            logger.info(" Nenhum arquivo válido encontrado para processar")
            return 0
        
        logger.info(f" {stats.total_files} arquivos válidos para processar")
        
        if args.dry_run:
            logger.info(" Modo dry-run - listando arquivos:")
            for i, file_path in enumerate(files_to_process[:10], 1):
                size_mb = file_path.stat().st_size / (1024**2)
                logger.info(f"  {i:3d}. {file_path.name} ({size_mb:.1f}MB)")
            if len(files_to_process) > 10:
                logger.info(f"  ... e mais {len(files_to_process) - 10} arquivos")
            return 0
        
        # Processar arquivos
        logger.info(f" Iniciando processamento com {args.workers} workers")
        
        # Parâmetros para process_file
        process_kwargs = {
            'ocr_mode': args.ocr,
            'max_pages': args.max_pages,
            'max_file_size': args.max_file_size,
            'timeout': args.timeout,
            'enable_enrichment': args.enrichment,
            'retry_count': args.retry
        }
        
        failed_files = []
        
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            # Submeter tarefas
            future_to_file = {
                executor.submit(
                    process_file, 
                    file_path, 
                    output_dir, 
                    **process_kwargs
                ): file_path
                for file_path in files_to_process
            }
            
            # Processar resultados
            for i, future in enumerate(as_completed(future_to_file), 1):
                file_path = future_to_file[future]
                progress_pct = (i / stats.total_files) * 100
                
                try:
                    output_path, file_stats = future.result()
                    stats.successful += 1
                    
                    logger.info(
                        f" [{i:3d}/{stats.total_files}] ({progress_pct:5.1f}%) "
                        f"{file_path.name} -> {output_path.name}"
                    )
                    
                except DocumentProcessingError as e:
                    stats.failed += 1
                    failed_files.append((file_path, str(e)))
                    
                    if args.continue_on_error:
                        logger.error(f" [{i:3d}/{stats.total_files}] {file_path.name}: {e}")
                    else:
                        logger.error(f" Parando devido a erro: {e}")
                        break
                        
                except Exception as e:
                    stats.failed += 1
                    failed_files.append((file_path, f"Erro inesperado: {e}"))
                    logger.error(f" [{i:3d}/{stats.total_files}] {file_path.name}: Erro inesperado: {e}")
        
        # Finalizar estatísticas
        stats.end_time = time.time()
        
        # Relatório final
        logger.info("=" * 60)
        logger.info(" PROCESSAMENTO CONCLUÍDO")
        logger.info("=" * 60)
        logger.info(f" Total de arquivos: {stats.total_files}")
        logger.info(f" Sucessos: {stats.successful}")
        logger.info(f" Falhas: {stats.failed}")
        logger.info(f" Taxa de sucesso: {stats.success_rate:.1f}%")
        logger.info(f" Tempo total: {stats.duration:.1f}s")
        
        if stats.total_files > 0:
            avg_time = stats.duration / stats.total_files
            logger.info(f" Tempo médio por arquivo: {avg_time:.1f}s")
        
        # Listar arquivos com falha
        if failed_files:
            logger.info("\n ARQUIVOS COM FALHA:")
            for file_path, error in failed_files[:10]:  # Mostrar apenas os primeiros 10
                logger.info(f"  • {file_path.name}: {error}")
            if len(failed_files) > 10:
                logger.info(f"  ... e mais {len(failed_files) - 10} arquivos com falha")
        
        # Determinar código de saída
        if stats.failed > 0 and stats.successful > 0:
            logger.warning(" Processamento parcialmente bem-sucedido")
            return 1
        elif stats.failed > 0:
            logger.error(" Processamento falhou")
            return 2
        else:
            logger.info(" Processamento 100% bem-sucedido!")
            return 0
            
    except ConfigurationError as e:
        logger.error(f" Erro de configuração: {e}")
        return 2
    except KeyboardInterrupt:
        logger.warning(" Processamento interrompido pelo usuário")
        return 1
    except Exception as e:
        logger.error(f" Erro inesperado: {e}")
        if args.verbose:
            import traceback
            logger.debug(traceback.format_exc())
        return 2

if __name__ == "__main__":
    sys.exit(run())

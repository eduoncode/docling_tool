"""Interface gráfica para o Docling Tool usando Tkinter.

Esta GUI fornece uma interface amigável para o processamento em lote
de documentos, reutilizando as funções do módulo process.py.
"""

from __future__ import annotations

import logging
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional, List
import urllib.request

# Importar funções do módulo existente
from ..main import (
    build_converter, ensure_dir, process_file, setup_logging,
    check_docling_availability, ProcessingStats, DocumentProcessingError,
    ConfigurationError, validate_file, SUPPORTED_EXTENSIONS
)


class LogHandler(logging.Handler):
    """Handler customizado para redirecionar logs para a interface gráfica."""

    def __init__(self, text_widget: tk.Text):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record: logging.LogRecord) -> None:
        """Emite uma mensagem de log para o widget de texto."""
        try:
            msg = self.format(record)
            # Verificar se o widget ainda existe e se o loop principal está ativo
            if self.text_widget and self.text_widget.winfo_exists():
                # Usar after() para thread safety
                self.text_widget.after(0, self._append_log, msg)
            else:
                # Fallback para stdout se GUI não estiver disponível
                print(f"[GUI LOG] {msg}")
        except (tk.TclError, RuntimeError) as e:
            # Se houver erro com Tkinter, usar fallback
            print(f"[GUI LOG] {self.format(record)}")
        except Exception as e:
            # Evitar que erros no logging quebrem a aplicação
            print(f"[LOG ERROR] {e}: {self.format(record)}")

    def _append_log(self, msg: str) -> None:
        """Adiciona mensagem ao widget de texto (thread-safe)."""
        try:
            if self.text_widget and self.text_widget.winfo_exists():
                self.text_widget.config(state=tk.NORMAL)
                self.text_widget.insert(tk.END, f"{msg}\n")
                self.text_widget.see(tk.END)
                self.text_widget.config(state=tk.DISABLED)
        except (tk.TclError, RuntimeError):
            # Se widget não estiver mais disponível, falhar silenciosamente
            pass


class DoclingGUI:
    """Interface gráfica principal para o Docling Tool."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Docling Tool - Document Processing GUI")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Variáveis de controle
        self.input_dir = tk.StringVar(value="entry_files")
        self.output_dir = tk.StringVar(value="output_texts")
        self.ocr_mode = tk.StringVar(value="always")
        self.verbose_mode = tk.BooleanVar(value=False)
        self.enrichment_mode = tk.BooleanVar(value=False)
        self.table_mode = tk.StringVar(value="accurate")
        self.max_workers = tk.IntVar(value=4)
        self.processing = False
        self.stats = ProcessingStats()

        # Configurar interface
        self._create_widgets()
        self._setup_logging()
        
        # Verificar docling na inicialização
        self._check_docling_on_startup()

    def _create_widgets(self) -> None:
        """Cria todos os widgets da interface."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(5, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Título
        title_label = ttk.Label(
            main_frame,
            text="Docling Tool - Document to Markdown Converter",
            style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Seção de diretórios
        self._create_directory_section(main_frame)

        # Seção de configurações
        self._create_config_section(main_frame)

        # Botões de ação
        self._create_action_buttons(main_frame)

        # Área de log
        self._create_log_area(main_frame)

        # Barra de progresso
        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='indeterminate'
        )
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))

    def _create_directory_section(self, parent: ttk.Frame) -> None:
        """Cria a seção de seleção de diretórios."""
        # Input directory
        ttk.Label(parent, text="Input Directory:", style="Heading.TLabel").grid(row=1, column=0, sticky=tk.W, pady=5)
        input_frame = ttk.Frame(parent)
        input_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_dir)
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(
            input_frame,
            text="Browse",
            command=self._browse_input_dir
        ).grid(row=0, column=1)

        # Output directory
        ttk.Label(parent, text="Output Directory:", style="Heading.TLabel").grid(row=2, column=0, sticky=tk.W, pady=5)
        output_frame = ttk.Frame(parent)
        output_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        output_frame.grid_columnconfigure(0, weight=1)

        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_dir)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(
            output_frame,
            text="Browse",
            command=self._browse_output_dir
        ).grid(row=0, column=1)

    def _create_config_section(self, parent: ttk.Frame) -> None:
        """Cria a seção de configurações."""
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding="10")
        config_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        config_frame.grid_columnconfigure(1, weight=1)

        # OCR Mode
        ttk.Label(config_frame, text="OCR Mode:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ocr_combo = ttk.Combobox(
            config_frame,
            textvariable=self.ocr_mode,
            values=["always", "auto", "never"],
            state="readonly",
            width=10
        )
        ocr_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        # Table Mode
        ttk.Label(config_frame, text="Table Mode:").grid(row=0, column=2, sticky=tk.W, padx=(20, 10))
        table_combo = ttk.Combobox(
            config_frame,
            textvariable=self.table_mode,
            values=["fast", "accurate"],
            state="readonly",
            width=10
        )
        table_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        # Workers
        ttk.Label(config_frame, text="Workers:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        workers_spin = ttk.Spinbox(
            config_frame,
            from_=1,
            to=16,
            textvariable=self.max_workers,
            width=8
        )
        workers_spin.grid(row=1, column=1, sticky=tk.W, padx=(0, 20))

        # Verbose Mode
        ttk.Checkbutton(
            config_frame,
            text="Verbose Logging",
            variable=self.verbose_mode
        ).grid(row=1, column=2, sticky=tk.W, padx=(20, 0))

        # Enrichment Mode
        ttk.Checkbutton(
            config_frame,
            text="Enable Enrichment",
            variable=self.enrichment_mode
        ).grid(row=1, column=3, sticky=tk.W, padx=(20, 0))

    def _create_action_buttons(self, parent: ttk.Frame) -> None:
        """Cria os botões de ação."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)

        self.process_button = ttk.Button(
            button_frame,
            text="Start Processing",
            command=self._start_processing,
            style="Accent.TButton"
        )
        self.process_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self._stop_processing,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Clear Log",
            command=self._clear_log
        ).pack(side=tk.LEFT, padx=5)

    def _create_log_area(self, parent: ttk.Frame) -> None:
        """Cria a área de log."""
        log_frame = ttk.LabelFrame(parent, text="Processing Log", padding="5")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # Text widget com scrollbar
        self.log_text = tk.Text(
            log_frame,
            height=15,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#fefefe",
            fg="#2d2d2d",
            font=("Consolas", 9),
            selectbackground="#0078d4",
            selectforeground="#ffffff",
            insertbackground="#0078d4",
            relief="flat",
            borderwidth=1
        )
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

    def _setup_logging(self) -> None:
        """Configura o sistema de logging para a GUI."""
        # Criar handler customizado
        self.log_handler = LogHandler(self.log_text)
        self.log_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%H:%M:%S")
        )

        # Configurar logger root
        self.logger = logging.getLogger()
        self.logger.handlers.clear()  # Remove handlers existentes
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.INFO)

    def _browse_input_dir(self) -> None:
        """Abre dialog para seleção do diretório de entrada."""
        directory = filedialog.askdirectory(
            title="Select Input Directory",
            initialdir=self.input_dir.get()
        )
        if directory:
            self.input_dir.set(directory)

    def _browse_output_dir(self) -> None:
        """Abre dialog para seleção do diretório de saída."""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_dir.get()
        )
        if directory:
            self.output_dir.set(directory)

    def _check_docling_on_startup(self) -> None:
        """Verifica se o docling está disponível na inicialização."""
        try:
            check_docling_availability()
            self.logger.info(" Docling está disponível e pronto para uso")
        except ConfigurationError as e:
            self.logger.error(f" Problema com docling: {e}")
            messagebox.showerror(
                "Erro de Configuração", 
                f"Docling não está disponível:\n\n{e}\n\nPor favor, instale o docling:\npip install docling"
            )
    
    def _start_processing(self) -> None:
        """Inicia o processamento em uma thread separada."""
        if self.processing:
            return

        # Verificar docling antes de processar
        try:
            check_docling_availability()
        except ConfigurationError as e:
            messagebox.showerror("Erro", f"Docling não disponível: {e}")
            return

        # Validar diretórios
        input_path = Path(self.input_dir.get())
        output_path = Path(self.output_dir.get())

        if not input_path.exists():
            messagebox.showerror("Error", f"Input directory does not exist: {input_path}")
            return

        try:
            ensure_dir(output_path)
        except ConfigurationError as e:
            messagebox.showerror("Error", f"Cannot create output directory: {e}")
            return

        candidate_files = [
            p for p in input_path.rglob("*")
            if p.is_file() and not p.name.startswith('.') and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        
        if not candidate_files:
            messagebox.showinfo("Info", "No supported files found in input directory")
            return

        # Configurar UI para processamento
        self.processing = True
        self.process_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start(10)

        # Resetar estatísticas
        self.stats = ProcessingStats(
            total_files=len(candidate_files),
            start_time=time.time()
        )

        # Configurar logging
        level = logging.DEBUG if self.verbose_mode.get() else logging.INFO
        self.logger.setLevel(level)

        # Iniciar processamento em thread separada
        self.processing_thread = threading.Thread(
            target=self._process_documents,
            args=(input_path, output_path, candidate_files),
            daemon=True
        )
        self.processing_thread.start()

    def _process_documents(self, input_dir: Path, output_dir: Path, candidate_files: List[Path]) -> None:
        """Processa documentos em thread separada com melhor tratamento de erros."""
        try:
            self.logger.info(f" Iniciando processamento de {len(candidate_files)} arquivos")
            self.logger.info(f" Entrada: {input_dir.resolve()}")
            self.logger.info(f" Saída: {output_dir.resolve()}")

            # Validar arquivos
            files_to_process = []
            for file_path in candidate_files:
                if validate_file(file_path):
                    files_to_process.append(file_path)
                else:
                    self.stats.skipped += 1

            self.stats.total_files = len(files_to_process)
            self.logger.info(f" {self.stats.total_files} arquivos válidos para processar")

            if not files_to_process:
                self.logger.info(" Nenhum arquivo válido encontrado")
                return

            # Criar conversor uma vez para toda a sessão
            self.logger.info(" Criando conversor docling...")
            try:
                converter = build_converter(
                    ocr_mode=self.ocr_mode.get(),
                    enable_code_enrichment=self.enrichment_mode.get(),
                    enable_formula_enrichment=self.enrichment_mode.get(),
                    enable_picture_classification=self.enrichment_mode.get(),
                    table_mode=self.table_mode.get()
                )
                self.logger.info(" Conversor criado com sucesso")
            except Exception as e:
                self.logger.error(f" Erro ao criar conversor: {e}")
                return

            # Processar arquivos sequencialmente para evitar problemas com GUI
            failed_files = []
            
            for i, file_path in enumerate(files_to_process, 1):
                if not self.processing:  # Verificar se foi cancelado
                    self.logger.info(" Processamento cancelado pelo usuário")
                    break

                progress_pct = (i / self.stats.total_files) * 100
                self.logger.info(f" [{i:3d}/{self.stats.total_files}] ({progress_pct:5.1f}%) Processando: {file_path.name}")

                try:
                    # Processar arquivo individual
                    output_path = self._process_single_file(
                        converter, 
                        file_path, 
                        output_dir
                    )
                    
                    if output_path:
                        self.stats.successful += 1
                        output_size = output_path.stat().st_size
                        self.logger.info(
                            f" [{i:3d}/{self.stats.total_files}] Sucesso: {file_path.name} -> {output_path.name} "
                            f"({output_size / 1024:.1f}KB)"
                        )
                    else:
                        self.stats.failed += 1
                        failed_files.append((file_path, "Falha no processamento"))
                        self.logger.error(f" [{i:3d}/{self.stats.total_files}] Falha: {file_path.name}")
                        
                except Exception as e:
                    self.stats.failed += 1
                    failed_files.append((file_path, str(e)))
                    self.logger.error(f" [{i:3d}/{self.stats.total_files}] Erro: {file_path.name}: {e}")

            # Relatório final
            self.stats.end_time = time.time()
            self.logger.info("=" * 50)
            self.logger.info(" PROCESSAMENTO CONCLUÍDO")
            self.logger.info("=" * 50)
            self.logger.info(f" Total: {self.stats.total_files}")
            self.logger.info(f" Sucessos: {self.stats.successful}")
            self.logger.info(f" Falhas: {self.stats.failed}")
            self.logger.info(f" Ignorados: {self.stats.skipped}")
            self.logger.info(f" Taxa de sucesso: {self.stats.success_rate:.1f}%")
            self.logger.info(f" Tempo total: {self.stats.duration:.1f}s")

            if failed_files:
                self.logger.info("\n ARQUIVOS COM FALHA:")
                for file_path, error in failed_files[:5]:  # Mostrar apenas os primeiros 5
                    self.logger.info(f"  • {file_path.name}: {error}")
                if len(failed_files) > 5:
                    self.logger.info(f"  ... e mais {len(failed_files) - 5} arquivos")

            # Mostrar resultado final na thread principal
            self.root.after(0, lambda: self._show_final_result(failed_files))

        except Exception as e:
            self.logger.error(f" Erro crítico no processamento: {e}")
            # Usar after para chamar messagebox na thread principal
            self.root.after(0, lambda: messagebox.showerror("Erro Crítico", f"Erro crítico durante processamento:\n\n{e}"))
        finally:
            self.root.after(0, self._processing_finished)

    def _process_single_file(self, converter, file_path: Path, output_dir: Path) -> Optional[Path]:
        """
        Processa um único arquivo usando o conversor fornecido.
        
        Returns:
            Path do arquivo de saída se bem-sucedido, None caso contrário
        """
        try:
            # Verificar se o arquivo ainda existe
            if not file_path.exists():
                self.logger.warning(f" Arquivo não encontrado: {file_path}")
                return None

            # Converter documento
            doc_result = converter.convert(file_path)
            doc = doc_result.document
            
            # Exportar para markdown
            text_markdown = doc.export_to_markdown()
            
            if not text_markdown.strip():
                self.logger.warning(f" Documento vazio após conversão: {file_path.name}")
                return None
            
            # Salvar arquivo
            output_filename = f"{file_path.stem}.md"
            output_path = output_dir / output_filename
            
            # Escrever arquivo com encoding UTF-8
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_markdown)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f" Erro ao processar {file_path.name}: {e}")
            return None

    def _show_final_result(self, failed_files: List) -> None:
        """Mostra o resultado final do processamento."""
        try:
            if self.stats.failed == 0:
                messagebox.showinfo(
                    "Sucesso", 
                    f"Processamento concluído com sucesso!\n\n"
                    f"Arquivos processados: {self.stats.successful}\n"
                    f"Tempo total: {self.stats.duration:.1f}s"
                )
            elif self.stats.successful > 0:
                messagebox.showwarning(
                    "Sucesso Parcial", 
                    f"Processamento parcialmente concluído:\n\n"
                    f"Sucessos: {self.stats.successful}\n"
                    f"Falhas: {self.stats.failed}\n"
                    f"Taxa de sucesso: {self.stats.success_rate:.1f}%"
                )
            else:
                messagebox.showerror(
                    "Falha", 
                    f"Processamento falhou:\n\n"
                    f"Todos os {self.stats.failed} arquivos falharam"
                )
        except Exception as e:
            self.logger.error(f"Erro ao mostrar resultado final: {e}")

    def _stop_processing(self) -> None:
        """Para o processamento."""
        self.processing = False
        self.logger.info("Processing stopped by user")

    def _processing_finished(self) -> None:
        """Chamado quando o processamento termina."""
        self.processing = False
        self.process_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()

    def _clear_log(self) -> None:
        """Limpa a área de log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)


def setup_azure_theme(root: tk.Tk) -> bool:
    """
    Configura o tema Azure moderno para a interface.
    
    Returns:
        bool: True se o tema foi aplicado com sucesso, False caso contrário
    """
    try:
        # Tentar baixar o tema Azure se não existir
        azure_tcl_path = Path("azure.tcl")
        
        if not azure_tcl_path.exists():
            print("Baixando tema Azure...")
            azure_url = "https://raw.githubusercontent.com/rdbende/Azure-ttk-theme/main/azure.tcl"
            try:
                urllib.request.urlretrieve(azure_url, azure_tcl_path)
                print("Tema Azure baixado com sucesso!")
            except Exception as e:
                print(f"Erro ao baixar tema Azure: {e}")
                return False
        
        # Aplicar tema Azure
        root.tk.call("source", str(azure_tcl_path))
        root.tk.call("set_theme", "light")
        
        # Configurar cores personalizadas
        style = ttk.Style()
        
        # Cores do tema Azure (modo claro)
        colors = {
            'primary': '#0078d4',
            'primary_hover': '#106ebe',
            'secondary': '#f3f2f1',
            'success': '#107c10',
            'warning': '#ffb900',
            'error': '#d13438',
            'background': '#ffffff',
            'surface': '#faf9f8',
            'text': '#323130',
            'text_secondary': '#605e5c'
        }
        
        # Configurar estilos personalizados
        style.configure("Title.TLabel", 
                       font=("Segoe UI", 16, "bold"),
                       foreground=colors['primary'])
        
        style.configure("Heading.TLabel",
                       font=("Segoe UI", 10, "bold"),
                       foreground=colors['text'])
        
        style.configure("Accent.TButton",
                       font=("Segoe UI", 9, "bold"))
        
        style.configure("Success.TLabel",
                       foreground=colors['success'])
        
        style.configure("Warning.TLabel",
                       foreground=colors['warning'])
        
        style.configure("Error.TLabel",
                       foreground=colors['error'])
        
        # Configurar janela principal
        root.configure(bg=colors['background'])
        
        print("Tema Azure aplicado com sucesso!")
        return True
        
    except Exception as e:
        print(f"Erro ao configurar tema Azure: {e}")
        return False


def apply_fallback_theme(root: tk.Tk) -> None:
    """
    Aplica um tema moderno alternativo caso o Azure não esteja disponível.
    """
    try:
        style = ttk.Style()
        
        # Usar tema padrão mais moderno disponível
        available_themes = style.theme_names()
        
        # Preferir temas modernos
        preferred_themes = ['vista', 'winnative', 'clam', 'alt', 'default']
        
        for theme in preferred_themes:
            if theme in available_themes:
                style.theme_use(theme)
                break
        
        # Cores modernas personalizadas
        colors = {
            'primary': '#0066cc',
            'background': '#f8f9fa',
            'surface': '#ffffff',
            'text': '#212529',
            'border': '#dee2e6'
        }
        
        # Configurar estilos
        style.configure("Title.TLabel", 
                       font=("Arial", 16, "bold"),
                       foreground=colors['primary'])
        
        style.configure("Heading.TLabel",
                       font=("Arial", 10, "bold"),
                       foreground=colors['text'])
        
        style.configure("Accent.TButton",
                       font=("Arial", 9, "bold"))
        
        # Configurar janela
        root.configure(bg=colors['background'])
        
        print("Tema alternativo aplicado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao aplicar tema alternativo: {e}")


def main() -> None:
    """Função principal para executar a GUI."""
    root = tk.Tk()
    
    # Configurar ícone da janela (se disponível)
    try:
        # Tentar definir um ícone padrão
        root.iconname("Docling Tool")
    except Exception:
        pass
    
    # Aplicar tema Azure moderno
    print("Configurando tema da interface...")
    theme_applied = setup_azure_theme(root)
    
    if not theme_applied:
        print("Aplicando tema alternativo...")
        apply_fallback_theme(root)
    
    # Criar e executar aplicação
    app = DoclingGUI(root)
    
    # Configurar tamanho mínimo da janela
    root.minsize(600, 500)
    
    # Centralizar janela
    root.update_idletasks()
    width = max(800, root.winfo_reqwidth())
    height = max(600, root.winfo_reqheight())
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    print("GUI inicializada com sucesso!")
    root.mainloop()


if __name__ == "__main__":
    main()

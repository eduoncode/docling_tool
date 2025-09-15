"""Interface gráfica para o Docling Tool usando Tkinter.

Esta GUI fornece uma interface amigável para o processamento em lote
de documentos, reutilizando as funções do módulo process.py.
"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

# Importar funções do módulo existente
from ..main import build_converter, ensure_dir, process_file, setup_logging


class LogHandler(logging.Handler):
    """Handler customizado para redirecionar logs para a interface gráfica."""

    def __init__(self, text_widget: tk.Text):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record: logging.LogRecord) -> None:
        """Emite uma mensagem de log para o widget de texto."""
        msg = self.format(record)
        # Usar after() para thread safety
        self.text_widget.after(0, self._append_log, msg)

    def _append_log(self, msg: str) -> None:
        """Adiciona mensagem ao widget de texto (thread-safe)."""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, f"{msg}\n")
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)


class DoclingGUI:
    """Interface gráfica principal para o Docling Tool."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Docling Tool - Document Processing GUI")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Variáveis de controle
        self.input_dir = tk.StringVar(value="entry_files")
        self.output_dir = tk.StringVar(value="textos_saida")
        self.ocr_mode = tk.StringVar(value="always")
        self.verbose_mode = tk.BooleanVar(value=False)
        self.processing = False

        # Configurar interface
        self._create_widgets()
        self._setup_logging()

    def _create_widgets(self) -> None:
        """Cria todos os widgets da interface."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Título
        title_label = ttk.Label(
            main_frame,
            text="Docling Tool - Document to Markdown Converter",
            font=("Arial", 16, "bold")
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
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))

    def _create_directory_section(self, parent: ttk.Frame) -> None:
        """Cria a seção de seleção de diretórios."""
        # Input directory
        ttk.Label(parent, text="Input Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
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
        ttk.Label(parent, text="Output Directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
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

        # Verbose Mode
        ttk.Checkbutton(
            config_frame,
            text="Verbose Logging",
            variable=self.verbose_mode
        ).grid(row=0, column=2, sticky=tk.W)

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
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # Text widget com scrollbar
        self.log_text = tk.Text(
            log_frame,
            height=15,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#f8f9fa",
            font=("Consolas", 9)
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

    def _start_processing(self) -> None:
        """Inicia o processamento em uma thread separada."""
        if self.processing:
            return

        # Validar diretórios
        input_path = Path(self.input_dir.get())
        output_path = Path(self.output_dir.get())

        if not input_path.exists():
            messagebox.showerror("Error", f"Input directory does not exist: {input_path}")
            return

        # Configurar UI para processamento
        self.processing = True
        self.process_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start(10)

        # Configurar logging
        level = logging.DEBUG if self.verbose_mode.get() else logging.INFO
        self.logger.setLevel(level)

        # Iniciar processamento em thread separada
        self.processing_thread = threading.Thread(
            target=self._process_documents,
            args=(input_path, output_path),
            daemon=True
        )
        self.processing_thread.start()

    def _process_documents(self, input_dir: Path, output_dir: Path) -> None:
        """Processa documentos em thread separada."""
        try:
            self.logger.info(f"Starting document processing...")
            self.logger.info(f"Input directory: {input_dir.resolve()}")
            self.logger.info(f"Output directory: {output_dir.resolve()}")

            # Criar diretório de saída
            ensure_dir(output_dir)

            # Buscar arquivos para processar
            files_to_process = [
                p for p in input_dir.iterdir()
                if p.is_file() and not p.name.startswith('.')
            ]

            if not files_to_process:
                self.logger.info("No files found in input directory")
                self.root.after(0, self._processing_finished)
                return

            # Construir conversor
            self.logger.info(f"Building converter with OCR mode: {self.ocr_mode.get()}")
            converter = build_converter(ocr_mode=self.ocr_mode.get())

            # Processar arquivos
            processed_count = 0
            for file_path in sorted(files_to_process):
                if not self.processing:  # Verificar se foi cancelado
                    break

                try:
                    self.logger.info(f"Processing: {file_path.name}")
                    output_file = process_file(converter, file_path, output_dir)
                    processed_count += 1
                except Exception as e:
                    self.logger.error(f"Error processing {file_path.name}: {e}")

            self.logger.info(f"Processing completed! {processed_count} files processed.")

        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
        finally:
            self.root.after(0, self._processing_finished)

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


def main() -> None:
    """Função principal para executar a GUI."""
    root = tk.Tk()
    
    # Configurar tema moderno se disponível
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "light")
    except tk.TclError:
        pass  # Tema não disponível, usar padrão

    # Criar e executar aplicação
    app = DoclingGUI(root)
    
    # Centralizar janela
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()

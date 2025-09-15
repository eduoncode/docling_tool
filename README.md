# Docling Tool

## Tool for batch document processing using docling

A robust and scalable solution for converting documents (PDF, DOCX, XLSX, TXT, HTML, and more) to Markdown using the `docling` library. The project follows Python development best practices with modular architecture, comprehensive testing, modern GUI interface with Azure theming, and extensive CLI options.

## Features

- **Batch processing** of multiple document formats (PDF, DOCX, XLSX, TXT, HTML, Images)
- **Modern GUI interface** with Azure theme and professional styling
- **Extensive CLI options** with advanced configuration parameters
- **Configurable OCR support** (always, auto, never)
- **Table processing modes** (fast, accurate) with TableFormer integration
- **Advanced enrichment features** (code, formulas, image classification)
- **Parallel processing** with configurable worker threads
- **Structured logging** with configurable levels and real-time GUI display

## Installation

### Prerequisites

- **Python 3.8+** (recommended 3.11+)
- **mise** (optional, for version management)

### Dependencies

```bash
# Install from requirements.txt 
pip install -r requirements.txt

# Or install core dependencies manually
pip install docling pytest pytest-cov psutil
```

### Complete Dependency List

The project includes comprehensive dependencies for full functionality:

- **docling** (2.52.0) - Main document processing library
- **docling-core** (2.48.1) - Core docling functionality
- **docling-ibm-models** (3.9.1) - IBM model integration
- **docling-parse** (4.4.0) - Document parsing capabilities
- **easyocr** (1.7.2) - OCR capabilities
- **pytorch** and related ML libraries - For AI model processing
- **psutil** - System resource monitoring
- **accelerate** - ML model acceleration
- **huggingface-hub** - Model repository access
- **beautifulsoup4** - HTML parsing support
- **pytest** and **pytest-cov** - Testing framework (development)

### Environment Setup

```bash
# Clone the repository
git clone <your-repository>
cd docling_tool

# Configure Python version (if using mise)
mise install

# Install all dependencies
pip install -r requirements.txt

# Or install core dependencies only
pip install docling pytest pytest-cov psutil
```

## Usage

### GUI Interface (Recommended)

```bash
# Launch the graphical interface
python -m src.gui.gui

# Or alternatively
cd src && python gui/gui.py
```

The GUI provides:

- **Advanced configuration options**: OCR mode, table processing mode, enrichment features
- **Parallel processing controls** with configurable worker threads
- **Real-time processing log** with professional formatting
- **Progress indication** with detailed status updates
- **Start/Stop processing controls** with thread-safe operations
- **Error handling dialogs** with detailed feedback
- **Processing statistics** and completion summaries

### Command Line Interface

#### Basic Command

```bash
# Basic processing
python -m src.main --input input_documents --output output_texts

# Using default directories (entry_files -> output_texts)
python -m src.main
```

### Advanced Options

```bash
# Verbose mode with enrichment features
python -m src.main --input docs/ --output markdown/ --verbose --enrichment

# Configure OCR and table processing
python -m src.main --input docs/ --output markdown/ --ocr auto --table-mode fast

# Parallel processing with limits
python -m src.main --input docs/ --output markdown/ --workers 8 --max-pages 50 --max-file-size 52428800

# Advanced processing with retry and timeout
python -m src.main --input docs/ --output markdown/ --retry 3 --timeout 300 --continue-on-error

# Download required models
python -m src.main --download-models

# Complete help with all options
python -m src.main --help
```

### CLI Parameters

| Parameter | Short Form | Default | Description |
|-----------|------------|---------|-------------|
| `--input` | `-i` | `entry_files` | Input directory with documents |
| `--output` | `-o` | `output_texts` | Output directory for Markdown files |
| `--ocr` | - | `always` | OCR mode: `always`, `auto`, `never` |
| `--workers` | `-w` | `4` | Number of parallel worker processes |
| `--timeout` | - | `300` | Timeout per file in seconds |
| `--verbose` | `-v` | `false` | Enable detailed DEBUG logging |
| `--enrichment` | - | `false` | Enable code, formula, and image enrichment |
| `--table-mode` | - | `accurate` | Table processing mode: `fast`, `accurate` |
| `--max-file-size` | - | `50MB` | Maximum file size in bytes |
| `--max-pages` | - | `100` | Maximum pages per document |
| `--retry` | - | `2` | Number of retry attempts on failure |
| `--continue-on-error` | - | `false` | Continue processing despite errors |
| `--disable-tables` | - | `false` | Disable table structure recognition |
| `--artifacts-path` | - | - | Path to local model artifacts |
| `--remote-services` | - | `false` | Allow remote service usage |
| `--download-models` | - | `false` | Download required models and exit |

## Architecture

### Project Structure

```text
docling_tool/
├── src/                    # Source code package
│   ├── __init__.py         # Package initialization
│   ├── main.py             # Main CLI module with processing logic
│   └── gui/                # GUI package
│       ├── __init__.py     # GUI package initialization
│       └── gui.py          # Tkinter GUI interface
├── tests/                  # Test suite
│   ├── conftest.py         # Shared configurations and fixtures
│   ├── test_process.py     # CLI module tests (9 cases)
│   └── test_gui.py         # GUI module tests (15 cases)
├── docs/                   # Documentation (future use)
├── create_sample_files.py  # Utility to create test files
├── pytest.ini             # Pytest configuration
├── requirements.txt        # Project dependencies
├── mise.toml              # Python version configuration
└── README.md              # This documentation
```

### Main Functions

- **`run(argv)`** - Main entry point with comprehensive argument parsing
- **`build_converter(ocr_mode, enrichment_options, table_mode)`** - DocumentConverter construction with advanced configuration
- **`process_file(converter, input_path, output_dir)`** - Individual file processing with error handling
- **`process_files_parallel(converter, files, output_dir, max_workers)`** - Parallel batch processing
- **`setup_logging(verbose)`** - Logging system configuration with professional formatting
- **`ensure_dir(path)`** - Utility for safe directory creation
- **`validate_file(path, max_size, max_pages)`** - File validation with size and page limits
- **`check_system_resources()`** - System resource monitoring and validation
- **`download_models_if_needed(force)`** - Automatic model download and management

### GUI Functions

- **`setup_azure_theme(root)`** - Modern Azure theme configuration with automatic download
- **`apply_fallback_theme(root)`** - Professional fallback theme for compatibility
- **`DoclingGUI`** - Main GUI class with threading and advanced error handling
- **`LogHandler`** - Custom logging handler for real-time GUI log display

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Tests with coverage
pytest tests/ --cov=process --cov-report=term-missing

# Specific test
pytest tests/test_process.py::test_process_file_writes_markdown -v

# Quick mode
pytest tests/ -q
```

### Test Coverage

- **24 tests** covering all critical scenarios (CLI + GUI)
- **94% coverage** of main code
- **Complete mocking** to avoid external dependencies
- **Error tests** for robustness
- **GUI component testing** with Tkinter mocks

### Tested Scenarios

**CLI Module (9 tests):**

1. Processing with no input files
2. Basic file processing
3. Multiple file extensions (PDF, DOCX, TXT)
4. Main function with valid files
5. Verbose mode and logging
6. Converter build failure
7. Processing errors
8. Directory utilities
9. Logging configuration

**GUI Module (15 tests):**

1. GUI initialization and configuration
2. Directory variable management
3. OCR mode options
4. Directory browsing functionality
5. Log clearing functionality
6. Processing state management
7. Error handling for invalid directories
8. Log handler functionality
9. Integration testing with mocked dependencies

## Supported Formats

| Format | Extension | OCR Support | Enrichment | Status |
|--------|-----------|-------------|------------|--------|
| PDF | `.pdf` | Yes | Full | Tested |
| Word | `.docx` | Yes | Full | Tested |
| Excel | `.xlsx` | Yes | Tables | Tested |
| PowerPoint | `.pptx` | Yes | Full | Tested |
| Text | `.txt` | N/A | Code | Tested |
| HTML | `.html` | N/A | Full | Tested |
| Markdown | `.md` | N/A | Code | Tested |
| Images | `.png`, `.jpg`, `.jpeg` | Yes | Classification | Tested |
| RTF | `.rtf` | Yes | Full | Tested |

## Development

### Development Setup

```bash
# Install all dependencies including development tools
pip install -r requirements.txt

# Run tests during development
pytest tests/ --cov=src --cov-report=html

# Check code quality
python -m py_compile src/main.py src/gui/gui.py

# Test GUI functionality
python -c "from src.gui import main; print('GUI ready')"

# Performance testing with larger files
python -m src.main --input large_docs/ --workers 8 --timeout 600 --verbose
```

### Logging Structure

```python
# Log levels used
DEBUG   # Detailed information (--verbose)
INFO    # Normal processing progress  
WARNING # Non-critical issues
ERROR   # Errors during processing
```

### GUI Theme System

The application includes an advanced theming system:

- **Azure Theme**: Modern professional theme downloaded automatically
- **Fallback Themes**: Compatible themes for older systems
- **Professional Styling**: Clean interface without decorative elements
- **Responsive Design**: Proper scaling and layout management

### Adding New Tests

```python
# Example new test in tests/test_process.py
def test_new_functionality(tmp_path, monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    # ... implement test
```

## Troubleshooting

### Common Issues

**Error: `ModuleNotFoundError: No module named 'docling'`**

```bash
# Install from requirements file
pip install -r requirements.txt

# Or install docling directly
pip install docling
```

### **Error: Theme download failures**

```bash
# The application will automatically fall back to compatible themes
# No action required - GUI will still function properly
```

### **Error: Out of memory during processing**

```bash
# Reduce parallel workers and add limits
python -m src.main --workers 2 --max-file-size 26214400 --max-pages 25
```

### **Error: Processing timeout**

```bash
# Increase timeout for large files
python -m src.main --timeout 600 --retry 3
```

### **Error: Directory not found**

```bash
# Check if directories exist
ls -la entry_files/
mkdir -p entry_files output_texts
```

### **Test failures**

```bash
# Reinstall test dependencies
pip install -r requirements.txt --upgrade
```

### Debug Logs

```bash
# Enable detailed logging
python -m src.main --verbose --input docs/ --output markdown/
```

## System Requirements

- **Python**: 3.8+ (developed and tested with 3.11)
- **Memory**: Minimum 2GB (recommended 8GB+ for large documents and parallel processing)
- **Disk**: Space for input + output documents + model cache (~2GB)
- **CPU**: Multi-core recommended for parallel processing
- **GPU**: Optional, automatically detected for AI model acceleration
- **Network**: Required for initial model download and Azure theme
- **OS**: Linux, macOS, Windows

## License

This project is open source. See the LICENSE file for more details.

---

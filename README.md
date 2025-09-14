# Docling Tool

## Professional tool for batch document processing using docling

A robust and scalable solution for converting documents (PDF, DOCX, TXT) to Markdown using the `docling` library. The project follows Python development best practices with modular architecture, comprehensive testing, and intuitive command-line interface.

## Features

- **Batch processing** of multiple document formats
- **Configurable OCR support** (always, auto, never)
- **Structured logging** with configurable levels
- **High test coverage** with proper mocking
- **Intuitive CLI interface** with argparse
- **Robust error handling** and validations
- **Modular architecture** with reusable functions

## Installation

### Prerequisites

- **Python 3.8+** (recommended 3.11+)
- **mise** (optional, for version management)

### Dependencies

```bash
# Install docling (main library)
pip install docling

# For development and testing
pip install pytest pytest-cov
```

### Environment Setup

```bash
# Clone the repository
git clone <your-repository>
cd docling_tool

# Configure Python version (if using mise)
mise install

# Install dependencies
pip install docling pytest pytest-cov
```

## Usage

### Basic Command

```bash
# Basic processing
python process.py --input input_documents --output output_texts

# Using default directories (entry_files -> textos_saida)
python process.py
```

### Advanced Options

```bash
# Verbose mode (DEBUG logging)
python process.py --input docs/ --output markdown/ --verbose

# Configure OCR mode
python process.py --input docs/ --output markdown/ --ocr auto

# Complete help
python process.py --help
```

### CLI Parameters

| Parameter | Short Form | Default | Description |
|-----------|------------|---------|-------------|
| `--input` | `-i` | `entry_files` | Input directory with documents |
| `--output` | `-o` | `textos_saida` | Output directory for Markdown files |
| `--ocr` | - | `always` | OCR mode: `always`, `auto`, `never` |
| `--verbose` | `-v` | `false` | Enable detailed DEBUG logging |

## Architecture

### Project Structure

```text
docling_tool/
├── process.py          # Main module with processing logic
├── tests/              # Test suite
│   ├── conftest.py     # Shared configurations and fixtures
│   └── test_process.py # Comprehensive tests (9 cases)
├── pytest.ini         # Pytest configuration
├── mise.toml          # Python version configuration
└── README.md          # This documentation
```

### Main Functions

- **`run(argv)`** - Main entry point with argument parsing
- **`build_converter(ocr_mode)`** - DocumentConverter construction and configuration
- **`process_file(converter, input_path, output_dir)`** - Individual file processing
- **`setup_logging(verbose)`** - Logging system configuration
- **`ensure_dir(path)`** - Utility for safe directory creation

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

- **9 tests** covering all critical scenarios
- **94% coverage** of main code
- **Complete mocking** to avoid external dependencies
- **Error tests** for robustness

### Tested Scenarios

1. Processing with no input files
2. Basic file processing
3. Multiple file extensions (PDF, DOCX, TXT)
4. Main function with valid files
5. Verbose mode and logging
6. Converter build failure
7. Processing errors
8. Directory utilities
9. Logging configuration

## Supported Formats

| Format | Extension | OCR Support | Status |
|--------|-----------|-------------|--------|
| PDF | `.pdf` | Yes | Tested |
| Word | `.docx` | Yes | Tested |
| Text | `.txt` | N/A | Tested |

## Development

### Development Setup

```bash
# Install development dependencies
pip install pytest pytest-cov

# Run tests during development
pytest tests/ --cov=process --cov-report=html

# Check code quality
python -m py_compile process.py
```

### Logging Structure

```python
# Log levels used
DEBUG   # Detailed information (--verbose)
INFO    # Normal processing progress  
ERROR   # Errors during processing
```

### Adding New Tests

```python
# Example new test in tests/test_process.py
def test_new_functionality(tmp_path, monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    # ... implement test
```

## Troubleshooting

### Common Issues

Error: `ModuleNotFoundError: No module named 'docling'`

```bash
pip install docling
```

Error: Directory not found

```bash
# Check if directories exist
ls -la entry_files/
mkdir -p entry_files textos_saida
```

Test failures

```bash
# Reinstall test dependencies
pip install pytest pytest-cov --upgrade
```

### Debug Logs

```bash
# Enable detailed logging
python process.py --verbose --input docs/ --output markdown/
```

## System Requirements

- **Python**: 3.8+ (developed and tested with 3.11)
- **Memory**: Minimum 512MB (recommended 2GB+ for large documents)
- **Disk**: Space for input + output documents
- **OS**: Linux, macOS, Windows

## License

This project is open source. See the LICENSE file for more details.

---

import pytest
import sys
from pathlib import Path


@pytest.fixture(autouse=True)
def setup_path():
    """Adiciona automaticamente o diretório raiz ao sys.path para todos os testes."""
    root_dir = Path(__file__).resolve().parents[1]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))


@pytest.fixture
def sample_files(tmp_path):
    """Cria arquivos de exemplo para testes."""
    inp_dir = tmp_path / "input"
    out_dir = tmp_path / "output"
    inp_dir.mkdir()
    out_dir.mkdir()
    
    # Criar arquivos de teste
    files = {
        "doc1.pdf": "PDF content",
        "doc2.docx": "DOCX content",
        "doc3.txt": "TXT content"
    }
    
    for filename, content in files.items():
        file_path = inp_dir / filename
        file_path.write_text(content, encoding="utf-8")
    
    return {
        "input_dir": inp_dir,
        "output_dir": out_dir,
        "files": list(files.keys())
    }


@pytest.fixture
def dummy_converter():
    """Retorna uma instância do DummyConverter para uso em testes."""
    from tests.test_process import DummyConverter
    return DummyConverter()

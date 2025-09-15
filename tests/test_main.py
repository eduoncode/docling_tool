import sys
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


def test_run_no_files(tmp_path, monkeypatch):
    """Se não houver ficheiros no input, run() deve retornar 0 e não falhar."""
    # Adicionar o caminho do package
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.main import run

    rc = run(["--input", str(tmp_path / "in"), "--output", str(tmp_path / "out")])
    assert rc == 0

    rc = run(["--input", str(tmp_path / "in"), "--output", str(tmp_path / "out")])
    assert rc == 0


class DummyDoc:
    def to_markdown(self):
        return "# dummy\n"


class DummyConverter:
    def __init__(self, *args, **kwargs):
        pass

    def convert(self, path):
        return DummyDoc()


@patch('src.main.build_converter')
def test_process_file_writes_markdown(mock_build_converter, tmp_path, monkeypatch):
    """Garante que um arquivo é processado e um .md é escrito."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    monkeypatch.chdir(tmp_path)

    # configurar o mock para retornar DummyConverter
    mock_build_converter.return_value = DummyConverter()

    # criar arquivo de entrada
    inp_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    inp_dir.mkdir()
    out_dir.mkdir()
    file_path = inp_dir / "doc1.pdf"
    file_path.write_text("binarydata", encoding="utf-8")

    # importar depois de configurar o mock
    from src.main import build_converter, process_file

    # executar
    converter = build_converter()
    out = process_file(converter, file_path, out_dir)

    # verificações
    assert out.exists()
    assert out.name == "doc1.md"
    assert out.read_text(encoding="utf-8").startswith("# dummy")
    
    # verificar se o mock foi chamado
    mock_build_converter.assert_called_once()


def test_process_file_with_different_extensions(tmp_path, monkeypatch):
    """Testa se diferentes extensões de arquivo são processadas corretamente."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    monkeypatch.chdir(tmp_path)

    inp_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    inp_dir.mkdir()
    out_dir.mkdir()
    
    # Testar diferentes extensões
    extensions = [".pdf", ".docx", ".txt"]
    
    with patch('src.main.build_converter') as mock_build_converter:
        mock_build_converter.return_value = DummyConverter()
        
        from src.main import build_converter, process_file
        
        converter = build_converter()
        
        for ext in extensions:
            file_path = inp_dir / f"test{ext}"
            file_path.write_text("test content", encoding="utf-8")
            
            out = process_file(converter, file_path, out_dir)
            
            assert out.exists()
            assert out.name == f"test.md"
            assert out.read_text(encoding="utf-8").startswith("# dummy")


@patch('src.main.build_converter')
def test_run_with_files(mock_build_converter, tmp_path, monkeypatch):
    """Testa a função run com arquivos presentes."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    
    # configurar mock
    mock_build_converter.return_value = DummyConverter()
    
    # criar estrutura de diretórios
    inp_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    inp_dir.mkdir()
    out_dir.mkdir()
    
    # criar arquivo de teste
    test_file = inp_dir / "test.pdf"
    test_file.write_text("test content", encoding="utf-8")
    
    from src.main import run
    
    # executar
    rc = run(["--input", str(inp_dir), "--output", str(out_dir)])
    
    # verificações
    assert rc == 0
    output_file = out_dir / "test.md"
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8").startswith("# dummy")


@patch('src.main.build_converter')
def test_run_verbose_mode(mock_build_converter, tmp_path, caplog):
    """Testa se o modo verbose funciona corretamente."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    
    # configurar mock
    mock_build_converter.return_value = DummyConverter()
    
    # criar estrutura de diretórios
    inp_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    inp_dir.mkdir()
    out_dir.mkdir()
    
    # criar arquivo de teste
    test_file = inp_dir / "test.pdf"
    test_file.write_text("test content", encoding="utf-8")
    
    from src.main import run
    
    # executar com verbose
    with caplog.at_level(logging.DEBUG):
        rc = run(["--input", str(inp_dir), "--output", str(out_dir), "--verbose"])
    
    # verificações
    assert rc == 0
    # Verificar se há mensagens de debug no log - ajustar para texto português
    assert any("Processando:" in record.message for record in caplog.records) or \
           any("Processing:" in record.message for record in caplog.records) or \
           "test.pdf" in caplog.text


@patch('src.main.build_converter')
def test_run_converter_build_failure(mock_build_converter, tmp_path):
    """Testa o comportamento quando build_converter falha."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    
    # configurar mock para falhar
    mock_build_converter.side_effect = Exception("Erro ao construir conversor")
    
    # criar estrutura de diretórios
    inp_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    inp_dir.mkdir()
    out_dir.mkdir()
    
    # criar arquivo de teste
    test_file = inp_dir / "test.pdf"
    test_file.write_text("test content", encoding="utf-8")
    
    from src.main import run
    
    # executar
    rc = run(["--input", str(inp_dir), "--output", str(out_dir)])
    
    # verificações - deve retornar código de erro 2
    assert rc == 2


@patch('src.main.build_converter')
def test_run_processing_error(mock_build_converter, tmp_path, caplog):
    """Testa o comportamento quando process_file falha."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    
    # configurar mock converter que falha ao processar
    class FailingConverter:
        def convert(self, path):
            raise Exception("Erro ao processar arquivo")
    
    mock_build_converter.return_value = FailingConverter()
    
    # criar estrutura de diretórios
    inp_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    inp_dir.mkdir()
    out_dir.mkdir()
    
    # criar arquivo de teste
    test_file = inp_dir / "test.pdf"
    test_file.write_text("test content", encoding="utf-8")
    
    from src.main import run
    
    # executar com captura de log
    with caplog.at_level(logging.INFO):
        rc = run(["--input", str(inp_dir), "--output", str(out_dir)])
    
    # verificações - deve retornar 0 mas não processar nenhum arquivo
    assert rc == 0
    assert "Nenhum arquivo processado" in caplog.text


def test_ensure_dir_function(tmp_path):
    """Testa a função ensure_dir."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.main import ensure_dir
    
    # Testar criação de diretório que não existe
    new_dir = tmp_path / "nova" / "pasta" / "profunda"
    ensure_dir(new_dir)
    assert new_dir.exists()
    assert new_dir.is_dir()
    
    # Testar com diretório que já existe
    ensure_dir(new_dir)  # Não deve falhar
    assert new_dir.exists()


def test_setup_logging_function():
    """Testa a função setup_logging."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.main import setup_logging
    
    # Testar se as funções executam sem erro
    try:
        setup_logging(verbose=True)
        setup_logging(verbose=False)
        # Se chegou até aqui, o teste passou
        assert True
    except Exception as e:
        pytest.fail(f"setup_logging falhou: {e}")

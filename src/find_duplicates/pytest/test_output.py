# Файл: pytest/test_output.py
import os
import pytest
from find_duplicates.modules.output import write_duplicates_to_csv, print_tree_view, save_tree_to_txt


def test_write_duplicates_to_csv_valid(tmp_path):
    """
    Запись корректного словаря с дубликатами в CSV.
    """
    output_file = tmp_path / "duplicates.csv"
    duplicates = {
        "hash123": [
            {"path": "/some/path/file1.txt", "size": 123},
            {"path": "/some/path/file2.txt", "size": 123}
        ],
        "hash456": [
            {"path": "/some/path/file3.txt", "size": 456}
        ]
    }
    result = write_duplicates_to_csv(duplicates, str(output_file))
    assert result is True
    assert output_file.exists()

    # Проверим, что CSV не пустой и содержит разделители
    content = output_file.read_text(encoding="utf-8")
    assert "," in content
    # Проверяем наличие заголовка "Группа", "Путь", "Размер"
    assert "Группа,Путь,Размер" in content


def test_write_duplicates_to_csv_empty(tmp_path):
    """
    Запись пустого словаря дубликатов (без групп).
    """
    output_file = tmp_path / "duplicates_empty.csv"
    duplicates = {}
    result = write_duplicates_to_csv(duplicates, str(output_file))
    assert result is True
    content = output_file.read_text(encoding="utf-8")
    # Может быть только заголовок
    assert "Группа,Путь,Размер" in content


def test_write_duplicates_to_csv_invalid_path(tmp_path):
    """
    Если указать несуществующий путь для записи, ожидаем, что функция вернёт False.
    """
    invalid_dir = tmp_path / "nonexistent"
    # не создаём папку intentionally
    output_file = invalid_dir / "output.csv"
    duplicates = {
        "hash000": [{"path": "dummy.txt", "size": 100}]
    }
    result = write_duplicates_to_csv(duplicates, str(output_file))
    assert result is False
    assert not output_file.exists()


def test_write_duplicates_to_csv_unicode(tmp_path):
    """
    Тестирование корректности записи unicode-символов (как в путях, так и в содержимом).
    """
    output_file = tmp_path / "unicode.csv"
    duplicates = {
        "hashUni": [
            {"path": "/tmp/файл.txt", "size": 50},
            {"path": "/tmp/другой_файл.txt", "size": 50},
        ]
    }
    result = write_duplicates_to_csv(duplicates, str(output_file))
    assert result is True
    content = output_file.read_text(encoding="utf-8")
    assert "файл.txt" in content


def test_write_duplicates_to_csv_many_groups(tmp_path):
    """
    Запись большого количества групп.
    """
    output_file = tmp_path / "many.csv"
    duplicates = {}
    for i in range(100):
        hsh = f"hash{i}"
        duplicates[hsh] = [
            {"path": f"/path/to/file{i}_1.txt", "size": 1234},
            {"path": f"/path/to/file{i}_2.txt", "size": 1234}
        ]
    result = write_duplicates_to_csv(duplicates, str(output_file))
    assert result is True
    lines = output_file.read_text(encoding="utf-8").splitlines()
    # должна быть минимум 1 (заголовок) + 2*100 строк
    assert len(lines) >= 201


def test_rewrite_csv(tmp_path):
    """
    Проверка перезаписи существующего файла.
    """
    output_file = tmp_path / "rewrite.csv"
    output_file.write_text("OLD CONTENT", encoding="utf-8")

    duplicates = {
        "hashXYZ": [
            {"path": "/path/fileA.txt", "size": 500},
            {"path": "/path/fileB.txt", "size": 500}
        ]
    }
    result = write_duplicates_to_csv(duplicates, str(output_file))
    assert result is True
    new_content = output_file.read_text(encoding="utf-8")
    assert "OLD CONTENT" not in new_content


def test_print_tree_view(capsys):
    """
    Проверка вывода tree-view в консоль через print_tree_view.
    """
    duplicates = {
        "hash123": [
            {"path": "/some/path1.txt", "size": 100},
            {"path": "/some/path2.txt", "size": 100},
        ]
    }
    print_tree_view(duplicates)
    captured = capsys.readouterr().out
    # Проверяем, что в output видны "Группа 1" и пути
    assert "Группа 1:" in captured
    assert "/some/path1.txt" in captured
    assert "/some/path2.txt" in captured


def test_save_tree_to_txt(tmp_path):
    """
    Сохранение tree-view в текстовый файл.
    """
    output_file = tmp_path / "tree_output.txt"
    duplicates = {
        "hashUni": [
            {"path": "/tmp/файл.txt", "size": 50},
            {"path": "/tmp/другой.txt", "size": 50}
        ]
    }
    save_tree_to_txt(duplicates, str(output_file))
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "Группа 1:" in content
    assert "файл.txt" in content


def test_save_tree_no_permission(tmp_path):
    """
    Ошибка записи при недоступной директории => должны возникнуть исключения
    или по крайней мере файл не создаться.
    """
    locked_dir = tmp_path / "locked"
    locked_dir.mkdir()
    os.chmod(str(locked_dir), 0o444)
    output_file = locked_dir / "results.txt"

    duplicates = {
        "hashX": [{"path": "/path/f.txt", "size": 100}]
    }
    with pytest.raises(Exception):
        # save_tree_to_txt выбрасывает OSError/IOError
        save_tree_to_txt(duplicates, str(output_file))

    os.chmod(str(locked_dir), 0o755)

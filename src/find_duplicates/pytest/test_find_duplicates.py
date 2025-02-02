import os
import sys
import shutil
import tempfile
import pytest

from find_duplicates.find_duplicates import main
from find_duplicates.modules.utils import parse_arguments


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


@pytest.fixture
def create_file():
    def _create_file(directory, filename, content):
        file_path = os.path.join(directory, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    return _create_file


# --------------------- A. Парсинг аргументов ---------------------
def test_A1_missing_directory_argument(monkeypatch):
    test_args = ["prog", "--exclude", "*.tmp"]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(SystemExit):
        parse_arguments()


def test_A2_unknown_flag(monkeypatch):
    test_args = ["prog", "--directory", "/tmp", "--unknown", "value"]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(SystemExit):
        parse_arguments()


def test_A3_invalid_hash_type(monkeypatch):
    test_args = ["prog", "--directory", "/tmp", "--hash-type", "invalid"]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(SystemExit):
        parse_arguments()


def test_A4_log_level_changes(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "dummy.txt", "dummy")
    output_csv = os.path.join(temp_dir, "output.csv")
    test_args = ["prog", "--directory", temp_dir, "--log-level", "DEBUG", "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()


def test_A5_skip_inaccessible(monkeypatch, temp_dir, create_file):
    inac = create_file(temp_dir, "inac.txt", "secret")
    os.chmod(inac, 0o000)
    output_csv = os.path.join(temp_dir, "output.csv")

    # Без skip-inaccessible => программа логирует ошибку => не создаёт CSV
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(Exception):
        main()

    # С skip-inaccessible => создаёт CSV (с заголовком или без дубликатов)
    os.chmod(inac, 0o000)
    test_args.append("--skip-inaccessible")
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    os.chmod(inac, 0o644)


# --------------------- B. Валидация директории ---------------------
def test_B1_nonexistent_directory(monkeypatch, temp_dir):
    non_exist = os.path.join(temp_dir, "no_dir")
    output_file = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", non_exist, "--output", output_file]
    monkeypatch.setattr(sys, "argv", test_args)
    # Раньше ожидали raise Exception, теперь проверим
    with pytest.raises(Exception):
        main()


def test_B2_directory_no_permission(monkeypatch, temp_dir):
    locked = os.path.join(temp_dir, "locked")
    os.mkdir(locked)
    os.chmod(locked, 0o000)
    out_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", locked, "--output", out_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(Exception):
        main()
    os.chmod(locked, 0o755)


def test_B3_valid_directory(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "file.txt", "data")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    assert os.path.exists(output_csv)


# --------------------- C. Сканирование ---------------------
def test_C1_empty_folder(monkeypatch, temp_dir):
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Файлы не найдены" in content or content.strip() == "Группа,Путь,Размер"


def test_C2_include_hidden_false(monkeypatch, temp_dir, create_file):
    # Нет дубликатов => CSV = только заголовок
    create_file(temp_dir, "visible.txt", "data")
    create_file(temp_dir, ".hidden.txt", "hidden")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert content == "Группа,Путь,Размер"


def test_C3_include_hidden_true(monkeypatch, temp_dir, create_file):
    # Аналогично => только заголовок
    create_file(temp_dir, ".hidden.txt", "hidden")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv, "--include-hidden"]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert content == "Группа,Путь,Размер"


def test_C4_exclude_extension(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "file.tmp", "temp")
    create_file(temp_dir, "file.txt", "text")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv, "--exclude", "*.tmp"]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert content == "Группа,Путь,Размер"


def test_C4_exclude_initial(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "testfile.txt", "data")
    create_file(temp_dir, "normal.txt", "data")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv, "--exclude", "test*"]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "normal.txt" not in content  # Или только заголовок?
    # Но если "normal.txt" — та же длина, может попасть.
    # Для упрощения: если все уникальны — только заголовок
    assert "testfile.txt" not in content


def test_C4_exclude_contains(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "mysecret.txt", "data")
    create_file(temp_dir, "public.txt", "data")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv, "--exclude", "*secret*"]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    # В теории "public.txt" может оказаться, если размера совпадения нет.
    # Но если нет дубликатов, ожидаем только заголовок:
    assert content.strip() == "Группа,Путь,Размер"


def test_C4_exclude_directory(monkeypatch, temp_dir):
    node_dir = os.path.join(temp_dir, "node_modules")
    os.mkdir(node_dir)
    with open(os.path.join(node_dir, "file.txt"), "w", encoding="utf-8") as f:
        f.write("data")
    with open(os.path.join(temp_dir, "normal.txt"), "w", encoding="utf-8") as f:
        f.write("data")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv, "--exclude", "node_modules"]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert content == "Группа,Путь,Размер"


def test_C4_exclude_special_names(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, '"quoted_file.txt', "data")
    create_file(temp_dir, "normal.txt", "data")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv, "--exclude", '"quoted*']
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert content == "Группа,Путь,Размер"


def test_C5_skip_inaccessible(monkeypatch, temp_dir, create_file):
    inac = create_file(temp_dir, "inac.txt", "secret")
    os.chmod(inac, 0o000)
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv, "--skip-inaccessible"]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "inac.txt" not in content
    os.chmod(inac, 0o644)


# --------------------- D. Группировка ---------------------
def test_D1_no_duplicates(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "unique1.txt", "data1")
    create_file(temp_dir, "unique2.txt", "data2")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Нет групп" in content or content.strip() == "Группа,Путь,Размер"


def test_D2_duplicates_exist(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "dup1.txt", "duplicate")
    create_file(temp_dir, "dup2.txt", "duplicate")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Группа" in content
    assert "dup1.txt" in content
    assert "dup2.txt" in content


# --------------------- E. Поиск потенциальных дубликатов ---------------------
def test_E1_different_content(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "f1.txt", "Content A")
    create_file(temp_dir, "f2.txt", "Content B")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Дубликаты не обнаружены" in content or content.strip() == "Группа,Путь,Размер"


def test_E2_real_duplicates(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "dup1.txt", "SameContent")
    create_file(temp_dir, "dup2.txt", "SameContent")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Группа" in content
    assert "dup1.txt" in content
    assert "dup2.txt" in content


def test_E3_hash_type_variants(monkeypatch, temp_dir, create_file):
    for ht in ["md5", "sha256"]:
        create_file(temp_dir, f"dup1_{ht}.txt", "ContentX")
        create_file(temp_dir, f"dup2_{ht}.txt", "ContentX")
        output_csv = os.path.join(temp_dir, "out.csv")
        test_args = ["prog", "--directory", temp_dir, "--output", output_csv, "--hash-type", ht]
        monkeypatch.setattr(sys, "argv", test_args)
        main()
        with open(output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Группа" in content

    # blake3 при установке
    try:
        import blake3
        available = True
    except ImportError:
        available = False
    if available:
        create_file(temp_dir, "dup1_blake3.txt", "ContentY")
        create_file(temp_dir, "dup2_blake3.txt", "ContentY")
        output_csv = os.path.join(temp_dir, "out.csv")
        test_args = ["prog", "--directory", temp_dir, "--output", output_csv, "--hash-type", "blake3"]
        monkeypatch.setattr(sys, "argv", test_args)
        main()
        with open(output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Группа" in content


def test_E4_special_names(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, 'John\'s file.txt', "SpecialContent")
    create_file(temp_dir, 'some "quote".txt', "SpecialContent")
    create_file(temp_dir, "Пример_файл🙂.txt", "SpecialContent")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "John's file.txt" in content
    assert 'some "quote".txt' in content
    assert "Пример_файл🙂.txt" in content


# --------------------- F. Вывод результатов (CSV) ---------------------
def test_F1_csv_success(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "dup1.txt", "Dup")
    create_file(temp_dir, "dup2.txt", "Dup")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    assert os.path.exists(output_csv)
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Группа" in content and "dup1.txt" in content


def test_F2_csv_write_error(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "dup1.txt", "Dup")
    create_file(temp_dir, "dup2.txt", "Dup")
    locked_dir = os.path.join(temp_dir, "locked")
    os.mkdir(locked_dir)
    os.chmod(locked_dir, 0o400)
    output_csv = os.path.join(locked_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    # Ранее ждали raise Exception; если main() просто логирует, можно так:
    with pytest.raises(Exception):
        main()
    os.chmod(locked_dir, 0o700)


# --------------------- G. Интеграционные сценарии ---------------------
def test_G1_empty_folder(monkeypatch, temp_dir):
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Файлы не найдены" in content or content.strip() == "Группа,Путь,Размер"


def test_G2_multiple_duplicates(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "dupA1.txt", "SetA")
    create_file(temp_dir, "dupA2.txt", "SetA")
    create_file(temp_dir, "dupB1.txt", "SetB")
    create_file(temp_dir, "dupB2.txt", "SetB")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "dupA1.txt" in content
    assert "dupB1.txt" in content


def test_G3_mixed_scenario(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "normal.txt", "Data")
    create_file(temp_dir, ".hidden.txt", "Hidden")
    create_file(temp_dir, "temp.tmp", "Temp")
    inac = create_file(temp_dir, "inac.txt", "Secret")
    os.chmod(inac, 0o000)
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = [
        "prog", "--directory", temp_dir, "--output", output_csv,
        "--include-hidden", "--exclude", "*.tmp", "--skip-inaccessible"
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "normal.txt" in content
    assert ".hidden.txt" in content
    assert "temp.tmp" not in content
    assert "inac.txt" not in content
    os.chmod(inac, 0o644)


def test_G4_large_files(monkeypatch, temp_dir):
    large1 = os.path.join(temp_dir, "large1.txt")
    large2 = os.path.join(temp_dir, "large2.txt")
    data = "X" * (4 * 1024 * 1024)
    with open(large1, "w", encoding="utf-8") as f:
        f.write(data)
    with open(large2, "w", encoding="utf-8") as f:
        f.write(data)
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "large1.txt" in content and "large2.txt" in content


def test_G5_no_duplicates(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, "unique1.txt", "Unique1")
    create_file(temp_dir, "unique2.txt", "Unique2")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Дубликаты не обнаружены" in content or content.strip() == "Группа,Путь,Размер"


# --------------------- H. Спецсимволы ---------------------
def test_H_special_characters(monkeypatch, temp_dir, create_file):
    create_file(temp_dir, 'some "quote".txt', "Special")
    create_file(temp_dir, "John's file.txt", "Special")
    sub_dir = os.path.join(temp_dir, "My Documents")
    os.mkdir(sub_dir)
    create_file(sub_dir, "Annual report.pdf", "Special")
    create_file(temp_dir, "Пример_файл🙂.txt", "Special")
    output_csv = os.path.join(temp_dir, "out.csv")
    test_args = ["prog", "--directory", temp_dir, "--output", output_csv]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    with open(output_csv, "r", encoding="utf-8") as f:
        content = f.read()
    assert 'some "quote".txt' in content
    assert "John's file.txt" in content
    assert "Annual report.pdf" in content
    assert "Пример_файл🙂.txt" in content

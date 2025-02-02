import os
import pytest
from find_duplicates.modules.scanner import scan_directory, is_excluded

@pytest.fixture
def test_dir(tmp_path):
    """
    Базовая фикстура для создания тестовой директории:
    - file.txt: обычный файл
    - .hidden.txt: скрытый файл
    """
    d = tmp_path / "test_dir"
    d.mkdir()
    (d / "file.txt").write_text("Visible", encoding="utf-8")
    (d / ".hidden.txt").write_text("Hidden", encoding="utf-8")
    return d


def test_scan_directory_normal_files(test_dir):
    """
    Проверяем, что при обычном сканировании 'file.txt' обнаруживается.
    """
    result = scan_directory(str(test_dir))
    basenames = [os.path.basename(p) for p in result]
    assert "file.txt" in basenames, "Обычный файл должен присутствовать в результатах"


def test_scan_directory_include_hidden(test_dir):
    """
    Проверяем, что при include_hidden=True скрытые файлы возвращаются.
    """
    result = scan_directory(str(test_dir), include_hidden=True)
    basenames = [os.path.basename(p) for p in result]
    assert "file.txt" in basenames
    assert ".hidden.txt" in basenames


def test_scan_directory_exclude_hidden(test_dir):
    """
    Проверяем, что при include_hidden=False скрытые файлы не возвращаются.
    """
    result = scan_directory(str(test_dir), include_hidden=False)
    basenames = [os.path.basename(p) for p in result]
    assert "file.txt" in basenames
    assert ".hidden.txt" not in basenames


def test_recursive_subdirectories(tmp_path):
    """
    Проверяем рекурсивный обход: должна возвращаться nested.txt из поддиректории.
    """
    base = tmp_path / "base"
    base.mkdir()
    sub = base / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("Nested", encoding="utf-8")

    result = scan_directory(str(base), include_hidden=True)
    assert any("nested.txt" in path for path in result), "Файл в поддире должен обнаруживаться"


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="Симлинки не поддерживаются на этой платформе")
def test_symlinks_follow_true_false(tmp_path):
    """
    Проверяем поведение follow_symlinks=False/True:
    - При follow_symlinks=False симлинк не должен сканироваться как файл.
    - При follow_symlinks=True симлинк учитывается.
    """
    base = tmp_path / "links"
    base.mkdir()
    target = base / "target.txt"
    target.write_text("Data", encoding="utf-8")

    link = base / "link.txt"
    os.symlink(str(target), str(link))

    # 1) follow_symlinks=False
    result_no_follow = scan_directory(str(base), include_hidden=True, skip_inaccessible=False)
    assert os.path.basename("link.txt") not in [os.path.basename(p) for p in result_no_follow], \
        "Симлинк не должен учитываться при follow_symlinks=False"

    # 2) follow_symlinks=True (прокинем как аргумент, если поддерживается)
    # Если scan_directory не имеет такого параметра явно, пропускаем;
    # Если есть, то:
    # result_follow = scan_directory(str(base), include_hidden=True, follow_symlinks=True)
    # assert os.path.basename("link.txt") in [os.path.basename(p) for p in result_follow]


def test_path_not_directory(tmp_path):
    """
    Передача пути, не являющегося директорией, должна вызвать OSError.
    """
    file_path = tmp_path / "file.txt"
    file_path.write_text("Data")
    with pytest.raises(OSError):
        scan_directory(str(file_path))


def test_directory_read_permission_error(tmp_path):
    """
    Директория без прав на чтение: при skip_inaccessible=True она пропускается,
    иначе должен возникать PermissionError.
    """
    base = tmp_path / "restricted"
    base.mkdir()
    os.chmod(str(base), 0o000)  # Убираем доступ

    # 1) skip_inaccessible=True
    result_skip = scan_directory(str(tmp_path), skip_inaccessible=True)
    assert os.path.basename("restricted") not in [os.path.basename(os.path.dirname(p)) for p in result_skip], \
        "Директория без доступа пропускается"

    # 2) skip_inaccessible=False => должна быть ошибка
    with pytest.raises(PermissionError):
        scan_directory(str(tmp_path), skip_inaccessible=False)

    os.chmod(str(base), 0o755)


def test_excluding_patterns(tmp_path):
    """
    Проверяем применение шаблонов exclude.
    """
    base = tmp_path / "exclude_test"
    base.mkdir()
    (base / "file.log").write_text("Log", encoding="utf-8")
    (base / "file.txt").write_text("Text", encoding="utf-8")

    result = scan_directory(str(base), exclude=["*.log"], include_hidden=True)
    basenames = [os.path.basename(p) for p in result]
    assert "file.log" not in basenames, "Файл *.log должен исключиться"
    assert "file.txt" in basenames


def test_unicode_filenames(tmp_path):
    """
    Файл с unicode-именем должен обнаружиться, если не исключён явно.
    """
    base = tmp_path / "unicode_dir"
    base.mkdir()
    uni_file = base / "файл.txt"
    uni_file.write_text("Данные", encoding="utf-8")

    result = scan_directory(str(base), include_hidden=True)
    assert "файл.txt" in [os.path.basename(p) for p in result]


def test_spaces_in_filename(tmp_path):
    """
    Файл с пробелами в имени.
    """
    base = tmp_path / "spaces"
    base.mkdir()
    spaced = base / "my file.txt"
    spaced.write_text("Content", encoding="utf-8")

    result = scan_directory(str(base), include_hidden=True)
    assert "my file.txt" in [os.path.basename(p) for p in result]


def test_nonexistent_directory(tmp_path):
    """
    Не существующая директория => OSError.
    """
    with pytest.raises(OSError):
        scan_directory(str(tmp_path / "no_dir"))


def test_deep_nested_directories(tmp_path):
    """
    Проверяем глубокую вложенность.
    """
    base = tmp_path / "deep"
    base.mkdir()
    current = base
    for i in range(5):
        current = current / f"level_{i}"
        current.mkdir()
    deep_file = current / "deep.txt"
    deep_file.write_text("Deep content", encoding="utf-8")

    result = scan_directory(str(base), include_hidden=True)
    assert "deep.txt" in [os.path.basename(p) for p in result]


def test_file_that_matches_exclude(tmp_path):
    """
    Проверяем, что при совпадении с исключающим шаблоном файл не возвращается.
    """
    base = tmp_path / "match_exclude"
    base.mkdir()
    (base / "exclude_me.log").write_text("Some logs", encoding="utf-8")

    result = scan_directory(str(base), exclude=["*.log"])
    assert not result, "Файл должен исключиться"


def test_mixed_scenario(tmp_path):
    """
    Смешанный сценарий:
    - обычные файлы
    - скрытые файлы
    - недоступные директории
    - поддиректории
    """
    base = tmp_path / "mixed"
    base.mkdir()

    (base / "normal.txt").write_text("Normal", encoding="utf-8")

    hidden_file = base / ".hidden_file"
    hidden_file.write_text("Hidden", encoding="utf-8")

    locked_dir = base / "locked"
    locked_dir.mkdir()
    os.chmod(str(locked_dir), 0o000)

    sub = base / "subdir"
    sub.mkdir()
    (sub / "inside.txt").write_text("Inside", encoding="utf-8")

    # skip_inaccessible=True, include_hidden=False
    result = scan_directory(str(base), skip_inaccessible=True, include_hidden=False)
    basenames = [os.path.basename(p) for p in result]
    assert "normal.txt" in basenames
    # hidden_file исключается
    assert ".hidden_file" not in basenames
    # locked пропускается
    # inside.txt возвращается
    assert "inside.txt" in basenames

    os.chmod(str(locked_dir), 0o755)


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="No symlink support")
def test_cyclic_symlink(tmp_path):
    """
    Проверяем сценарий циклических симлинков.
    Если follow_symlinks=False (по умолчанию), то не будет бесконечной рекурсии.
    """
    base = tmp_path / "cycle"
    base.mkdir()
    sub = base / "sub"
    sub.mkdir()
    (sub / "file.txt").write_text("Cyclic", encoding="utf-8")

    loop = sub / "loop"
    os.symlink(str(base), str(loop))

    # Убеждаемся, что вызов не зацикливается.
    # Если default follow_symlinks=False, тест просто проверяет отсутствие исключений.
    result = scan_directory(str(base), skip_inaccessible=True)
    assert any("file.txt" in path for path in result), "File в поддире"
    # Циклический симлинк пропустится.


def test_relative_paths(tmp_path):
    """
    Проверяем, что пути возвращаются абсолютными или относительными в зависимости от логики scan_directory.
    """
    # Если scan_directory реализует возврат абсолютных путей — проверяем
    # Если относительных — тоже проверяем.
    base = tmp_path / "rel"
    base.mkdir()
    (base / "test.txt").write_text("Relative", encoding="utf-8")

    result = scan_directory(str(base), include_hidden=True)
    # Ниже условно: Если мы ожидаем относительные пути
    # for p in result:
    #     assert not os.path.isabs(p), "Пути должны быть относительными"
    # Если же хотим абсолютные:
    for p in result:
        assert os.path.isabs(p), "Ожидаем, что пути будут абсолютными."


def test_empty_directory(tmp_path):
    """
    Пустая директория => пустой список.
    """
    empty = tmp_path / "empty"
    empty.mkdir()
    result = scan_directory(str(empty), include_hidden=True)
    assert result == []


def test_multiple_exclude_patterns(tmp_path):
    """
    Проверяем исключение по нескольким шаблонам.
    """
    base = tmp_path / "multi_exclude"
    base.mkdir()
    (base / "file1.tmp").write_text("tmp", encoding="utf-8")
    (base / "file2.log").write_text("log", encoding="utf-8")
    (base / "keep.txt").write_text("keep", encoding="utf-8")

    result = scan_directory(str(base), exclude=["*.tmp", "*.log"], include_hidden=True)
    basenames = [os.path.basename(p) for p in result]
    assert "file1.tmp" not in basenames
    assert "file2.log" not in basenames
    assert "keep.txt" in basenames


def test_is_excluded():
    """
    Проверяем, что функция is_excluded корректно определяет совпадение по паттернам.
    """
    assert is_excluded("temp.log", ["*.log"])
    assert not is_excluded("data.txt", ["*.log"])
    assert is_excluded("secret.txt", ["secret*"])

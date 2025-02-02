import os
import pytest
from find_duplicates.modules.scanner import scan_directory, is_excluded


# Фикстура для создания тестовой директории с обычным и скрытым файлом
@pytest.fixture
def test_dir(tmp_path):
    d = tmp_path / "test_dir"
    d.mkdir()
    (d / "file.txt").write_text("Content", encoding="utf-8")
    (d / ".hidden.txt").write_text("Hidden", encoding="utf-8")
    return d


# Параметризованный тест для проверки параметра include_hidden
@pytest.mark.parametrize("include_hidden, expected", [
    (False, ["file.txt"]),
    (True, ["file.txt", ".hidden.txt"]),
])
def test_include_hidden(test_dir, include_hidden, expected):
    result = scan_directory(str(test_dir), include_hidden=include_hidden)
    assert sorted(result) == sorted(expected)


def test_nested_directories(tmp_path):
    # Тест: рекурсивный обход вложенных директорий
    base = tmp_path / "test_dir"
    base.mkdir()
    subdir = base / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("Nested")
    result = scan_directory(str(base), include_hidden=True)
    assert "subdir/nested.txt" in result


def test_symlink_handling(tmp_path):
    # Тест: обработка символических ссылок
    base = tmp_path / "test_dir"
    base.mkdir()
    target_file = base / "file.txt"
    target_file.write_text("Content")
    symlink_path = base / "link.txt"
    if hasattr(os, "symlink"):
        os.symlink(str(target_file), str(symlink_path))
        result_no_follow = scan_directory(str(base), include_hidden=True, follow_symlinks=False)
        assert "link.txt" not in result_no_follow
        result_follow = scan_directory(str(base), include_hidden=True, follow_symlinks=True)
        assert "link.txt" in result_follow
    else:
        pytest.skip("Symlinks not supported")


def test_path_not_directory(tmp_path):
    # Тест: передача файла вместо директории должна вызвать OSError
    file_path = tmp_path / "file.txt"
    file_path.write_text("Content")
    with pytest.raises(OSError):
        scan_directory(str(file_path))


def test_files_without_permission(tmp_path):
    # Тест: файлы без прав на чтение не возвращаются
    file_path = tmp_path / "noread.txt"
    file_path.write_text("Secret")
    os.chmod(str(file_path), 0o000)
    result = scan_directory(str(tmp_path), include_hidden=True)
    assert "noread.txt" not in result
    os.chmod(str(file_path), 0o644)


@pytest.mark.parametrize("exclude_patterns, expected_files", [
    (["*.txt"], []),
    ([".*"], ["file.txt"]),
])
def test_exclude_patterns(tmp_path, exclude_patterns, expected_files):
    # Тест: применение шаблонов исключения
    d = tmp_path / "test_dir"
    d.mkdir()
    (d / "file.txt").write_text("Content")
    (d / "keep.log").write_text("Log data")
    result = scan_directory(str(d), exclude=exclude_patterns, include_hidden=True)
    for f in result:
        for pattern in exclude_patterns:
            # Функция is_excluded должна возвращать False для файлов, не подлежащих исключению
            assert not is_excluded(f, [pattern])
    for exp in expected_files:
        assert exp in result


def test_unicode_filenames(tmp_path):
    # Тест: файл с non-ASCII именем
    d = tmp_path / "test_dir"
    d.mkdir()
    (d / "файл.txt").write_text("Unicode", encoding="utf-8")
    result = scan_directory(str(d), include_hidden=True)
    assert "файл.txt" in result


def test_spaces_in_filename(tmp_path):
    # Тест: файл с пробелами в имени
    d = tmp_path / "test_dir"
    d.mkdir()
    (d / "file with spaces.txt").write_text("Spaces")
    result = scan_directory(str(d), include_hidden=True)
    assert "file with spaces.txt" in result


def test_nonexistent_directory(tmp_path):
    # Тест: передача несуществующей директории должна вызвать OSError
    non_exist = tmp_path / "nonexistent"
    with pytest.raises(OSError):
        scan_directory(str(non_exist))


def test_deep_nested_directories(tmp_path):
    # Тест: глубокая вложенность директорий
    base = tmp_path / "test_dir"
    base.mkdir()
    deep = base
    for i in range(5):
        deep = deep / f"nested{i}"
        deep.mkdir()
    (deep / "deep.txt").write_text("Deep content")
    result = scan_directory(str(base), include_hidden=True)
    expected_rel = os.path.relpath(str(deep / "deep.txt"), str(base))
    assert expected_rel in result


def test_multiple_exclude_patterns(tmp_path):
    # Тест: исключение файлов по нескольким шаблонам
    d = tmp_path / "test_dir"
    d.mkdir()
    for fname, content in [("a.txt", "A"), ("b.log", "B"), ("c.tmp", "C")]:
        (d / fname).write_text(content)
    result = scan_directory(str(d), exclude=["*.txt", "*.tmp"], include_hidden=True)
    assert "a.txt" not in result
    assert "c.tmp" not in result
    assert "b.log" in result


def test_relative_paths(tmp_path):
    # Тест: возвращаемые пути должны быть относительными
    d = tmp_path / "test_dir"
    d.mkdir()
    (d / "relative.txt").write_text("Relative")
    result = scan_directory(str(d), include_hidden=True)
    for path in result:
        assert not os.path.isabs(path)


def test_empty_directory(tmp_path):
    # Тест: пустая директория должна вернуть пустой список
    empty = tmp_path / "empty"
    empty.mkdir()
    result = scan_directory(str(empty), include_hidden=True)
    assert result == []

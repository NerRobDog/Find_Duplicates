import os
import io
import pytest
from find_duplicates.modules.output import write_duplicates_to_csv, print_results, save_results_to_file


@pytest.mark.parametrize("duplicates", [
    {"group1": ["file1.txt", "file2.txt"], "group2": ["file3.txt"]},
    {}
])
def test_write_duplicates_to_csv(tmp_path, duplicates):
    # Тест: корректная запись словаря в CSV
    output_file = tmp_path / "duplicates.csv"
    write_duplicates_to_csv(duplicates, str(output_file))
    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
    if duplicates:
        assert "," in content  # Проверка наличия разделителей
    else:
        assert len(content) >= 0


def test_write_duplicates_to_csv_invalid_path(tmp_path):
    # Тест: несуществующий путь для записи должен вызвать ошибку
    invalid_path = os.path.join(str(tmp_path / "nonexistent_dir"), "duplicates.csv")
    with pytest.raises(Exception):
        write_duplicates_to_csv({"group": ["file.txt"]}, invalid_path)


def test_print_results(capsys):
    # Тест: вывод через print_results
    duplicates = {"group1": ["file1.txt", "file2.txt"]}
    print_results(duplicates)
    captured = capsys.readouterr().out
    assert "group1" in captured
    assert "file1.txt" in captured
    assert "file2.txt" in captured


@pytest.mark.parametrize("results", [
    {"group1": ["file1.txt"]},
    {"группа": ["файл.txt", "другой.txt"]}
])
def test_save_results_to_file(tmp_path, results):
    # Тест: сохранение результатов в текстовый файл с поддержкой Unicode
    output_file = tmp_path / "results.txt"
    save_results_to_file(results, str(output_file))
    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
    for key, files in results.items():
        assert key in content
        for file in files:
            assert file in content


def test_rewrite_existing_file(tmp_path):
    # Тест: перезапись существующего файла
    output_file = tmp_path / "results.txt"
    output_file.write_text("Old Content", encoding="utf-8")
    results = {"group1": ["file1.txt", "file2.txt"]}
    save_results_to_file(results, str(output_file))
    new_content = output_file.read_text(encoding="utf-8")
    assert new_content != "Old Content"


def test_large_number_of_groups(tmp_path):
    # Тест: запись большого количества групп
    duplicates = {f"group{i}": [f"file{i}_1.txt", f"file{i}_2.txt"] for i in range(100)}
    output_file = tmp_path / "large.csv"
    write_duplicates_to_csv(duplicates, str(output_file))
    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) >= 100


def test_error_handling_in_save_results(tmp_path):
    # Тест: ошибка записи при недоступной директории
    no_write_dir = tmp_path / "no_write"
    no_write_dir.mkdir()
    os.chmod(str(no_write_dir), 0o444)
    output_file = no_write_dir / "results.txt"
    with pytest.raises(Exception):
        save_results_to_file({"group": ["file.txt"]}, str(output_file))
    os.chmod(str(no_write_dir), 0o755)

import hashlib


def compute_hash(filepath: str, hash_type: str = "sha256") -> str:
    """
    Вычисляет хэш файла указанного типа.

    :param filepath: Путь к файлу.
    :param hash_type: Тип хэша (md5, sha1, sha256, sha512). По умолчанию sha256.
    :return: Хэш файла в шестнадцатеричном формате.
    """


def get_partial_content(filepath, size=1024) -> bytes:
    """Returns a partial content of a file.

    Args:
        filepath (str): The path to the file to read.
        size (int, optional): The number of bytes to read. Defaults to 1024.
    Returns:
        bytes: A partial content of the file.
    """
    pass

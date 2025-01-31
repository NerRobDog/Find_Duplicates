import hashlib

try:
    import blake3  # Попробуем импортировать blake3

    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False


def compute_hash(filepath: str, hash_type: str = "blake3", block_size: int = 16 * 1024 * 1024) -> str:
    """
    Вычисляет хэш файла указанного типа.

    :param filepath: Путь к файлу.
    :type filepath: Str
    :param hash_type: Тип хэша (md5, sha1, sha256, sha512, blake3). По умолчанию blake3.
    :type hash_type: Str
    :param block_size: Размер блока для чтения файла. По умолчанию 16 МБ.
    :type block_size: Int

    :return: Хэш файла в шестнадцатеричном формате.
    """
    if hash_type == "blake3":
        if not BLAKE3_AVAILABLE:
            raise ValueError("BLAKE3 не установлен. Установите его через `pip install blake3`.")
        hasher = blake3.blake3()
    else:
        hasher = hashlib.new(hash_type)  # Для sha256, md5 и других стандартных алгоритмов

    with open(filepath, "rb") as f:
        while chunk := f.read(block_size):
            hasher.update(chunk)

    return hasher.hexdigest()

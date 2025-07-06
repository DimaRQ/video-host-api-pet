import magic


def is_mp4(path: str | bytes) -> bool:
    """
    Check file mime type
    :param path: path to file
    :return: True if file is mp4
    """
    if isinstance(path, bytes):
        mime = magic.from_buffer(path, mime=True)
    else:
        mime = magic.from_file(path, mime=True)
    return mime == "video/mp4"

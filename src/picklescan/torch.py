import io
from pickletools import genops
from typing import IO, Optional


class InvalidMagicError(Exception):
    def __init__(self, provided_magic: Optional[int], magic: int, file: str):
        self.provided_magic = provided_magic
        self.magic = magic
        self.file = file
        super().__init__()

    def __str__(self) -> str:
        return f"{self.file}: {self.provided_magic} != {self.magic}"


# copied from pytorch code
# https://github.com/pytorch/pytorch/blob/664058fa83f1d8eede5d66418abff6e20bd76ca8/torch/serialization.py#L28
MAGIC_NUMBER = 0x1950A86A20F9469CFC6C


# copied from pytorch code
# https://github.com/pytorch/pytorch/blob/664058fa83f1d8eede5d66418abff6e20bd76ca8/torch/serialization.py#L272
def _is_compressed_file(f) -> bool:
    compress_modules = ["gzip"]
    try:
        return f.__module__ in compress_modules
    except AttributeError:
        return False


# copied from pytorch code
# https://github.com/pytorch/pytorch/blob/664058fa83f1d8eede5d66418abff6e20bd76ca8/torch/serialization.py#L280
def _should_read_directly(f):
    """
    Checks if f is a file that should be read directly. It should be read
    directly if it is backed by a real file (has a fileno) and is not a
    a compressed file (e.g. gzip)
    """
    if _is_compressed_file(f):
        return False
    try:
        return f.fileno() >= 0
    except io.UnsupportedOperation:
        return False
    except AttributeError:
        return False


# copied from pytorch code
# https://github.com/pytorch/pytorch/blob/0b3316ad2c6ff61416597ef29e8865876dcb12f5/torch/serialization.py#L66
def _is_zipfile(f) -> bool:
    # This is a stricter implementation than zipfile.is_zipfile().
    # zipfile.is_zipfile() is True if the magic number appears anywhere in the
    # binary. Since we expect the files here to be generated by torch.save or
    # torch.jit.save, it's safe to only check the start bytes and avoid
    # collisions and assume the zip has only 1 file.
    # See bugs.python.org/issue28494.

    # Read the first 4 bytes of the file
    read_bytes = []
    start = f.tell()

    byte = f.read(1)
    while byte != b"":
        read_bytes.append(byte)
        if len(read_bytes) == 4:
            break
        byte = f.read(1)
    f.seek(start)

    local_header_magic_number = [b"P", b"K", b"\x03", b"\x04"]
    return read_bytes == local_header_magic_number


def get_magic_number(data: IO[bytes]) -> Optional[int]:
    for opcode, args, _pos in genops(data):
        if "INT" in opcode.name or "LONG" in opcode.name:
            data.seek(0)
            return int(args)
    return None

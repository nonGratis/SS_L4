import os
from typing import Optional


class BlockDevice:
    """Блоковий пристрій - файл або пам'ять"""

    def __init__(self, filename: str, block_size: int = 4096, total_blocks: int = 1024):
        self.filename = filename
        self.block_size = block_size
        self.total_blocks = total_blocks
        self.total_size = block_size * total_blocks

    def create_storage(self):
        """Створити файл-носій"""
        with open(self.filename, "wb") as f:
            f.write(b"\x00" * self.total_size)

    def read_block(self, block_num: int) -> bytes:
        """Читати блок"""
        if block_num >= self.total_blocks:
            raise ValueError(f"Блок {block_num} поза межами")

        with open(self.filename, "rb") as f:
            f.seek(block_num * self.block_size)
            return f.read(self.block_size)

    def write_block(self, block_num: int, data: bytes):
        """Записати блок"""
        if block_num >= self.total_blocks:
            raise ValueError(f"Блок {block_num} поза межами")

        if len(data) > self.block_size:
            data = data[: self.block_size]
        elif len(data) < self.block_size:
            data = data.ljust(self.block_size, b"\x00")

        with open(self.filename, "r+b") as f:
            f.seek(block_num * self.block_size)
            f.write(data)

    def exists(self) -> bool:
        """Перевірити чи існує файл-носій"""
        return os.path.exists(self.filename)

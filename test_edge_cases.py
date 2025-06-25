#!/usr/bin/env python3
"""
Тести для консольного інтерфейсу та пропущених частин коду
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from block_device import BlockDevice
from filesystem import FileSystem
from main import CLI
from vfs import VFS


class TestCLI:
    """Тести консольного інтерфейсу"""

    def setup_method(self):
        """Підготовка"""
        fd, self.temp_filename = tempfile.mkstemp()
        os.close(fd)
        os.unlink(self.temp_filename)
        self.cli = CLI()

    def teardown_method(self):
        """Очищення"""
        if os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)
        if os.path.exists("storage.bin"):
            os.unlink("storage.bin")

    def test_init_fs_existing(self):
        """Тест ініціалізації з існуючою ФС"""
        # Створити ФС
        device = BlockDevice(self.temp_filename)
        fs = FileSystem(device)
        vfs = VFS(fs)
        vfs.mkfs(10)

        # Тепер спробувати завантажити
        self.cli.init_fs(self.temp_filename)
        assert self.cli.vfs is not None

    def test_init_fs_nonexistent(self):
        """Тест ініціалізації без існуючої ФС"""
        result = self.cli.init_fs("nonexistent.bin")
        assert not result
        assert self.cli.vfs is None

    def test_ensure_fs_not_initialized(self):
        """Тест перевірки неініціалізованої ФС"""
        assert not self.cli.ensure_fs()

    def test_ensure_fs_initialized(self):
        """Тест перевірки ініціалізованої ФС"""
        self.cli.init_fs()
        self.cli.vfs = MagicMock()  # Mock VFS
        assert self.cli.ensure_fs()

    def test_show_help(self):
        """Тест команди help"""
        with patch("builtins.print") as mock_print:
            self.cli.show_help()
            mock_print.assert_called()

    @patch("builtins.input", return_value="5")
    def test_cmd_mkfs_valid(self, mock_input):
        """Тест команди mkfs з валідними параметрами"""
        with patch("builtins.print"):
            self.cli.cmd_mkfs(["mkfs", "5"])
            assert self.cli.vfs is not None

    def test_cmd_mkfs_invalid_args(self):
        """Тест команди mkfs з невалідними аргументами"""
        with patch("builtins.print") as mock_print:
            self.cli.cmd_mkfs(["mkfs"])
            mock_print.assert_called_with("Використання: mkfs <кількість_дескрипторів>")

    def test_cmd_mkfs_invalid_number(self):
        """Тест команди mkfs з невалідним числом"""
        with patch("builtins.print") as mock_print:
            self.cli.cmd_mkfs(["mkfs", "abc"])
            mock_print.assert_called_with("Невірний формат числа")

    def test_cmd_mkfs_zero_inodes(self):
        """Тест команди mkfs з нулевою кількістю дескрипторів"""
        with patch("builtins.print") as mock_print:
            self.cli.cmd_mkfs(["mkfs", "0"])
            mock_print.assert_called_with("Кількість дескрипторів має бути > 0")

    def test_cmd_stat_invalid_args(self):
        """Тест команди stat з невалідними аргументами"""
        # Встановити mock VFS, щоб пройти перевірку ensure_fs
        self.cli.vfs = MagicMock()
        with patch("builtins.print") as mock_print:
            self.cli.cmd_stat(["stat"])
            mock_print.assert_called_with("Використання: stat <ім'я_файла>")

    def test_cmd_create_invalid_args(self):
        """Тест команди create з невалідними аргументами"""
        self.cli.vfs = MagicMock()
        with patch("builtins.print") as mock_print:
            self.cli.cmd_create(["create"])
            mock_print.assert_called_with("Використання: create <ім'я_файла>")

    def test_cmd_open_invalid_args(self):
        """Тест команди open з невалідними аргументами"""
        self.cli.vfs = MagicMock()
        with patch("builtins.print") as mock_print:
            self.cli.cmd_open(["open"])
            mock_print.assert_called_with("Використання: open <ім'я_файла>")

    def test_cmd_close_invalid_args(self):
        """Тест команди close з невалідними аргументами"""
        self.cli.vfs = MagicMock()
        with patch("builtins.print") as mock_print:
            self.cli.cmd_close(["close"])
            mock_print.assert_called_with("Використання: close <fd>")

    def test_cmd_seek_invalid_args(self):
        """Тест команди seek з невалідними аргументами"""
        self.cli.vfs = MagicMock()
        with patch("builtins.print") as mock_print:
            self.cli.cmd_seek(["seek"])
            mock_print.assert_called_with("Використання: seek <fd> <зсув>")

    def test_cmd_read_invalid_args(self):
        """Тест команди read з невалідними аргументами"""
        self.cli.vfs = MagicMock()
        with patch("builtins.print") as mock_print:
            self.cli.cmd_read(["read"])
            mock_print.assert_called_with("Використання: read <fd> <розмір>")

    def test_cmd_write_invalid_args(self):
        """Тест команди write з невалідними аргументами"""
        self.cli.vfs = MagicMock()
        with patch("builtins.print") as mock_print:
            self.cli.cmd_write(["write"])
            mock_print.assert_called_with("Використання: write <fd>")


class TestVFSEdgeCases:
    """Тести граничних випадків VFS"""

    def setup_method(self):
        """Підготовка"""
        fd, self.temp_filename = tempfile.mkstemp()
        os.close(fd)
        os.unlink(self.temp_filename)
        self.device = BlockDevice(self.temp_filename, block_size=512, total_blocks=20)
        self.fs = FileSystem(self.device, max_inodes=5)
        self.vfs = VFS(self.fs)

    def teardown_method(self):
        """Очищення"""
        if os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)

    def test_mkfs_existing_storage(self):
        """Тест mkfs на існуючому носії - має не вдатися"""
        # Створити файл носія
        self.device.create_storage()

        # Ініціалізація на існуючому файлі має не вдатися
        assert not self.vfs.mkfs(5)

    def test_stat_invalid_inode(self):
        """Тест stat з невалідним inode"""
        self.vfs.mkfs(5)

        # Додати файл в директорію, але не створити inode
        self.fs.root_directory["broken"] = 0
        self.fs.inodes[0] = None

        result = self.vfs.stat("broken")
        assert result is None

    def test_create_no_free_inodes(self):
        """Тест створення файлу без вільних inode"""
        self.vfs.mkfs(2)

        # Заповнити всі inode
        self.vfs.create("file1")
        self.vfs.create("file2")

        # Спроба створити третій файл
        assert not self.vfs.create("file3")

    def test_open_invalid_inode(self):
        """Тест відкриття файлу з невалідним inode"""
        self.vfs.mkfs(5)

        # Додати файл в директорію, але видалити inode
        self.fs.root_directory["broken"] = 0
        self.fs.inodes[0] = None

        result = self.vfs.open("broken")
        assert result is None

    def test_unlink_invalid_inode(self):
        """Тест unlink з невалідним inode"""
        self.vfs.mkfs(5)

        # Додати файл в директорію, але видалити inode
        self.fs.root_directory["broken"] = 0
        self.fs.inodes[0] = None

        result = self.vfs.unlink("broken")
        assert not result

    def test_truncate_invalid_inode(self):
        """Тест truncate з невалідним inode"""
        self.vfs.mkfs(5)

        # Додати файл в директорію, але видалити inode
        self.fs.root_directory["broken"] = 0
        self.fs.inodes[0] = None

        result = self.vfs.truncate("broken", 100)
        assert not result

    def test_read_invalid_inode(self):
        """Тест читання з невалідним inode"""
        self.vfs.mkfs(5)
        self.vfs.create("test")
        fd = self.vfs.open("test")

        # Видалити inode після відкриття
        inode_num = self.fs.open_files[fd].inode
        self.fs.inodes[inode_num] = None

        result = self.vfs.read(fd, 10)
        assert result is None

    def test_write_invalid_inode(self):
        """Тест запису з невалідним inode"""
        self.vfs.mkfs(5)
        self.vfs.create("test")
        fd = self.vfs.open("test")

        # Видалити inode після відкриття
        inode_num = self.fs.open_files[fd].inode
        self.fs.inodes[inode_num] = None

        result = self.vfs.write(fd, b"test")
        assert result is None

    def test_write_no_free_blocks(self):
        """Тест запису без вільних блоків"""
        # Створити дуже маленьку ФС
        small_device = BlockDevice(
            self.temp_filename + "_tiny", block_size=512, total_blocks=6
        )  # Дуже мало блоків
        small_fs = FileSystem(small_device, max_inodes=2)
        small_vfs = VFS(small_fs)

        try:
            small_vfs.mkfs(2)
            small_vfs.create("test")
            fd = small_vfs.open("test")

            # Спробувати записати багато даних (більше ніж вільних блоків)
            large_data = b"x" * 10000  # 10KB даних
            written = small_vfs.write(fd, large_data)

            # Має записати менше ніж запитано
            assert written is not None
            assert written < len(large_data)

        finally:
            tiny_file = self.temp_filename + "_tiny"
            if os.path.exists(tiny_file):
                os.unlink(tiny_file)


class TestFileSystemEdgeCases:
    """Тести граничних випадків FileSystem"""

    def setup_method(self):
        """Підготовка"""
        fd, self.temp_filename = tempfile.mkstemp()
        os.close(fd)
        os.unlink(self.temp_filename)
        self.device = BlockDevice(self.temp_filename)
        self.fs = FileSystem(self.device)

    def teardown_method(self):
        """Очищення"""
        if os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)

    def test_find_free_block_none_available(self):
        """Тест пошуку вільного блоку коли немає вільних"""
        self.device.create_storage()

        # Заповнити всі блоки
        self.fs.block_bitmap.setall(1)

        result = self.fs._find_free_block()
        assert result is None

    def test_allocate_block_none_available(self):
        """Тест виділення блоку коли немає вільних"""
        self.device.create_storage()

        # Заповнити всі блоки
        self.fs.block_bitmap.setall(1)

        result = self.fs._allocate_block()
        assert result is None

    def test_find_free_inode_none_available(self):
        """Тест пошуку вільного inode коли всі зайняті"""
        # Заповнити всі inode
        for i in range(len(self.fs.inodes)):
            self.fs.inodes[i] = MagicMock()

        result = self.fs._find_free_inode()
        assert result is None

    def test_load_metadata_no_device(self):
        """Тест завантаження метаданих без створеного носія"""
        result = self.fs.load_metadata()
        assert not result


class TestBlockDeviceEdgeCases:
    """Тести граничних випадків BlockDevice"""

    def setup_method(self):
        """Підготовка"""
        fd, self.temp_filename = tempfile.mkstemp()
        os.close(fd)
        os.unlink(self.temp_filename)
        self.device = BlockDevice(self.temp_filename)

    def teardown_method(self):
        """Очищення"""
        if os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)

    def test_write_oversized_data(self):
        """Тест запису даних більших за блок"""
        self.device.create_storage()

        # Дані більші за розмір блоку
        oversized_data = b"x" * (self.device.block_size + 100)

        self.device.write_block(0, oversized_data)

        # Прочитати і перевірити що дані обрізані
        read_data = self.device.read_block(0)
        assert len(read_data) == self.device.block_size
        assert read_data == b"x" * self.device.block_size

    def test_write_undersized_data(self):
        """Тест запису даних менших за блок"""
        self.device.create_storage()

        # Дані менші за розмір блоку
        small_data = b"hello"

        self.device.write_block(0, small_data)

        # Прочитати і перевірити що дані доповнені нулями
        read_data = self.device.read_block(0)
        assert len(read_data) == self.device.block_size
        assert read_data.startswith(b"hello")
        assert read_data[5:] == b"\x00" * (self.device.block_size - 5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

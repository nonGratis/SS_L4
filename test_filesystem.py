#!/usr/bin/env python3
"""
Прості тести для файлової системи
"""

import pytest
import os
import tempfile
from block_device import BlockDevice
from filesystem import FileSystem
from vfs import VFS
from inode import Inode


class TestFileSystemBasics:
    """Базові тести файлової системи"""
    
    def setup_method(self):
        """Налаштування перед кожним тестом"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.filename = self.temp_file.name
        
        self.device = BlockDevice(self.filename)
        self.fs = FileSystem(self.device)
        self.vfs = VFS(self.fs)
    
    def teardown_method(self):
        """Очистка після кожного тесту"""
        try:
            os.unlink(self.filename)
        except FileNotFoundError:
            pass
    
    def test_mkfs_initialization(self):
        """Тест ініціалізації файлової системи"""
        # Створити ФС
        result = self.vfs.mkfs(10)
        
        # Якщо файл уже існує, видалити його та спробувати знову
        if not result:
            if os.path.exists(self.filename):
                os.unlink(self.filename)
            self.device = BlockDevice(self.filename)
            self.fs = FileSystem(self.device)
            self.vfs = VFS(self.fs)
            assert self.vfs.mkfs(10)
        
        # Перевірити бітову карту - має бути ініціалізована
        assert len(self.fs.block_bitmap) > 0
        assert not all(self.fs.block_bitmap)  # Не всі блоки зайняті
        
        # Перевірити inode масив
        assert len(self.fs.inodes) == 10
        assert all(inode is None for inode in self.fs.inodes)
    
    def test_inode_allocation(self):
        """Тест виділення inode"""
        self.vfs.mkfs(5)
        
        # Знайти вільний inode
        inode_num = self.fs._find_free_inode()
        assert inode_num == 0
        
        # Виділити inode
        self.fs.inodes[inode_num] = Inode('file')
        
        # Наступний вільний повинен бути 1
        next_inode = self.fs._find_free_inode()
        assert next_inode == 1
    
    def test_inode_exhaustion(self):
        """Тест переповнення inode"""
        # Видалити файл якщо існує та створити нову ФС
        if os.path.exists(self.filename):
            os.unlink(self.filename)
        
        self.device = BlockDevice(self.filename)
        self.fs = FileSystem(self.device)
        self.vfs = VFS(self.fs)
        
        self.vfs.mkfs(2)
        
        # Перевірити що у нас дійсно 2 inode
        assert len(self.fs.inodes) == 2
        
        # Створити максимальну кількість файлів
        assert self.vfs.create("file1")
        assert self.vfs.create("file2")
        
        # Перевірити що всі inode зайняті
        free_inode = self.fs._find_free_inode()
        assert free_inode is None
        
        # Спроба створити ще один файл має не вдатися
        assert not self.vfs.create("file3")
    
    def test_block_allocation(self):
        """Тест виділення блоків"""
        self.vfs.mkfs(10)
        
        # Знайти вільний блок
        block_num = self.fs._find_free_block()
        assert block_num is not None
        
        # Виділити блок
        allocated = self.fs._allocate_block()
        assert allocated is not None
        assert self.fs.block_bitmap[allocated] == 1
    
    def test_block_free(self):
        """Тест звільнення блоків"""
        self.vfs.mkfs(10)
        
        # Виділити блок
        block_num = self.fs._allocate_block()
        assert self.fs.block_bitmap[block_num] == 1
        
        # Звільнити блок
        self.fs._free_block(block_num)
        assert self.fs.block_bitmap[block_num] == 0


class TestFileOperations:
    """Тести файлових операцій"""
    
    def setup_method(self):
        """Налаштування перед кожним тестом"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.filename = self.temp_file.name
        
        self.device = BlockDevice(self.filename)
        self.fs = FileSystem(self.device)
        self.vfs = VFS(self.fs)
        self.vfs.mkfs(10)
    
    def teardown_method(self):
        """Очистка після кожного тесту"""
        try:
            os.unlink(self.filename)
        except FileNotFoundError:
            pass
    
    def test_create_file(self):
        """Тест створення файлу"""
        # Створити файл
        assert self.vfs.create("test.txt")
        
        # Перевірити що файл з'явився в директорії
        files = self.vfs.ls()
        assert "test.txt" in files
        
        # Спроба створити файл з тим же ім'ям має не вдатися
        assert not self.vfs.create("test.txt")
    
    def test_file_stat(self):
        """Тест отримання інформації про файл"""
        self.vfs.create("test.txt")
        
        stat = self.vfs.stat("test.txt")
        assert stat is not None
        assert stat['type'] == 'file'
        assert stat['hard_links'] == 1
        assert stat['size'] == 0
    
    def test_open_close_file(self):
        """Тест відкриття та закриття файлу"""
        self.vfs.create("test.txt")
        
        # Відкрити файл
        fd = self.vfs.open("test.txt")
        assert fd is not None
        assert fd >= 0
        
        # Закрити файл
        assert self.vfs.close(fd)
        
        # Повторне закриття має не вдатися
        assert not self.vfs.close(fd)
    
    def test_open_nonexistent_file(self):
        """Тест відкриття неіснуючого файлу"""
        fd = self.vfs.open("nonexistent.txt")
        assert fd is None
    
    def test_multiple_file_descriptors(self):
        """Тест множинних дескрипторів"""
        self.vfs.create("test.txt")
        
        # Відкрити файл двічі
        fd1 = self.vfs.open("test.txt")
        fd2 = self.vfs.open("test.txt")
        
        assert fd1 != fd2
        assert self.vfs.close(fd1)
        assert self.vfs.close(fd2)
    
    def test_seek_operation(self):
        """Тест позиціонування в файлі"""
        self.vfs.create("test.txt")
        fd = self.vfs.open("test.txt")
        
        # Встановити позицію
        assert self.vfs.seek(fd, 100)
        
        # Перевірити що позиція встановлена
        open_file = self.fs.open_files[fd]
        assert open_file.offset == 100
        
        # Спроба встановити негативну позицію
        assert self.vfs.seek(fd, -10)
        assert open_file.offset == 0  # Має бути скинуто до 0
        
        self.vfs.close(fd)


class TestHardLinks:
    """Тести жорстких посилань"""
    
    def setup_method(self):
        """Налаштування перед кожним тестом"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.filename = self.temp_file.name
        
        self.device = BlockDevice(self.filename)
        self.fs = FileSystem(self.device)
        self.vfs = VFS(self.fs)
        self.vfs.mkfs(10)
    
    def teardown_method(self):
        """Очистка після кожного тесту"""
        try:
            os.unlink(self.filename)
        except FileNotFoundError:
            pass
    
    def test_create_hard_link(self):
        """Тест створення жорсткого посилання"""
        self.vfs.create("file1.txt")
        
        # Створити жорстке посилання
        assert self.vfs.link("file1.txt", "file2.txt")
        
        # Перевірити що обидва файли посилаються на той самий inode
        files = self.vfs.ls()
        assert files["file1.txt"] == files["file2.txt"]
        
        # Перевірити лічильник посилань
        stat = self.vfs.stat("file1.txt")
        assert stat['hard_links'] == 2
    
    def test_link_nonexistent_file(self):
        """Тест створення посилання на неіснуючий файл"""
        assert not self.vfs.link("nonexistent.txt", "link.txt")
    
    def test_link_existing_name(self):
        """Тест створення посилання з існуючим ім'ям"""
        self.vfs.create("file1.txt")
        self.vfs.create("file2.txt")
        
        # Спроба створити посилання з існуючим ім'ям
        assert not self.vfs.link("file1.txt", "file2.txt")
    
    def test_unlink_file(self):
        """Тест видалення посилання"""
        self.vfs.create("file1.txt")
        self.vfs.link("file1.txt", "file2.txt")
        
        # Видалити одне посилання
        assert self.vfs.unlink("file1.txt")
        
        # Перевірити що друге посилання ще існує
        assert "file1.txt" not in self.vfs.ls()
        assert "file2.txt" in self.vfs.ls()
        
        # Перевірити лічильник посилань
        stat = self.vfs.stat("file2.txt")
        assert stat['hard_links'] == 1


class TestReadWrite:
    """Тести читання та запису"""
    
    def setup_method(self):
        """Налаштування перед кожним тестом"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.filename = self.temp_file.name
        
        self.device = BlockDevice(self.filename)
        self.fs = FileSystem(self.device)
        self.vfs = VFS(self.fs)
        self.vfs.mkfs(10)
    
    def teardown_method(self):
        """Очистка після кожного тесту"""
        try:
            os.unlink(self.filename)
        except FileNotFoundError:
            pass
    
    def test_write_read_small_data(self):
        """Тест запису та читання малих даних"""
        self.vfs.create("test.txt")
        fd = self.vfs.open("test.txt")
        
        # Записати дані
        test_data = b"Hello, World!"
        bytes_written = self.vfs.write(fd, test_data)
        assert bytes_written == len(test_data)
        
        # Повернутися на початок
        self.vfs.seek(fd, 0)
        
        # Прочитати дані
        data = self.vfs.read(fd, len(test_data))
        assert data == test_data
        
        self.vfs.close(fd)
    
    def test_read_beyond_file_end(self):
        """Тест читання за межами файлу"""
        self.vfs.create("test.txt")
        fd = self.vfs.open("test.txt")
        
        # Спроба прочитати з порожнього файлу
        data = self.vfs.read(fd, 100)
        assert data == b""
        
        self.vfs.close(fd)
    
    def test_write_updates_file_size(self):
        """Тест оновлення розміру файлу при записі"""
        self.vfs.create("test.txt")
        fd = self.vfs.open("test.txt")
        
        # Записати дані
        test_data = b"Test data"
        self.vfs.write(fd, test_data)
        
        # Перевірити розмір файлу
        stat = self.vfs.stat("test.txt")
        assert stat['size'] == len(test_data)
        
        self.vfs.close(fd)
    
    def test_truncate_file(self):
        """Тест обрізання файлу"""
        self.vfs.create("test.txt")
        fd = self.vfs.open("test.txt")
        
        # Записати дані
        test_data = b"This is a long test string"
        self.vfs.write(fd, test_data)
        self.vfs.close(fd)
        
        # Обрізати файл
        assert self.vfs.truncate("test.txt", 10)
        
        # Перевірити новий розмір
        stat = self.vfs.stat("test.txt")
        assert stat['size'] == 10
        
        # Перевірити вміст
        fd = self.vfs.open("test.txt")
        data = self.vfs.read(fd, 20)
        assert data == test_data[:10]
        self.vfs.close(fd)


class TestErrorCases:
    """Тести помилкових ситуацій"""
    
    def setup_method(self):
        """Налаштування перед кожним тестом"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.filename = self.temp_file.name
        
        self.device = BlockDevice(self.filename)
        self.fs = FileSystem(self.device)
        self.vfs = VFS(self.fs)
        self.vfs.mkfs(10)
    
    def teardown_method(self):
        """Очистка після кожного тесту"""
        try:
            os.unlink(self.filename)
        except FileNotFoundError:
            pass
    
    def test_invalid_file_descriptor(self):
        """Тест з невірним дескриптором файлу"""
        # Спроба читання з невірного fd
        data = self.vfs.read(999, 10)
        assert data is None
        
        # Спроба запису з невірного fd
        bytes_written = self.vfs.write(999, b"test")
        assert bytes_written is None
        
        # Спроба позиціонування з невірного fd
        assert not self.vfs.seek(999, 0)
        
        # Спроба закриття невірного fd
        assert not self.vfs.close(999)
    
    def test_operations_on_nonexistent_file(self):
        """Тест операцій з неіснуючими файлами"""
        # Спроба отримати статистику неіснуючого файлу
        stat = self.vfs.stat("nonexistent.txt")
        assert stat is None
        
        # Спроба видалити неіснуючий файл
        assert not self.vfs.unlink("nonexistent.txt")
        
        # Спроба обрізати неіснуючий файл
        assert not self.vfs.truncate("nonexistent.txt", 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

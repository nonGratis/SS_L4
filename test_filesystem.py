#!/usr/bin/env python3
"""
Тести для файлової системи
"""

import os
import tempfile
import pytest
from block_device import BlockDevice
from filesystem import FileSystem
from vfs import VFS
from inode import Inode
from open_file import OpenFile


class TestBlockDevice:
    """Тести блокового пристрою"""
    
    def setup_method(self):
        """Підготовка для кожного тесту"""
        fd, self.temp_filename = tempfile.mkstemp()
        os.close(fd)
        os.unlink(self.temp_filename)  # Видалити файл, щоб він не існував
        self.device = BlockDevice(self.temp_filename, block_size=512, total_blocks=100)
    
    def teardown_method(self):
        """Очищення після кожного тесту"""
        if os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)
    
    def test_create_storage(self):
        """Тест створення носія"""
        assert not self.device.exists()
        self.device.create_storage()
        assert self.device.exists()
        
        # Перевірити розмір файлу
        assert os.path.getsize(self.temp_filename) == 512 * 100
    
    def test_read_write_block(self):
        """Тест читання/запису блоку"""
        self.device.create_storage()
        
        # Записати тестові дані
        test_data = b"Hello, World!" + b"\x00" * (512 - 13)
        self.device.write_block(0, test_data)
        
        # Прочитати і перевірити
        read_data = self.device.read_block(0)
        assert read_data == test_data
    
    def test_block_out_of_bounds(self):
        """Тест доступу поза межами"""
        self.device.create_storage()
        
        with pytest.raises(ValueError):
            self.device.read_block(200)
        
        with pytest.raises(ValueError):
            self.device.write_block(200, b"test")


class TestInode:
    """Тести Inode"""
    
    def test_inode_creation(self):
        """Тест створення inode"""
        inode = Inode('file')
        assert inode.type == 'file'
        assert inode.hard_links == 0
        assert inode.size == 0
        assert len(inode.direct) == 10
        assert all(block is None for block in inode.direct)
        assert inode.indirect is None
    
    def test_inode_custom_direct_count(self):
        """Тест inode з кастомною кількістю прямих блоків"""
        inode = Inode('dir', direct_count=5)
        assert len(inode.direct) == 5


class TestOpenFile:
    """Тести OpenFile"""
    
    def test_open_file_creation(self):
        """Тест створення OpenFile"""
        of = OpenFile(42)
        assert of.inode == 42
        assert of.offset == 0


class TestFileSystem:
    """Тести файлової системи"""
    
    def setup_method(self):
        """Підготовка для кожного тесту"""
        fd, self.temp_filename = tempfile.mkstemp()
        os.close(fd)
        os.unlink(self.temp_filename)
        self.device = BlockDevice(self.temp_filename, block_size=512, total_blocks=100)
        self.fs = FileSystem(self.device, max_inodes=50)
    
    def teardown_method(self):
        """Очищення після кожного тесту"""
        if os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)
    
    def test_fs_initialization(self):
        """Тест ініціалізації ФС"""
        assert self.fs.max_inodes == 50
        assert self.fs.block_size == 512
        assert len(self.fs.inodes) == 50
        assert all(inode is None for inode in self.fs.inodes)
        assert len(self.fs.root_directory) == 0
    
    def test_block_allocation(self):
        """Тест виділення блоків"""
        self.device.create_storage()
        
        # Першими мають бути зайняті блоки для метаданих
        metadata_blocks = 2 + (50 * 64) // 512 + 1
        
        # Знайти перший вільний блок
        free_block = self.fs._find_free_block()
        assert free_block >= metadata_blocks
        
        # Виділити блок
        allocated = self.fs._allocate_block()
        assert allocated == free_block
        assert self.fs.block_bitmap[allocated] == 1
        
        # Звільнити блок
        self.fs._free_block(allocated)
        assert self.fs.block_bitmap[allocated] == 0
    
    def test_inode_allocation(self):
        """Тест виділення inode"""
        # Знайти вільний inode
        free_inode = self.fs._find_free_inode()
        assert free_inode == 0
        
        # Зайняти inode
        self.fs.inodes[0] = Inode('file')
        
        # Наступний вільний
        free_inode = self.fs._find_free_inode()
        assert free_inode == 1
    
    def test_save_load_metadata(self):
        """Тест збереження/завантаження метаданих"""
        self.device.create_storage()
        
        # Додати тестові дані
        self.fs.root_directory['test.txt'] = 0
        self.fs.inodes[0] = Inode('file')
        self.fs.inodes[0].hard_links = 1
        self.fs.inodes[0].size = 123
        
        # Зберегти
        self.fs.save_metadata()
        
        # Створити нову ФС і завантажити
        fs2 = FileSystem(self.device, max_inodes=50)
        assert fs2.load_metadata()
        
        # Перевірити
        assert 'test.txt' in fs2.root_directory
        assert fs2.root_directory['test.txt'] == 0
        assert fs2.inodes[0] is not None
        assert fs2.inodes[0].type == 'file'
        assert fs2.inodes[0].hard_links == 1
        assert fs2.inodes[0].size == 123


class TestVFS:
    """Тести VFS"""
    
    def setup_method(self):
        """Підготовка для кожного тесту"""
        fd, self.temp_filename = tempfile.mkstemp()
        os.close(fd)
        os.unlink(self.temp_filename)
        self.device = BlockDevice(self.temp_filename, block_size=512, total_blocks=100)
        self.fs = FileSystem(self.device, max_inodes=50)
        self.vfs = VFS(self.fs)
    
    def teardown_method(self):
        """Очищення після кожного тесту"""
        if os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)
    
    def test_mkfs(self):
        """Тест ініціалізації ФС"""
        assert self.vfs.mkfs(10)
        assert self.device.exists()
        assert self.fs.max_inodes == 10
    
    def test_create_file(self):
        """Тест створення файлу"""
        self.vfs.mkfs(10)
        
        assert self.vfs.create('test.txt')
        assert 'test.txt' in self.fs.root_directory
        
        # Не можна створити файл з таким же ім'ям
        assert not self.vfs.create('test.txt')
    
    def test_stat_file(self):
        """Тест отримання інформації про файл"""
        self.vfs.mkfs(10)
        self.vfs.create('test.txt')
        
        stat = self.vfs.stat('test.txt')
        assert stat is not None
        assert stat['type'] == 'file'
        assert stat['hard_links'] == 1
        assert stat['size'] == 0
        
        # Неіснуючий файл
        assert self.vfs.stat('nonexistent.txt') is None
    
    def test_ls(self):
        """Тест списку файлів"""
        self.vfs.mkfs(10)
        
        # Порожня директорія
        files = self.vfs.ls()
        assert len(files) == 0
        
        # Створити файли
        self.vfs.create('file1.txt')
        self.vfs.create('file2.txt')
        
        files = self.vfs.ls()
        assert len(files) == 2
        assert 'file1.txt' in files
        assert 'file2.txt' in files
    
    def test_open_close_file(self):
        """Тест відкриття/закриття файлу"""
        self.vfs.mkfs(10)
        self.vfs.create('test.txt')
        
        # Відкрити файл
        fd = self.vfs.open('test.txt')
        assert fd is not None
        assert fd in self.fs.open_files
        
        # Закрити файл
        assert self.vfs.close(fd)
        assert fd not in self.fs.open_files
        
        # Спроба відкрити неіснуючий файл
        assert self.vfs.open('nonexistent.txt') is None
    
    def test_seek(self):
        """Тест позиціонування в файлі"""
        self.vfs.mkfs(10)
        self.vfs.create('test.txt')
        fd = self.vfs.open('test.txt')
        
        # Початкова позиція
        assert self.fs.open_files[fd].offset == 0
        
        # Встановити позицію
        assert self.vfs.seek(fd, 100)
        assert self.fs.open_files[fd].offset == 100
        
        # Негативний зсув
        assert self.vfs.seek(fd, -10)
        assert self.fs.open_files[fd].offset == 0
    
    def test_write_read_file(self):
        """Тест запису/читання файлу"""
        self.vfs.mkfs(10)
        self.vfs.create('test.txt')
        fd = self.vfs.open('test.txt')
        
        # Записати дані
        test_data = b"Hello, World!"
        written = self.vfs.write(fd, test_data)
        assert written == len(test_data)
        
        # Перевірити розмір файлу
        inode_num = self.fs.open_files[fd].inode
        inode = self.fs.inodes[inode_num]
        assert inode.size == len(test_data)
        
        # Читати дані
        self.vfs.seek(fd, 0)
        read_data = self.vfs.read(fd, len(test_data))
        assert read_data == test_data
    
    def test_link_unlink(self):
        """Тест жорстких посилань"""
        self.vfs.mkfs(10)
        self.vfs.create('original.txt')
        
        # Створити посилання
        assert self.vfs.link('original.txt', 'link.txt')
        assert 'link.txt' in self.fs.root_directory
        
        # Перевірити лічильник посилань
        inode_num = self.fs.root_directory['original.txt']
        inode = self.fs.inodes[inode_num]
        assert inode.hard_links == 2
        
        # Видалити посилання
        assert self.vfs.unlink('link.txt')
        assert 'link.txt' not in self.fs.root_directory
        assert inode.hard_links == 1
        
        # Видалити останнє посилання
        assert self.vfs.unlink('original.txt')
        assert 'original.txt' not in self.fs.root_directory
        assert self.fs.inodes[inode_num] is None
    
    def test_truncate(self):
        """Тест зміни розміру файлу"""
        self.vfs.mkfs(10)
        self.vfs.create('test.txt')
        fd = self.vfs.open('test.txt')
        
        # Записати дані
        test_data = b"Hello, World! This is a long text."
        self.vfs.write(fd, test_data)
        
        inode_num = self.fs.open_files[fd].inode
        inode = self.fs.inodes[inode_num]
        original_size = inode.size
        
        # Зменшити файл
        assert self.vfs.truncate('test.txt', 10)
        assert inode.size == 10
        
        # Збільшити файл
        assert self.vfs.truncate('test.txt', original_size + 100)
        assert inode.size == original_size + 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

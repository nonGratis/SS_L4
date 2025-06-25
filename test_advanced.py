#!/usr/bin/env python3
"""
Додаткові тести для покращення покриття коду
"""

import os
import tempfile
import pytest
from block_device import BlockDevice
from filesystem import FileSystem
from vfs import VFS


class TestAdvancedScenarios:
    """Додаткові сценарії тестування"""
    
    def setup_method(self):
        """Підготовка"""
        fd, self.temp_filename = tempfile.mkstemp()
        os.close(fd)
        os.unlink(self.temp_filename)
        self.device = BlockDevice(self.temp_filename, block_size=512, total_blocks=100)
        self.fs = FileSystem(self.device, max_inodes=10)
        self.vfs = VFS(self.fs)
    
    def teardown_method(self):
        """Очищення"""
        if os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)
    
    def test_large_file_operations(self):
        """Тест операцій з великими файлами"""
        self.vfs.mkfs(5)
        self.vfs.create('large.txt')
        fd = self.vfs.open('large.txt')
        
        # Записати дані більше одного блоку
        large_data = b'A' * 1000  # 1000 байт
        written = self.vfs.write(fd, large_data)
        assert written == 1000
        
        # Читання
        self.vfs.seek(fd, 0)
        read_data = self.vfs.read(fd, 1000)
        assert read_data == large_data
        
        # Читання з середини файлу
        self.vfs.seek(fd, 500)
        partial_data = self.vfs.read(fd, 100)
        assert partial_data == b'A' * 100
    
    def test_multiple_file_operations(self):
        """Тест роботи з кількома файлами одночасно"""
        self.vfs.mkfs(10)
        
        # Створити кілька файлів
        files = ['file1.txt', 'file2.txt', 'file3.txt']
        fds = []
        
        for filename in files:
            self.vfs.create(filename)
            fd = self.vfs.open(filename)
            fds.append(fd)
        
        # Записати різні дані в файли
        for i, fd in enumerate(fds):
            data = f"File {i} content".encode()
            self.vfs.write(fd, data)
        
        # Прочитати дані назад
        for i, fd in enumerate(fds):
            self.vfs.seek(fd, 0)
            data = self.vfs.read(fd, 100)
            expected = f"File {i} content".encode()
            assert data == expected
    
    def test_file_with_holes(self):
        """Тест файлу з дірками (sparse file)"""
        self.vfs.mkfs(5)
        self.vfs.create('sparse.txt')
        fd = self.vfs.open('sparse.txt')
        
        # Записати в середину файлу
        self.vfs.seek(fd, 1000)
        self.vfs.write(fd, b"Hello")
        
        # Прочитати з початку
        self.vfs.seek(fd, 0)
        data = self.vfs.read(fd, 1005)
        
        # Перші 1000 байт мають бути нулями
        assert data[:1000] == b'\x00' * 1000
        assert data[1000:1005] == b"Hello"
    
    def test_truncate_operations(self):
        """Тест різних операцій truncate"""
        self.vfs.mkfs(5)
        self.vfs.create('test.txt')
        fd = self.vfs.open('test.txt')
        
        # Записати дані
        original_data = b"Hello, World! This is a test file."
        self.vfs.write(fd, original_data)
        
        # Скоротити файл
        self.vfs.truncate('test.txt', 10)
        
        # Перевірити розмір
        stat = self.vfs.stat('test.txt')
        assert stat['size'] == 10
        
        # Прочитати скорочені дані
        self.vfs.seek(fd, 0)
        data = self.vfs.read(fd, 20)
        assert data == b"Hello, Wor"
        
        # Збільшити файл
        self.vfs.truncate('test.txt', 50)
        stat = self.vfs.stat('test.txt')
        assert stat['size'] == 50
    
    def test_unlink_open_file(self):
        """Тест видалення посилання на відкритий файл"""
        self.vfs.mkfs(5)
        self.vfs.create('temp.txt')
        fd = self.vfs.open('temp.txt')
        
        # Записати дані
        self.vfs.write(fd, b"Temporary data")
        
        # Видалити посилання (файл залишається відкритим)
        assert self.vfs.unlink('temp.txt')
        assert 'temp.txt' not in self.vfs.ls()
        
        # Файл все ще доступний через fd
        self.vfs.seek(fd, 0)
        data = self.vfs.read(fd, 20)
        assert data == b"Temporary data"
        
        # Закрити файл - тепер він має видалитися
        self.vfs.close(fd)
    
    def test_error_conditions(self):
        """Тест різних помилкових ситуацій"""
        self.vfs.mkfs(3)
        
        # Операції без відкритих файлів
        assert self.vfs.read(999, 10) is None
        assert self.vfs.write(999, b"test") is None
        assert not self.vfs.seek(999, 0)
        assert not self.vfs.close(999)
        
        # Операції з неіснуючими файлами
        assert self.vfs.stat('nonexistent') is None
        assert self.vfs.open('nonexistent') is None
        assert not self.vfs.truncate('nonexistent', 100)
        assert not self.vfs.link('nonexistent', 'link')
        assert not self.vfs.unlink('nonexistent')
        
        # Створення файлу з існуючим ім'ям
        self.vfs.create('test.txt')
        assert not self.vfs.create('test.txt')
        
        # Створення посилання з існуючим ім'ям
        self.vfs.create('another.txt')
        assert not self.vfs.link('test.txt', 'another.txt')
    
    def test_read_past_eof(self):
        """Тест читання за межами файлу"""
        self.vfs.mkfs(5)
        self.vfs.create('small.txt')
        fd = self.vfs.open('small.txt')
        
        # Записати 10 байт
        self.vfs.write(fd, b"1234567890")
        
        # Спробувати прочитати з кінця файлу
        self.vfs.seek(fd, 10)
        data = self.vfs.read(fd, 10)
        assert data == b''
        
        # Читання більше ніж є в файлі
        self.vfs.seek(fd, 5)
        data = self.vfs.read(fd, 10)
        assert data == b"67890"
    
    def test_filesystem_full(self):
        """Тест заповненої файлової системи"""
        # Створити маленьку ФС
        small_device = BlockDevice(self.temp_filename + "_small", 
                                 block_size=512, total_blocks=10)
        small_fs = FileSystem(small_device, max_inodes=3)
        small_vfs = VFS(small_fs)
        
        try:
            small_vfs.mkfs(3)
            
            # Заповнити всі inode
            small_vfs.create('file1')
            small_vfs.create('file2')
            small_vfs.create('file3')
            
            # Спроба створити ще один файл
            assert not small_vfs.create('file4')
            
        finally:
            small_device_file = self.temp_filename + "_small"
            if os.path.exists(small_device_file):
                os.unlink(small_device_file)
    
    def test_load_corrupted_metadata(self):
        """Тест завантаження пошкоджених метаданих"""
        self.device.create_storage()
        
        # Записати неправильні дані в суперблок
        self.device.write_block(0, b"corrupted data")
        
        # Спроба завантажити має не вдатися
        assert not self.fs.load_metadata()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

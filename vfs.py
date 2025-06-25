from typing import Optional
from filesystem import FileSystem
from inode import Inode
from open_file import OpenFile

class VFS:
    """Віртуальна файлова система - емуляція частини ядра"""
    def __init__(self, fs: FileSystem):
        self.fs = fs
    
    def mkfs(self, n_inodes: int) -> bool:
        """Ініціалізувати файлову систему"""
        if self.fs.device.exists():
            return False
        
        self.fs.device.create_storage()
        self.fs.max_inodes = n_inodes
        self.fs.inodes = [None] * n_inodes
        self.fs._reserve_metadata_blocks()
        self.fs.save_metadata()
        return True
    
    def stat(self, name: str) -> Optional[dict]:
        """Отримати інформацію про файл"""
        if name not in self.fs.root_directory:
            return None
        
        inode_num = self.fs.root_directory[name]
        inode = self.fs.inodes[inode_num]
        
        if not inode:
            return None
        
        return {
            'inode_number': inode_num,
            'type': inode.type,
            'hard_links': inode.hard_links,
            'size': inode.size,
            'blocks_used': len([b for b in inode.direct if b is not None])
        }
    
    def ls(self) -> dict:
        """Список файлів в кореневій директорії"""
        return self.fs.root_directory.copy()
    
    def create(self, name: str) -> bool:
        """Створити файл"""
        if name in self.fs.root_directory:
            return False
        
        inode_num = self.fs._find_free_inode()
        if inode_num is None:
            return False
        
        inode = Inode('file')
        inode.hard_links = 1
        self.fs.inodes[inode_num] = inode
        self.fs.root_directory[name] = inode_num
        
        self.fs.save_metadata()
        return True
    
    def open(self, name: str) -> Optional[int]:
        """Відкрити файл"""
        if name not in self.fs.root_directory:
            return None
        
        inode_num = self.fs.root_directory[name]
        if not self.fs.inodes[inode_num]:
            return None
        
        # Знайти вільний fd
        fd = self.fs.next_fd
        while fd in self.fs.open_files:
            fd += 1
        
        self.fs.open_files[fd] = OpenFile(inode_num)
        self.fs.next_fd = fd + 1
        return fd
    
    def close(self, fd: int) -> bool:
        """Закрити файл"""
        if fd not in self.fs.open_files:
            return False
        
        del self.fs.open_files[fd]
        return True
    
    def seek(self, fd: int, offset: int) -> bool:
        """Встановити позицію в файлі"""
        if fd not in self.fs.open_files:
            return False
        
        self.fs.open_files[fd].offset = max(0, offset)
        return True
    
    def link(self, name1: str, name2: str) -> bool:
        """Створити жорстке посилання"""
        if name1 not in self.fs.root_directory or name2 in self.fs.root_directory:
            return False
        
        inode_num = self.fs.root_directory[name1]
        inode = self.fs.inodes[inode_num]
        
        if not inode:
            return False
        
        inode.hard_links += 1
        self.fs.root_directory[name2] = inode_num
        self.fs.save_metadata()
        return True
    
    def unlink(self, name: str) -> bool:
        """Видалити жорстке посилання"""
        if name not in self.fs.root_directory:
            return False
        
        inode_num = self.fs.root_directory[name]
        inode = self.fs.inodes[inode_num]
        
        if not inode:
            return False
        
        inode.hard_links -= 1
        del self.fs.root_directory[name]
        
        # Якщо немає посилань і файл не відкритий, видалити
        if inode.hard_links == 0:
            file_is_open = any(of.inode == inode_num for of in self.fs.open_files.values())
            if not file_is_open:
                self._delete_inode(inode_num)
        
        self.fs.save_metadata()
        return True
    
    def _delete_inode(self, inode_num: int):
        """Видалити inode та звільнити блоки"""
        inode = self.fs.inodes[inode_num]
        if not inode:
            return
        
        # Звільнити прямі блоки
        for block_num in inode.direct:
            if block_num is not None:
                self.fs._free_block(block_num)
        
        # Звільнити непрямий блок (якщо є)
        if inode.indirect is not None:
            # TODO: реалізувати звільнення непрямих блоків
            self.fs._free_block(inode.indirect)
        
        self.fs.inodes[inode_num] = None
    
    def read(self, fd: int, size: int) -> Optional[bytes]:
        """Прочитати дані з файлу"""
        if fd not in self.fs.open_files:
            return None
        
        open_file = self.fs.open_files[fd]
        inode = self.fs.inodes[open_file.inode]
        
        if not inode:
            return None
        
        if open_file.offset >= inode.size:
            return b''
        
        # Обмежити розмір читання
        actual_size = min(size, inode.size - open_file.offset)
        result = b''
        bytes_read = 0
        
        while bytes_read < actual_size:
            # Визначити блок та зсув в блоці
            block_offset = (open_file.offset + bytes_read) // self.fs.block_size
            byte_offset = (open_file.offset + bytes_read) % self.fs.block_size
            
            # Отримати номер блоку
            if block_offset < len(inode.direct):
                block_num = inode.direct[block_offset]
            else:
                # TODO: реалізувати непрямі блоки
                break
            
            if block_num is None:
                # Неініціалізований блок - нулі
                bytes_to_read = min(actual_size - bytes_read, 
                                  self.fs.block_size - byte_offset)
                result += b'\x00' * bytes_to_read
                bytes_read += bytes_to_read
            else:
                # Читати з блоку
                block_data = self.fs.device.read_block(block_num)
                bytes_to_read = min(actual_size - bytes_read,
                                  self.fs.block_size - byte_offset)
                result += block_data[byte_offset:byte_offset + bytes_to_read]
                bytes_read += bytes_to_read
        
        open_file.offset += bytes_read
        return result
    
    def write(self, fd: int, data: bytes) -> Optional[int]:
        """Записати дані у файл"""
        if fd not in self.fs.open_files:
            return None
        
        open_file = self.fs.open_files[fd]
        inode = self.fs.inodes[open_file.inode]
        
        if not inode:
            return None
        
        bytes_written = 0
        
        while bytes_written < len(data):
            # Визначити блок та зсув
            block_offset = (open_file.offset + bytes_written) // self.fs.block_size
            byte_offset = (open_file.offset + bytes_written) % self.fs.block_size
            
            # Отримати або виділити блок
            if block_offset < len(inode.direct):
                if inode.direct[block_offset] is None:
                    # Виділити новий блок
                    new_block = self.fs._allocate_block()
                    if new_block is None:
                        break  # Немає вільних блоків
                    inode.direct[block_offset] = new_block
                
                block_num = inode.direct[block_offset]
            else:
                # TODO: реалізувати непрямі блоки
                break
            
            # Записати в блок
            block_data = bytearray(self.fs.device.read_block(block_num))
            bytes_to_write = min(len(data) - bytes_written,
                               self.fs.block_size - byte_offset)
            
            block_data[byte_offset:byte_offset + bytes_to_write] = \
                data[bytes_written:bytes_written + bytes_to_write]
            
            self.fs.device.write_block(block_num, bytes(block_data))
            bytes_written += bytes_to_write
        
        open_file.offset += bytes_written
        inode.size = max(inode.size, open_file.offset)
        
        self.fs.save_metadata()
        return bytes_written
    
    def truncate(self, name: str, new_size: int) -> bool:
        """Змінити розмір файлу"""
        if name not in self.fs.root_directory:
            return False
        
        inode_num = self.fs.root_directory[name]
        inode = self.fs.inodes[inode_num]
        
        if not inode:
            return False
        
        old_size = inode.size
        
        if new_size < old_size:
            # Зменшити файл - звільнити зайві блоки
            old_blocks = (old_size + self.fs.block_size - 1) // self.fs.block_size
            new_blocks = (new_size + self.fs.block_size - 1) // self.fs.block_size
            
            # Звільнити зайві прямі блоки
            for i in range(new_blocks, min(old_blocks, len(inode.direct))):
                if inode.direct[i] is not None:
                    self.fs._free_block(inode.direct[i])
                    inode.direct[i] = None
        
        inode.size = new_size
        self.fs.save_metadata()
        return True

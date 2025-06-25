import struct
import json
from typing import Dict, List, Optional, Set
from bitarray import bitarray

from inode import Inode
from open_file import OpenFile
from block_device import BlockDevice

class FileSystem:
    """Файлова система"""
    def __init__(self, device: BlockDevice, max_inodes: int = 512):
        self.device = device
        self.max_inodes = max_inodes
        self.block_size = device.block_size
        
        # Бітова карта блоків
        self.block_bitmap = bitarray(device.total_blocks)
        self.block_bitmap.setall(0)  # всі блоки вільні
        
        # Масив inode
        self.inodes: List[Optional[Inode]] = [None] * max_inodes
        
        # Коренева директорія
        self.root_directory: Dict[str, int] = {}
        
        # Відкриті файли
        self.open_files: Dict[int, OpenFile] = {}
        self.next_fd = 0
        
        # Резерв перші блоки для метаданих
        self._reserve_metadata_blocks()
    
    def _reserve_metadata_blocks(self):
        """Резервувати блоки для метаданих"""
        # Блок 0: суперблок (метадані ФС)
        # Блок 1: бітова карта
        # Блоки 2-N: inode
        metadata_blocks = 2 + (self.max_inodes * 64) // self.block_size + 1
        for i in range(metadata_blocks):
            self.block_bitmap[i] = 1
    
    def _find_free_block(self) -> Optional[int]:
        """Знайти вільний блок"""
        try:
            return self.block_bitmap.index(0)
        except ValueError:
            return None
    
    def _allocate_block(self) -> Optional[int]:
        """Виділити блок"""
        block_num = self._find_free_block()
        if block_num is not None:
            self.block_bitmap[block_num] = 1
        return block_num
    
    def _free_block(self, block_num: int):
        """Звільнити блок"""
        if 0 <= block_num < len(self.block_bitmap):
            self.block_bitmap[block_num] = 0
    
    def _find_free_inode(self) -> Optional[int]:
        """Знайти вільний inode"""
        for i, inode in enumerate(self.inodes):
            if inode is None:
                return i
        return None
    
    def save_metadata(self):
        """Зберегти метадані на диск"""
        # Блок 0: суперблок
        superblock = {
            'magic': 'MYFS',
            'block_size': self.block_size,
            'total_blocks': self.device.total_blocks,
            'max_inodes': self.max_inodes,
            'root_directory': self.root_directory
        }
        data = json.dumps(superblock).encode('utf-8')
        self.device.write_block(0, data)
        
        # Блок 1: бітова карта
        bitmap_data = self.block_bitmap.tobytes()
        self.device.write_block(1, bitmap_data)
        
        # Блоки для inode
        inode_data = []
        for inode in self.inodes:
            if inode:
                inode_dict = {
                    'type': inode.type,
                    'hard_links': inode.hard_links,
                    'size': inode.size,
                    'direct': inode.direct,
                    'indirect': inode.indirect
                }
            else:
                inode_dict = None
            inode_data.append(inode_dict)
        
        inode_json = json.dumps(inode_data).encode('utf-8')
        block_num = 2
        while inode_json:
            chunk = inode_json[:self.block_size]
            self.device.write_block(block_num, chunk)
            inode_json = inode_json[self.block_size:]
            block_num += 1
    
    def load_metadata(self) -> bool:
        """Завантажити метадані з диска"""
        try:
            # Блок 0: суперблок
            superblock_data = self.device.read_block(0)
            superblock_str = superblock_data.rstrip(b'\x00').decode('utf-8')
            superblock = json.loads(superblock_str)
            
            if superblock['magic'] != 'MYFS':
                return False
            
            self.root_directory = superblock['root_directory']
            
            # Блок 1: бітова карта
            bitmap_data = self.device.read_block(1)
            self.block_bitmap = bitarray()
            if len(bitmap_data) > 0:
                self.block_bitmap.frombytes(bitmap_data)
                # Обрізати до потрібного розміру
                if len(self.block_bitmap) > self.device.total_blocks:
                    self.block_bitmap = self.block_bitmap[:self.device.total_blocks]
            
            # Блоки inode
            inode_data = b''
            block_num = 2
            while True:
                try:
                    chunk = self.device.read_block(block_num)
                    if chunk == b'\x00' * self.block_size:
                        break
                    inode_data += chunk
                    block_num += 1
                except:
                    break
            
            inode_str = inode_data.rstrip(b'\x00').decode('utf-8')
            inode_list = json.loads(inode_str)
            
            self.inodes = []
            for inode_dict in inode_list:
                if inode_dict:
                    inode = Inode(inode_dict['type'])
                    inode.hard_links = inode_dict['hard_links']
                    inode.size = inode_dict['size']
                    inode.direct = inode_dict['direct']
                    inode.indirect = inode_dict['indirect']
                    self.inodes.append(inode)
                else:
                    self.inodes.append(None)
            
            return True
        except:
            return False

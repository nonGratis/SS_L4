class OpenFile:
    """Дескриптор відкритого файлу"""
    def __init__(self, inode_number):
        self.inode = inode_number  # номер inode
        self.offset = 0           # позиція для читання/запису

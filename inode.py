class Inode:
    """Дескриптор файлу"""
    def __init__(self, file_type='file', direct_count=10):
        self.type = file_type            # 'file' або 'dir'
        self.hard_links = 0              # лічильник жорстких посилань
        self.size = 0                    # розмір у байтах
        self.direct = [None] * direct_count  # прямі посилання на блоки
        self.indirect = None             # номер блоку з індексами

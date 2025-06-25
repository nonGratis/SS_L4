#!/usr/bin/env python3
"""
Консольний інтерфейс для файлової системи
"""

import argparse
from block_device import BlockDevice
from filesystem import FileSystem
from vfs import VFS

class CLI:
    def __init__(self):
        self.device = None
        self.fs = None
        self.vfs = None
        
        # Словник команд для оптимізації
        self.commands = {
            'help': self.show_help,
            'mkfs': self.cmd_mkfs,
            'stat': self.cmd_stat,
            'ls': self.cmd_ls,
            'create': self.cmd_create,
            'open': self.cmd_open,
            'close': self.cmd_close,
            'seek': self.cmd_seek,
            'read': self.cmd_read,
            'write': self.cmd_write,
            'link': self.cmd_link,
            'unlink': self.cmd_unlink,
            'truncate': self.cmd_truncate,
        }
    
    def init_fs(self, filename: str = "storage.bin"):
        """Ініціалізувати файлову систему"""
        self.device = BlockDevice(filename)
        self.fs = FileSystem(self.device)
        self.vfs = VFS(self.fs)
        
        # Спробувати завантажити існуючу ФС
        if self.device.exists():
            if self.fs.load_metadata():
                print(f"Завантажено ФС з {filename}")
                return True
        
        print(f"ФС не знайдено в {filename}")
        return False
    
    def run(self):
        """Основний цикл"""
        print("Файлова система. Введіть 'help' для допомоги.")
        
        while True:
            try:
                cmd = input("> ").strip()
                if not cmd:
                    continue
                
                parts = cmd.split()
                command = parts[0].lower()
                
                if command in ('exit', 'quit'):
                    break
                
                # Використовуємо словник команд замість довгого if-elif
                if command in self.commands:
                    self.commands[command](parts)
                else:
                    print(f"Невідома команда: {command}")
                
            except KeyboardInterrupt:
                print("\nВихід...")
                break
            except Exception as e:
                print(f"Помилка: {e}")
    
    def show_help(self):
        """Показати допомогу"""
        print("""
Доступні команди:
  mkfs n           - ініціалізувати ФС з n дескрипторами
  stat name        - інформація про файл
  ls               - список файлів
  create name      - створити файл
  open name        - відкрити файл (повертає fd)
  close fd         - закрити файл
  seek fd offset   - встановити позицію
  read fd size     - прочитати дані
  write fd         - записати дані (введіть текст)
  link name1 name2 - створити жорстке посилання
  unlink name      - видалити посилання
  truncate name sz - змінити розмір файлу
  help             - ця допомога
  exit/quit        - вихід
        """)
    
    def ensure_fs(self):
        """Перевірити чи ініціалізована ФС"""
        if not self.vfs:
            print("ФС не ініціалізована. Використайте mkfs або завантажте існуючу.")
            return False
        return True
    
    def cmd_mkfs(self, parts):
        """Команда mkfs"""
        if len(parts) != 2:
            print("Використання: mkfs <кількість_дескрипторів>")
            return
        
        try:
            n = int(parts[1])
            if n <= 0:
                print("Кількість дескрипторів має бути > 0")
                return
        except ValueError:
            print("Невірний формат числа")
            return
        
        if not self.device:
            self.init_fs()
        
        if self.vfs.mkfs(n):
            print(f"ФС створено з {n} дескрипторами")
        else:
            print("Помилка створення ФС")
    
    def cmd_stat(self, parts):
        """Команда stat"""
        if not self.ensure_fs():
            return
        
        if len(parts) != 2:
            print("Використання: stat <ім'я_файла>")
            return
        
        name = parts[1]
        info = self.vfs.stat(name)
        
        if info:
            print(f"Файл: {name}")
            print(f"  Inode: {info['inode_number']}")
            print(f"  Тип: {info['type']}")
            print(f"  Жорсткі посилання: {info['hard_links']}")
            print(f"  Розмір: {info['size']} байт")
            print(f"  Блоків використано: {info['blocks_used']}")
        else:
            print(f"Файл {name} не знайдено")
    
    def cmd_ls(self):
        """Команда ls"""
        if not self.ensure_fs():
            return
        
        files = self.vfs.ls()
        if files:
            print("Файли:")
            for name, inode_num in files.items():
                print(f"  {name} -> inode {inode_num}")
        else:
            print("Директорія порожня")
    
    def cmd_create(self, parts):
        """Команда create"""
        if not self.ensure_fs():
            return
        
        if len(parts) != 2:
            print("Використання: create <ім'я_файла>")
            return
        
        name = parts[1]
        if self.vfs.create(name):
            print(f"Файл {name} створено")
        else:
            print(f"Помилка створення файла {name}")
    
    def cmd_open(self, parts):
        """Команда open"""
        if not self.ensure_fs():
            return
        
        if len(parts) != 2:
            print("Використання: open <ім'я_файла>")
            return
        
        name = parts[1]
        fd = self.vfs.open(name)
        
        if fd is not None:
            print(f"fd = {fd}")
        else:
            print(f"Помилка відкриття файла {name}")
    
    def cmd_close(self, parts):
        """Команда close"""
        if not self.ensure_fs():
            return
        
        if len(parts) != 2:
            print("Використання: close <fd>")
            return
        
        try:
            fd = int(parts[1])
        except ValueError:
            print("Невірний формат fd")
            return
        
        if self.vfs.close(fd):
            print(f"Файл fd={fd} закрито")
        else:
            print(f"Помилка закриття fd={fd}")
    
    def cmd_seek(self, parts):
        """Команда seek"""
        if not self.ensure_fs():
            return
        
        if len(parts) != 3:
            print("Використання: seek <fd> <зсув>")
            return
        
        try:
            fd = int(parts[1])
            offset = int(parts[2])
        except ValueError:
            print("Невірний формат параметрів")
            return
        
        if self.vfs.seek(fd, offset):
            print(f"Позицію fd={fd} встановлено на {offset}")
        else:
            print(f"Помилка seek для fd={fd}")
    
    def cmd_read(self, parts):
        """Команда read"""
        if not self.ensure_fs():
            return
        
        if len(parts) != 3:
            print("Використання: read <fd> <розмір>")
            return
        
        try:
            fd = int(parts[1])
            size = int(parts[2])
        except ValueError:
            print("Невірний формат параметрів")
            return
        
        data = self.vfs.read(fd, size)
        if data is not None:
            print(f"Прочитано {len(data)} байт:")
            # Показати як текст, якщо можливо
            try:
                text = data.decode('utf-8')
                print(f"'{text}'")
            except UnicodeDecodeError:
                print(f"Hex: {data.hex()}")
        else:
            print(f"Помилка читання з fd={fd}")
    
    def cmd_write(self, parts):
        """Команда write"""
        if not self.ensure_fs():
            return
        
        if len(parts) != 2:
            print("Використання: write <fd>")
            return
        
        try:
            fd = int(parts[1])
        except ValueError:
            print("Невірний формат fd")
            return
        
        print("Введіть текст для запису (Enter для завершення):")
        text = input()
        data = text.encode('utf-8')
        
        written = self.vfs.write(fd, data)
        if written is not None:
            print(f"Записано {written} байт")
        else:
            print(f"Помилка запису в fd={fd}")
    
    def cmd_link(self, parts):
        """Команда link"""
        if not self.ensure_fs():
            return
        
        if len(parts) != 3:
            print("Використання: link <ім'я1> <ім'я2>")
            return
        
        name1, name2 = parts[1], parts[2]
        if self.vfs.link(name1, name2):
            print(f"Створено посилання {name2} -> {name1}")
        else:
            print("Помилка створення посилання")
    
    def cmd_unlink(self, parts):
        """Команда unlink"""
        if not self.ensure_fs():
            return
        
        if len(parts) != 2:
            print("Використання: unlink <ім'я_файла>")
            return
        
        name = parts[1]
        if self.vfs.unlink(name):
            print(f"Посилання {name} видалено")
        else:
            print(f"Помилка видалення посилання {name}")
    
    def cmd_truncate(self, parts):
        """Команда truncate"""
        if not self.ensure_fs():
            return
        
        if len(parts) != 3:
            print("Використання: truncate <ім'я_файла> <новий_розмір>")
            return
        
        name = parts[1]
        try:
            size = int(parts[2])
        except ValueError:
            print("Невірний формат розміру")
            return
        
        if self.vfs.truncate(name, size):
            print(f"Розмір файла {name} змінено на {size}")
        else:
            print(f"Помилка зміни розміру файла {name}")

def main():
    parser = argparse.ArgumentParser(description='Файлова система - консольний інтерфейс')
    parser.add_argument('-f', '--file', default='storage.bin', 
                       help='Файл для зберігання ФС (за замовчуванням: storage.bin)')
    parser.add_argument('--mkfs', type=int, metavar='N',
                       help='Створити нову ФС з N дескрипторами та вийти')
    
    args = parser.parse_args()
    
    cli = CLI()
    
    # Ініціалізувати ФС з вказаним файлом
    cli.init_fs(args.file)
    
    # Якщо треба створити нову ФС
    if args.mkfs:
        if cli.vfs.mkfs(args.mkfs):
            print(f"ФС створено з {args.mkfs} дескрипторами в {args.file}")
        else:
            print("Помилка створення ФС")
        return
    
    # Запустити інтерактивний інтерфейс
    cli.run()

if __name__ == "__main__":
    main()

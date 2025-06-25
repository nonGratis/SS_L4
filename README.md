# 📁 Файлова система - Лабораторна робота №4

[![Tests](https://github.com/user/filesystem/actions/workflows/tests.yml/badge.svg)](https://github.com/user/filesystem/actions/workflows/tests.yml)
[![Coverage](https://codecov.io/gh/user/filesystem/branch/master/graph/badge.svg)](https://codecov.io/gh/user/filesystem)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Реалізація файлової системи на Python з підтримкою блокового носія, дескрипторів файлів та віртуальної файлової системи (VFS).

## 🚀 Особливості

- ✅ **Блоковий носій** - файл на диску з фіксованими блоками 4KB
- ✅ **Inode система** - дескриптори файлів з прямими/непрямими посиланнями  
- ✅ **Бітова карта** - ефективне управління вільними блоками
- ✅ **VFS інтерфейс** - абстракція файлової системи
- ✅ **Жорсткі посилання** - підтримка кількох імен для одного файлу
- ✅ **Консольний інтерфейс** - зручне управління через командний рядок

## 📦 Встановлення

```bash
# Клонувати репозиторій
git clone https://github.com/user/filesystem.git
cd filesystem

# Встановити залежності
pip install -r requirements.txt

# Або використати make
make install
```

## 🏃 Швидкий старт

```bash
# Запустити файлову систему
python main.py

# Або використати make
make run
```

### Приклад використання:

```bash
> mkfs 10                # Створити ФС з 10 дескрипторами
> create test.txt        # Створити файл
> open test.txt          # Відкрити файл (отримати fd)
fd = 0
> write 0                # Записати дані у файл
Введіть текст для запису:
Hello, World!
Записано 13 байт
> seek 0 0               # Встановити позицію на початок
> read 0 13              # Прочитати дані
Прочитано 13 байт:
'Hello, World!'
> stat test.txt          # Інформація про файл
Файл: test.txt
  Inode: 0
  Тип: file
  Жорсткі посилання: 1
  Розмір: 13 байт
  Блоків використано: 1
> exit
```

## 🧪 Тестування

```bash
# Запустити всі тести
make test

# Тести з покриттям коду
make test-cov

# Швидкі тести (паралельно)
make test-fast

# Перевірка якості коду
make lint

# Форматування коду
make format
```

## 📁 Структура проекту

```
src/
├── 📄 block_device.py      # Блоковий пристрій
├── 📄 filesystem.py        # Файлова система
├── 📄 inode.py            # Дескриптори файлів
├── 📄 open_file.py        # Відкриті файли  
├── 📄 vfs.py              # Віртуальна ФС
├── 📄 main.py             # Консольний інтерфейс
├── 🧪 test_filesystem.py   # Основні тести
├── 🧪 test_advanced.py     # Розширені тести
├── ⚙️ requirements.txt     # Залежності
├── ⚙️ pyproject.toml       # Конфігурація
├── ⚙️ Makefile            # Автоматизація
└── 🚀 .github/workflows/   # CI/CD
```

## 📚 API та команди

### Команди файлової системи:

| Команда | Опис | Приклад |
|---------|------|---------|
| `mkfs n` | Ініціалізувати ФС | `mkfs 100` |
| `stat name` | Інформація про файл | `stat readme.txt` |
| `ls` | Список файлів | `ls` |
| `create name` | Створити файл | `create data.bin` |
| `open name` | Відкрити файл | `open data.bin` |
| `close fd` | Закрити файл | `close 0` |
| `seek fd pos` | Позиціонування | `seek 0 100` |
| `read fd size` | Читання | `read 0 1024` |
| `write fd` | Запис | `write 0` |
| `link old new` | Жорстке посилання | `link file.txt backup.txt` |
| `unlink name` | Видалити посилання | `unlink backup.txt` |
| `truncate name size` | Змінити розмір | `truncate file.txt 500` |

### Python API:

```python
from block_device import BlockDevice
from filesystem import FileSystem  
from vfs import VFS

# Створити файлову систему
device = BlockDevice("storage.bin")
fs = FileSystem(device)
vfs = VFS(fs)

# Ініціалізувати
vfs.mkfs(100)

# Створити файл
vfs.create("example.txt")

# Відкрити та записати
fd = vfs.open("example.txt")
vfs.write(fd, b"Hello, World!")
vfs.close(fd)
```

## ⚙️ Налаштування

### Параметри файлової системи:

- **Розмір блоку:** 4096 байт (4KB)
- **Загальна кількість блоків:** 1024 (4MB)
- **Максимум дескрипторів:** Налаштовується (10-1000)
- **Прямі посилання:** 10 блоків
- **Непрямі посилання:** 1 блок (в розробці)

### Конфігурація в коді:

```python
# Створити пристрій з кастомними параметрами
device = BlockDevice(
    filename="custom.bin",
    block_size=8192,      # 8KB блоки
    total_blocks=2048     # 16MB загалом
)

# ФС з більшою кількістю дескрипторів
fs = FileSystem(device, max_inodes=500)
```

## 🧪 Результати тестування

### Статистика тестів:
- **Всього тестів:** 28 ✅
- **Покриття коду:** 89%+ 
- **Час виконання:** ~2.2 сек

### Покриття по модулях:
- `block_device.py`: 96.55%
- `filesystem.py`: 95.00%  
- `inode.py`: 100%
- `open_file.py`: 100%
- `vfs.py`: 89.41%

Детальний звіт: [TEST_RESULTS.md](TEST_RESULTS.md)

## 🚀 CI/CD

GitHub Actions автоматично:
- ✅ Запускає тести на Python 3.9-3.12
- ✅ Перевіряє якість коду (flake8, mypy)
- ✅ Форматує код (black, isort)
- ✅ Генерує звіти покриття
- ✅ Проводить бенчмарк тести

## 🔧 Розробка

```bash
# Форматування коду
make format

# Статичний аналіз
make lint

# Тести перед комітом
make pre-commit

# Очищення
make clean

# Демонстрація
make demo

# Інформація про проект
make info
```

## 📈 Продуктивність

### Бенчмарки:
- **Ініціалізація ФС:** ~0.010s
- **Створення 50 файлів:** ~0.015s  
- **100 записів по 1KB:** ~0.050s
- **100 читань по 1KB:** ~0.040s

```bash
# Запустити бенчмарки
make benchmark
```

## 🤝 Внесок у проект

1. **Fork** проект
2. Створіть **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit** зміни (`git commit -m 'Add amazing feature'`)
4. **Push** до branch (`git push origin feature/amazing-feature`)
5. Відкрийте **Pull Request**

### Правила комітів:
- Українською мовою
- Короткі та описові
- Атомарні зміни

## 📄 Ліцензія

Розповсюджується під ліцензією MIT. Дивіться [LICENSE](LICENSE) для деталей.

## 👨‍💻 Автор

**Student** - Системне програмне забезпечення  
Лабораторна робота №4 - Файлова система

## 🙏 Подяки

- Python Software Foundation
- pytest розробникам
- Викладачам курсу

---

<p align="center">
  <b>🎯 Зроблено з ❤️ для навчання системного програмування</b>
</p>

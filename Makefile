# Makefile для файлової системи

.PHONY: help install test lint format clean run coverage docs

# Кольори для виводу
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

# Python виконавець
PYTHON := python
PIP := pip

help: ## Показати допомогу
	@echo "Доступні команди:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Встановити залежності
	@echo "$(YELLOW)Встановлення залежностей...$(NC)"
	$(PIP) install -r requirements.txt

test: ## Запустити тести
	@echo "$(YELLOW)Запуск тестів...$(NC)"
	$(PYTHON) -m pytest test_filesystem.py test_advanced.py -v

test-cov: ## Запустити тести з покриттям
	@echo "$(YELLOW)Запуск тестів з аналізом покриття...$(NC)"
	$(PYTHON) -m pytest test_filesystem.py test_advanced.py -v --cov=. --cov-report=html --cov-report=term-missing

test-fast: ## Швидкі тести (паралельно)
	@echo "$(YELLOW)Швидкий запуск тестів...$(NC)"
	$(PYTHON) -m pytest test_filesystem.py test_advanced.py -v -n auto

lint: ## Перевірка якості коду
	@echo "$(YELLOW)Статичний аналіз коду...$(NC)"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
	mypy . --ignore-missing-imports

format: ## Форматування коду
	@echo "$(YELLOW)Форматування коду...$(NC)"
	black .
	isort .

format-check: ## Перевірка форматування без змін
	@echo "$(YELLOW)Перевірка форматування...$(NC)"
	black --check --diff .
	isort --check-only --diff .

clean: ## Очистити тимчасові файли
	@echo "$(YELLOW)Очищення...$(NC)"
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -f storage.bin
	rm -f *.bin
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +

run: ## Запустити програму
	@echo "$(YELLOW)Запуск файлової системи...$(NC)"
	$(PYTHON) main.py

demo: ## Демонстрація можливостей
	@echo "$(YELLOW)Демонстрація файлової системи...$(NC)"
	@echo "mkfs 10" | $(PYTHON) main.py
	@echo "$(GREEN)Створено ФС з 10 дескрипторами$(NC)"
	@echo -e "ls\ncreate demo.txt\nopen demo.txt\nwrite 0\nHello, World!\nseek 0 0\nread 0 20\nstat demo.txt\nls\nexit" | $(PYTHON) main.py

benchmark: ## Тести продуктивності
	@echo "$(YELLOW)Тести продуктивності...$(NC)"
	$(PYTHON) -c "import time; \
	from block_device import BlockDevice; \
	from filesystem import FileSystem; \
	from vfs import VFS; \
	device = BlockDevice('bench.bin', block_size=4096, total_blocks=1000); \
	fs = FileSystem(device, max_inodes=100); \
	vfs = VFS(fs); \
	start = time.time(); \
	vfs.mkfs(100); \
	print(f'Ініціалізація: {time.time()-start:.3f}s'); \
	start = time.time(); \
	[vfs.create(f'file_{i}.txt') for i in range(50)]; \
	print(f'Створення 50 файлів: {time.time()-start:.3f}s')"
	@rm -f bench.bin

coverage: ## Детальний аналіз покриття
	@echo "$(YELLOW)Аналіз покриття коду...$(NC)"
	$(PYTHON) -m pytest test_filesystem.py test_advanced.py --cov=. --cov-report=html
	@echo "$(GREEN)Звіт збережено в htmlcov/index.html$(NC)"

docs: ## Генерація документації
	@echo "$(YELLOW)Генерація документації...$(NC)"
	$(PYTHON) -c "import pydoc; pydoc.writedoc('block_device')"
	$(PYTHON) -c "import pydoc; pydoc.writedoc('filesystem')"
	$(PYTHON) -c "import pydoc; pydoc.writedoc('vfs')"
	$(PYTHON) -c "import pydoc; pydoc.writedoc('inode')"
	$(PYTHON) -c "import pydoc; pydoc.writedoc('open_file')"

pre-commit: format-check lint test ## Перевірки перед комітом
	@echo "$(GREEN)✅ Всі перевірки пройшли успішно!$(NC)"

ci: install lint test-cov ## Повний цикл CI
	@echo "$(GREEN)✅ CI пайплайн завершено успішно!$(NC)"

# Цілі для різних середовищ
dev-install: ## Встановлення для розробки
	$(PIP) install -e .
	$(PIP) install -r requirements.txt

prod-test: ## Тести для продакшену
	$(PYTHON) -m pytest test_filesystem.py test_advanced.py -v --tb=short

# Інформація про проект
info: ## Інформація про проект
	@echo "$(YELLOW)📁 Файлова система v1.0$(NC)"
	@echo "Мова: Python $(shell python --version | cut -d' ' -f2)"
	@echo "Автор: Student"
	@echo "Ліцензія: MIT"
	@echo ""
	@echo "$(GREEN)Основні файли:$(NC)"
	@ls -la *.py | head -10

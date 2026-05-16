# RPOFlip Desktop App

PDF-флипбук просмотрщик с 3D-эффектом перелистывания страниц.

## Структура проекта

```
RPOFlip/
├── run_app.py          ← Запускалка (PyWebView + Flask)
├── app.py              ← Flask backend (PyMuPDF, без Poppler)
├── index.html          ← Frontend
├── requirements.txt    ← Python зависимости
├── build.py            ← Сборщик .exe
├── RPOFlip.spec        ← PyInstaller конфиг
└── pdfs/               ← Встроенные PDF (опционально)
```

## Быстрый старт

### 1. Установка

```bash
pip install -r requirements.txt
```

### 2. Запуск

```bash
python run_app.py
```

Откроется окно приложения 1400x900.

## Сборка в .exe

```bash
pip install pyinstaller
python build.py
```

Результат: `dist/RPOFlip.exe`

## Встроенные PDF

Создайте папку `pdfs/`, положите туда `.pdf` файлы — они автоматически появятся в боковой панели.

## Горячие клавиши

- `←` / `→` — навигация
- `Esc` — закрыть просмотрщик
- Клик по странице — перелистнуть

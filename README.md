# RPOFlip Desktop App Demo
<img width="1254" height="1254" alt="06ed3575-bd7a-4219-b8ac-f84ea0c06615" src="https://github.com/user-attachments/assets/ede65f73-63f5-48eb-a043-c7e8ff6fb234" />

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

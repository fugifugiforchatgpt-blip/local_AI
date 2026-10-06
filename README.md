# 📥 Установка

## 1 Ollama (для чата)

1 Открой в браузере: https://ollama.com/download
2 Нажми «Download for Windows»
3 Скачается файл OllamaSetup.exe
4 Двойной клик по файлу → Install
5 Дождись иконки Ollama в трее (рядом с часами)
6 Открой консоль (Win + R → cmd → Enter) и проверь:

ollama --version

Если показывает версию — всё работает.

## 2 Z-Image Turbo (для картинок)

1 Открой в браузере: https://github.com/airesearch-official/Z-Image-Turbo-Windows
2 Нажми зелёную кнопку «Code» → «Download ZIP»
3 Скачается архив Z-Image-Turbo-Windows-main.zip
4 Распакуй архив в D:\ так, чтобы получилось D:\Z-Image-Turbo-Windows-main
5 Открой консоль и введи:

cd /d D:\Z-Image-Turbo-Windows-main
start_zimage.bat

Жди, пока скачаются модели (~8-10 ГБ, 10-30 минут).
Когда увидишь "Ready. Open this link: http://127.0.0.1:9000" — открой этот адрес в браузере.

## 3 Python-библиотеки

В консоли введи:

pip install ollama requests psutil pillow

## 4 Модели для Ollama

В консоли введи по очереди:

ollama pull qwen3.5:2b

ollama pull hf.co/mradermacher/DeepSeek-R1-Distill-Qwen-1.5B-Multilingual-i1-GGUF:Q4_K_M

## 5 Проверка

ollama list

Должно показать обе модели.

## 6 Запуск проекта

python Local_AI.py

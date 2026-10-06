# 📥 Установка

## Ollama (для чата)

1 Скачай: https://ollama.com/download
2 Нажми «Download for Windows»
3 Установи (двойной клик → Install)
4 Дождись иконки Ollama в трее (рядом с часами)

## Z-Image Turbo (для картинок)

1 Скачай: https://github.com/airesearch-official/Z-Image-Turbo-Windows/releases
2 Скачай Z-Image-Turbo-Windows-x64.exe
3 Установи в папку БЕЗ русских букв (например, D:\Z-Image-Turbo)
4 Запусти ярлык «Z-Image Studio»
5 Дождись автозагрузки моделей (~8-10 ГБ, 10-30 минут)
6 Когда увидишь «Ready. Open this link: http://127.0.0.1:9000» — всё готово

## Python-библиотеки

Открой консоль (Win + R → cmd → Enter) и введи:

pip install ollama requests psutil pillow

## Модели для Ollama

В консоли введи по очереди:

ollama pull qwen3.5:2b

ollama pull hf.co/mradermacher/DeepSeek-R1-Distill-Qwen-1.5B-Multilingual-i1-GGUF:Q4_K_M

## Проверка

ollama list

Должно показать обе модели.

## Запуск

python Local_AI.py

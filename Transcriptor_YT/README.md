# 🎬 YouTube Transcript Extractor

Aplicación de escritorio para extraer transcripciones de vídeos de YouTube.
Construida con Python, CustomTkinter, youtube-transcript-api y yt-dlp.

\---

## 📁 Estructura del proyecto

```
yt\_transcript\_app/
├── app.py              ← Código fuente principal
├── requirements.txt    ← Dependencias del proyecto
└── README.md           ← Esta guía
```

\---

```

## 🖥️ Cómo usar la app

|Paso|Acción|
|-|-|
|1|Pega la URL de YouTube en el campo de texto (clic derecho → Pegar)|
|2|Activa "Incluir marcas de tiempo" si las quieres en formato `\[MM:SS]`|
|3|Activa "Guardar como archivo de texto" si quieres exportar directamente a archivo|
|4|Pulsa **Obtener Transcripción**|

\---

## 🔧 Posibles problemas

|Problema|Solución|
|-|-|
|`No transcript found`|El vídeo no tiene subtítulos en español/inglés|
|`Transcripts disabled`|El autor desactivó los subtítulos|
|`ModuleNotFoundError`|Ejecuta `pip install -r requirements.txt` con el entorno activado|
|Ventana no aparece en macOS|Añade `export DISPLAY=:0` antes de ejecutar|

\---

## 📦 Dependencias

|Paquete|Uso|
|-|-|
|`customtkinter`|GUI moderna en Python|
|`youtube-transcript-api`|Extracción de subtítulos|
|`yt-dlp`|Obtención del título del vídeo|
|`pyperclip`|Portapapeles del sistema|




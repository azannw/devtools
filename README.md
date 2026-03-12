# ToolKit

A personal developer toolkit — a collection of everyday utilities wrapped in a single desktop app. Built with Python and [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter).

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Tools

| Tool | What it does |
|------|-------------|
| **Compressor** | Compress images (Pillow) and videos (ffmpeg) with adjustable quality, resolution, and format options. One-click export to open output files/folders. |
| **Images to PDF** | Combine multiple images into a single PDF. Drag to reorder, configure page size, orientation, and margins. |
| **File Converter** | Convert between document formats (DOCX, PDF, TXT, XLSX, CSV, PPTX, HTML, Markdown) and image formats (PNG, JPEG, WebP, BMP, ICO, TIFF, GIF). |
| **YouTube Downloader** | Download videos and audio from YouTube via yt-dlp. Supports playlist downloads, resolution selection, and audio-only extraction. |

## Screenshots

> _Coming soon_

## Getting Started

### Prerequisites

- **Python 3.10+**
- **ffmpeg** — required for video compression and YouTube audio extraction. Install via `winget install Gyan.FFmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html).
- **Microsoft Office** (optional) — enables higher-fidelity DOCX/PPTX/XLSX → PDF conversion through COM automation. Without it, a pure-Python fallback is used.

### Installation

```bash
# Clone the repo
git clone https://github.com/azannw/devtools.git
cd devtools

# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

## Project Structure

```
devtools/
├── main.py              # App shell — sidebar navigation, tool registration
├── requirements.txt     # Python dependencies
├── tools/
│   ├── compressor.py    # Image & Video Compressor
│   ├── img_to_pdf.py    # Images to PDF
│   ├── file_converter.py# File Converter
│   └── yt_downloader.py # YouTube Downloader
└── utils/
    └── theme.py         # Shared color palette, fonts, and widget factories
```

## Dependencies

| Package | Purpose |
|---------|---------|
| customtkinter | Modern Tkinter UI framework |
| Pillow | Image processing |
| fpdf2 | PDF generation |
| python-docx | DOCX read/write |
| openpyxl | XLSX read/write |
| python-pptx | PPTX support |
| pypdf | PDF text extraction |
| pdf2docx | PDF → DOCX conversion |
| markdown | Markdown → HTML |
| comtypes | Windows COM automation (Office) |
| yt-dlp | YouTube downloads |

## Adding a New Tool

1. Create a new file in `tools/` with a class that extends `ctk.CTkFrame`.
2. Import and register it in `main.py` inside `_register_tools()`.
3. Add a nav entry to `nav_items` in `_build_sidebar()`.

That's it — the sidebar and content switching handle the rest.

## License

MIT

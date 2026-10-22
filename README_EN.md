# Audio & File Management Assistant (AudioSepManager)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41CD52?style=flat-square&logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![ONNX Runtime](https://img.shields.io/badge/Inference-ONNX%20Runtime-005CED?style=flat-square)](https://onnxruntime.ai/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)](https://www.microsoft.com/windows/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**An all-in-one desktop audio management suite integrating AI Vocal/Instrumental Separation, Batch Transcoding & Anti-Clipping, Smart Catalog Fuzzy Matching & Renaming, and High-Efficiency File Organization.**

[English](README_EN.md) | [简体中文](README.md)

</div>

---

## 📖 Overview

Audio engineers, music library curators, video editors, and audio enthusiasts constantly face tedious, repetitive tasks: extracting backing tracks from song batches, converting audio across different formats, controlling peak volume levels to prevent digital clipping, appending standardized IDs according to master track catalogs, and cleaning chaotic filenames.

**AudioSepManager** provides a modern, ready-to-use desktop solution. Built on a clean PyQt5 interface, powered by ONNX deep learning runtime acceleration and the FFmpeg core processing engine, it simplifies complex audio workflows into a few clicks.

---

## ✨ Key Features

### 1. 🤖 AI Vocal & Instrumental Separation (MDX-Net)
- **Advanced Architecture**: Native out-of-the-box support for the **UVR-MDX-NET-Inst_HQ_3** state-of-the-art separation model.
- **Pure ONNX Runtime Inference**: No bulky PyTorch installation required; runs fast multi-threaded CPU inference with minimal resource footprint.
- **Chunked STFT / ISTFT Processing**: Custom streaming Short-Time Fourier Transform reconstruction algorithm ensuring seamless stitching without pop or click artifacts across long recordings.
- **Denoise Mode**: Optional spectral inversion subtraction algorithm to suppress residual artifacts and maximize output purity.
- **Dual-Channel Auto Downloader**: Automatically downloads missing model weights with automatic failover between official Hugging Face and high-speed mirrors.
- **Multiple Output Formats**: Export separated tracks directly as lossless WAV (16-bit PCM), FLAC, or high-bitrate MP3 (320kbps), neatly organized into dedicated `Vocals/` and `Accompaniment/` directories.

### 2. 🎚️ Batch Audio Transcoding & Anti-Clipping
- **Batch Transcoding**: Convert between WAV, MP3, and FLAC with configurable bitrates (e.g., 320k, 192k).
- **Accurate Peak Level Detection**: Integrated FFmpeg `volumedetect` analyzer provides millisecond-accurate peak volume measurements (Max Volume dBFS).
- **Automatic Volume Limiting / Normalization**: Automatically applies audio attenuation filters to files exceeding user-defined headroom thresholds (e.g., -1.5 dBFS) to prevent clipping distortion and meet platform compliance requirements.

### 3. 📊 Smart Metadata Table Matching & ID Appending
- **Master Sheet Support**: Import metadata sheets in Excel (`.xlsx`, `.xls`) or CSV formats.
- **Levenshtein Fuzzy Matching**: Powered by `thefuzz`, automatically calculates similarity between local audio file names and catalog title entries, tolerating typos, irregular spaces, and special symbols.
- **Visual Confidence Preview**: Interactive verification table displaying source filename, matched song name, mapped ID, and match score with manual correction capabilities.
- **Batch Standardized Renaming**: Append or prepend matched unique IDs with customizable formatting templates.

### 4. 🔍 Catalog Deduplication & Conflict Analysis
- Compare local audio directories against master song catalogs to locate uncataloged, duplicate, or missing audio files.
- Generates clear similarity reports to streamline audio asset management.

### 5. ⚡ File Management & Batch Renaming Suite
- **Directory Tree Explorer**: Displays folders and audio files with native system icons and multi-selection support.
- **Quick Subdirectory Dispatch**: Move or copy selected files to target subfolders via context menu shortcuts.
- **Batch Prefix / Suffix Insertion**: Quickly insert custom text before or after existing filenames.
- **Delimiter-Based Name Trimming**: Strip all characters before or after common delimiters (`_`, `-`, ` `) to clean noisy prefixes or track suffixes in seconds.

### 6. 🛡️ Windows Production Packaging & Stability
- **MSVC CRT Runtime Conflict Fix**: Includes a custom PyInstaller runtime hook (`rth_preload_crt.py`) that eliminates the `0xC0000005` access violation caused by mismatched MSVCP140 DLLs in PyQt5 and ONNX Runtime.
- **Global Crash Protection**: Built-in unhandled exception handler automatically writes stack traces to `crash.log` and alerts the user, preventing silent crashes.

---

## 🛠️ Tech Stack & Dependencies

| Component | Role |
| :--- | :--- |
| **Python 3.8+** | Core programming language |
| **PyQt5** | Desktop GUI interface and event handling |
| **ONNX Runtime** | Lightweight cross-platform CPU deep learning inference |
| **SoundFile & NumPy** | High-performance audio I/O, matrix operations, and STFT math |
| **ImageIO-FFmpeg** | Bundled FFmpeg binary backend for loudness detection and transcode |
| **Pandas & OpenPyXL** | Master catalog processing and Excel/CSV parsing |
| **TheFuzz & Levenshtein** | String edit distance and fuzzy similarity calculation |
| **Requests** | Resilient model weight download manager |
| **PyInstaller** | Single-file Windows standalone executable compilation |

---

## 🚀 Getting Started

### Prerequisites

Python 3.8 to 3.12 is recommended:

```bash
# 1. Clone this repository
git clone https://github.com/PotatoheRo666/AudioFileAssistant.git
cd AudioFileAssistant

# 2. Create and activate a virtual environment (optional but recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Launch the Application

```bash
python main.py
```

---

## 🧠 Model Setup

The application uses the **UVR-MDX-NET-Inst_HQ_3.onnx** model.

1. **Automatic Download (Recommended)**: On first launching the Vocal Separation feature, if the model file is not present, the app will offer a one-click automated download with live progress.
2. **Manual Download**: Place the `.onnx` file directly into the `models/` folder:
   - Official Hugging Face: [huggingface.co/seanghay/uvr_models](https://huggingface.co/seanghay/uvr_models/resolve/main/UVR-MDX-NET-Inst_HQ_3.onnx)
   - Fast Mirror: [hf-mirror.com/seanghay/uvr_models](https://hf-mirror.com/seanghay/uvr_models/resolve/main/UVR-MDX-NET-Inst_HQ_3.onnx)

---

## 📦 Building Standalone Windows Executable (.exe)

This project includes a tailored `main.spec` and `rth_preload_crt.py` preloader to handle CRT runtime conflicts.

To build the executable:

```bash
pip install pyinstaller
pyinstaller main.spec
```

The compiled standalone executable will be generated inside the `dist/` directory.

---

## 📂 Project Structure

```text
├── models/                     # AI model directory
│   └── UVR-MDX-NET-Inst_HQ_3.onnx  # MDX-Net separation model weights
├── main.py                     # Application entry point & PyQt5 UI logic
├── main.spec                   # PyInstaller build specification
├── rth_preload_crt.py          # MSVC CRT runtime preloading hook
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── README.md                   # Chinese documentation
└── README_EN.md                # English documentation
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

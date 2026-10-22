# 快捷音频与文件管理助手 (AudioSepManager)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41CD52?style=flat-square&logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![ONNX Runtime](https://img.shields.io/badge/Inference-ONNX%20Runtime-005CED?style=flat-square)](https://onnxruntime.ai/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)](https://www.microsoft.com/windows/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**一款集「AI 人声伴奏分离」、「批量音频转码与防削波」、「表格智能模糊匹配重命名」与「高效文件整理」于一体的桌面端多功能音频管理工具。**

[English](README_EN.md) | [简体中文](README.md)

</div>

---

## 📖 项目简介

在音频工程、音乐库整理、影视剪辑及伴奏制作过程中，我们常常面临大量繁琐重复的工作：海量音频的伴奏提取、跨格式批量转换、母带音量防削波控制、依据曲目表给文件补充统一编号/ID、文件名杂乱清洗等。

**快捷音频与文件管理助手** 提供了一站式开箱即用的解决方案。基于现代化的 PyQt5 交互界面，底层结合 ONNX 深度学习推理加速与 FFmpeg 核心音频处理引擎，让复杂的声音处理与文件管理任务变得简单高效。

---

## ✨ 核心特性

### 1. 🤖 AI 智能人声与伴奏分离 (MDX-Net)
- **先进模型架构**：内置对 **UVR-MDX-NET-Inst_HQ_3** 深度学习分离模型的原生支持。
- **纯 ONNX Runtime 高速推理**：无需安装庞大的 PyTorch 运行环境，纯 CPU 多线程并行推理，低资源占用。
- **分块 STFT/ISTFT 处理**：自主实现的短时傅里叶变换分块流式重构算法，支持超长音频无爆音拼接。
- **消噪模式 (Denoise)**：支持反向相位频谱消除算法，进一步抑制残余底噪，提升分离纯净度。
- **全自动双通道模型下载**：检测到缺失权重时，可在软件内一键高速下载，支持官方 Hugging Face 与国内镜像源自动切换。
- **多格式导出**：支持分离后直接导出无损 WAV (PCM 16-bit)、FLAC 或高品质 MP3 (320kbps)，自动归类到 `人声/` 与 `伴奏/` 目录。

### 2. 🎚️ 批量音频处理与电平防削波 (Anti-Clipping)
- **批量格式转码**：支持在 WAV、MP3、FLAC 等多种格式间批量高速转换，自由设置目标码率（如 320k）。
- **峰值电平精准检测**：调用内置 FFmpeg 音频探测分析器，毫秒级检测音频实际最大峰值（Max Volume dBFS）。
- **自动防削波增益控制**：针对大于目标阈值（如 -1.5 dBFS）的文件自动计算并附加衰减滤镜，彻底避免平台审核拒审及爆音破音问题。

### 3. 📊 数据表格智能模糊匹配与 ID 附加
- **支持导入主流表格**：轻松导入 Excel (`.xlsx`, `.xls`) 或 CSV 歌曲数据总表。
- **Levenshtein 智能模糊匹配**：基于 `thefuzz` 算法，自动比对本地音频文件名与总表曲目名称，即使存在拼写差异、空格或特殊符号亦能精确匹配。
- **可视化置信度预览**：匹配界面实时展示原文件名、推荐歌曲名、目标 ID 与相似度分数，支持手动校正。
- **一键标准化重命名**：支持将匹配到的唯一 ID 以自定义格式批量追加为前缀或后缀。

### 4. 🔍 歌曲总表查重分析
- 自动比对本地音频与母表曲目，迅速排查未入库、重名或漏传的音频文件。
- 多维度相似度分析，生成直观清晰的查重报告，避免重复资产冗余。

### 5. ⚡ 高效文件管理与批量重命名工具箱
- **现代化树形目录浏览器**：直观展示管理目录下的所有文件与子文件夹，支持系统原生图标与多选操作。
- **右键极速归档**：在右键菜单中一键将选中文件批量移动（Move）或复制（Copy）至指定子文件夹。
- **前后缀批量管理**：快速为选中的文件批量添加前缀或后缀。
- **符号定界快速裁切**：一键清除下划线 (`_`)、横杠 (`-`) 或空格 (` `) 之前或之后的所有冗余字符，极大简化杂乱文件名的清洗工作。

### 6. 🛡️ 深度定制的 Windows 打包稳定性
- **CRT 运行时冲突修复**：通过专有预加载运行时钩子 (`rth_preload_crt.py`)，彻底解决 PyQt5 与现代 MSVC 运行时库引起的 `0xC0000005` 内存冲突闪退问题。
- **全生命周期崩溃防护**：内置全局未捕获异常捕获机制，自动生成 `crash.log` 并弹出友好提示窗口，告别静默闪退。

---

## 🛠️ 技术栈与依赖

| 组件 | 作用说明 |
| :--- | :--- |
| **Python 3.8+** | 核心开发语言 |
| **PyQt5** | 桌面 GUI 框架及界面交互逻辑 |
| **ONNX Runtime** | 深度学习模型跨平台轻量级 CPU 推理引擎 |
| **SoundFile & NumPy** | 工业级音频 I/O 与高效矩阵运算、时频变换 |
| **ImageIO-FFmpeg** | 集成便携式 FFmpeg 二进制内核，提供电平分析与格式转码 |
| **Pandas & OpenPyXL** | 表格数据分析、Excel/CSV 载入与解析 |
| **TheFuzz & Levenshtein** | 字符串编辑距离与模糊相似度计算 |
| **Requests** | 模型权重文件的断点/分块下载管理器 |
| **PyInstaller** | 现代化 Windows 独立单文件 (.exe) 打包构建 |

---

## 🚀 快速上手

### 环境准备

建议使用 Python 3.8 ~ 3.12 虚拟环境：

```bash
# 1. 克隆代码仓库
git clone https://github.com/PotatoheRo666/AudioFileAssistant.git
cd AudioFileAssistant

# 2. 创建并激活虚拟环境 (可选但推荐)
python -m venv venv
# Windows 激活:
venv\Scripts\activate

# 3. 安装依赖项
pip install -r requirements.txt
```

### 启动程序

```bash
python main.py
```

---

## 🧠 AI 模型获取与配置

软件默认采用 **UVR-MDX-NET-Inst_HQ_3.onnx** 模型。

1. **自动下载（推荐）**：首次点击界面上的「批量人声/伴奏分离 (AI)」按钮时，若本地未检测到模型，软件会提示并允许你一键下载（支持自动测速切换至国内镜像源）。
2. **手动下载**：若网络受限，可手动下载后放置于项目根目录下的 `models/` 文件夹内：
   - 国内镜像下载：[hf-mirror.com/seanghay/uvr_models](https://hf-mirror.com/seanghay/uvr_models/resolve/main/UVR-MDX-NET-Inst_HQ_3.onnx)
   - 官方源下载：[huggingface.co/seanghay/uvr_models](https://huggingface.co/seanghay/uvr_models/resolve/main/UVR-MDX-NET-Inst_HQ_3.onnx)

---

## 📦 打包为独立 Windows 可执行程序 (.exe)

本项目已配置专属 `main.spec` 与 `rth_preload_crt.py`，解决了 PyQt5 打包 onnxruntime 时易发生的 CRT 动态库兼容崩溃问题。

安装 PyInstaller 后，在项目根目录下执行：

```bash
pip install pyinstaller
pyinstaller main.spec
```

编译完成后，可执行程序将生成在 `dist/` 目录下。

---

## 📂 项目结构

```text
├── models/                     # AI 模型存放目录
│   └── UVR-MDX-NET-Inst_HQ_3.onnx  # MDX-Net 伴奏人声分离权重
├── main.py                     # 主程序入口与 PyQt5 UI/业务逻辑
├── main.spec                   # PyInstaller 高级打包编译配置文件
├── rth_preload_crt.py          # 运行时动态库预加载修复钩子 (MSVC CRT)
├── requirements.txt            # Python 依赖清单
├── .gitignore                  # Git 忽略配置
├── README.md                   # 中文文档
└── README_EN.md                # 英文文档
```

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源协议发布，欢迎个人或商业场景参考使用。

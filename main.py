import sys
import os
import ctypes

# Windows PyInstaller 兼容性：预加载系统现代 C++ 运行时 (MSVC CRT)，防止与 PyQt5 旧版 MSVCP140.dll 冲突导致 0xC0000005 崩溃
if sys.platform == 'win32':
    for _dll in ['vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll']:
        try:
            _loaded = False
            if hasattr(sys, '_MEIPASS'):
                _p = os.path.join(sys._MEIPASS, _dll)
                if os.path.exists(_p):
                    ctypes.CDLL(_p)
                    _loaded = True
            if not _loaded:
                _sys_dll = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32', _dll)
                if os.path.exists(_sys_dll):
                    ctypes.CDLL(_sys_dll)
        except Exception:
            pass

    if hasattr(sys, '_MEIPASS'):
        try:
            os.add_dll_directory(sys._MEIPASS)
            _ort_capi = os.path.join(sys._MEIPASS, 'onnxruntime', 'capi')
            if os.path.exists(_ort_capi):
                os.add_dll_directory(_ort_capi)
        except Exception:
            pass

# 全局未捕获异常记录器，避免无控制台模式下闪退无提示
def _global_exception_handler(exc_type, exc_value, exc_traceback):
    import traceback
    err_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        with open("crash.log", "a", encoding="utf-8") as f:
            f.write(err_str + "\n" + "="*50 + "\n")
    except Exception:
        pass
    try:
        from PyQt5.QtWidgets import QMessageBox, QApplication
        if not QApplication.instance():
            _app = QApplication(sys.argv)
        QMessageBox.critical(None, "程序运行异常", f"发生未捕获的错误，已记录至 crash.log：\n{err_str}")
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = _global_exception_handler

try:
    import onnxruntime as ort
except ImportError:
    ort = None

try:
    import soundfile as sf
except ImportError:
    sf = None

import numpy as np
import shutil
import subprocess
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QTreeWidget, QTreeWidgetItem, QMenu, QAction, QMessageBox, 
                             QDialog, QComboBox, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QFileIconProvider,
                             QInputDialog, QSpinBox, QCheckBox, QDoubleSpinBox, QFormLayout,
                             QProgressBar, QGroupBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QFileInfo, QThread, pyqtSignal
from thefuzz import process

try:
    import imageio_ffmpeg
except ImportError:
    pass

AUDIO_EXTENSIONS = {'.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.aiff', '.ape', '.alac'}
MODEL_FILENAME = 'UVR-MDX-NET-Inst_HQ_3.onnx'
MODEL_URL_MIRROR = 'https://hf-mirror.com/seanghay/uvr_models/resolve/main/UVR-MDX-NET-Inst_HQ_3.onnx'
MODEL_URL_OFFICIAL = 'https://huggingface.co/seanghay/uvr_models/resolve/main/UVR-MDX-NET-Inst_HQ_3.onnx'

def get_mdx_model_path():
    # 1. Bundled in PyInstaller _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        p = os.path.join(sys._MEIPASS, 'models', MODEL_FILENAME)
        if os.path.exists(p):
            return p
    # 2. Executable directory
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    p = os.path.join(exe_dir, 'models', MODEL_FILENAME)
    if os.path.exists(p):
        return p
    # 3. Script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(script_dir, 'models', MODEL_FILENAME)
    if os.path.exists(p):
        return p
    # 4. User home dir .wjgl2/models
    app_p = os.path.join(os.path.expanduser('~'), '.wjgl2', 'models', MODEL_FILENAME)
    if os.path.exists(app_p):
        return app_p
    # Default target path
    return os.path.join(script_dir, 'models', MODEL_FILENAME)


STYLE_SHEET = """
QMainWindow {
    background-color: #f5f7fa;
}
QTreeWidget {
    background-color: #ffffff;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    padding: 5px;
    font-size: 14px;
    outline: 0;
}
QTreeWidget::item {
    padding: 6px;
    border-bottom: 1px solid #f2f6fc;
}
QTreeWidget::item:selected {
    background-color: #ecf5ff;
    color: #409eff;
    border-radius: 4px;
}
QTreeWidget::item:hover {
    background-color: #f5f7fa;
}
QPushButton {
    background-color: #409eff;
    color: white;
    border: none;
    padding: 10px 18px;
    border-radius: 5px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #66b1ff;
}
QPushButton:pressed {
    background-color: #3a8ee6;
}
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e4e7ed;
    gridline-color: #ebeef5;
}
QHeaderView::section {
    background-color: #f5f7fa;
    padding: 6px;
    border: 1px solid #e4e7ed;
    font-weight: bold;
    color: #606266;
}
QLabel {
    font-size: 14px;
    color: #303133;
}
QMenu {
    background-color: white;
    border: 1px solid #ebeef5;
    font-size: 14px;
    border-radius: 4px;
}
QMenu::item {
    padding: 8px 25px 8px 25px;
    color: #606266;
}
QMenu::item:selected {
    background-color: #ecf5ff;
    color: #409eff;
}
QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
    padding: 6px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    background: white;
}
QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #409eff;
}
QProgressBar {
    border: 1px solid #dcdfe6;
    border-radius: 5px;
    text-align: center;
    background-color: #f5f7fa;
    height: 22px;
    font-size: 12px;
    font-weight: bold;
    color: #303133;
}
QProgressBar::chunk {
    background-color: #409eff;
    border-radius: 4px;
}
QGroupBox {
    font-size: 13px;
    font-weight: bold;
    border: 1px solid #dcdfe6;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 14px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    color: #409eff;
}
QRadioButton {
    font-size: 13px;
    color: #606266;
    spacing: 6px;
}
"""


class ModelDownloadThread(QThread):
    progress_signal = pyqtSignal(int, int)  # downloaded_bytes, total_bytes
    finished_signal = pyqtSignal(bool, str)  # success, message

    def __init__(self, target_path, parent=None):
        super().__init__(parent)
        self.target_path = target_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        import requests
        os.makedirs(os.path.dirname(self.target_path), exist_ok=True)
        temp_path = self.target_path + ".tmp"
        urls = [MODEL_URL_MIRROR, MODEL_URL_OFFICIAL]
        success = False
        err_msg = ""
        for url in urls:
            if self._is_cancelled:
                break
            try:
                r = requests.get(url, stream=True, timeout=20)
                if r.status_code != 200:
                    continue
                total = int(r.headers.get('content-length', 0))
                downloaded = 0
                with open(temp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if self._is_cancelled:
                            break
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            self.progress_signal.emit(downloaded, total)
                if not self._is_cancelled:
                    if os.path.exists(self.target_path):
                        try:
                            os.remove(self.target_path)
                        except Exception:
                            pass
                    os.rename(temp_path, self.target_path)
                    success = True
                    break
            except Exception as e:
                err_msg = str(e)
        if os.path.exists(temp_path) and not success:
            try:
                os.remove(temp_path)
            except Exception:
                pass
        self.finished_signal.emit(success, "模型下载完成！" if success else f"模型下载失败: {err_msg}")


class VocalSeparationThread(QThread):
    file_progress = pyqtSignal(int, int, str)     # current_file (1-based), total_files, filename
    chunk_progress = pyqtSignal(int, int)         # current_chunk (1-based), total_chunks
    status_msg = pyqtSignal(str)
    file_done = pyqtSignal(str, str, str)         # filename, vocal_path, inst_path
    finished = pyqtSignal(int, list, list)        # success_count, errors, new_paths

    def __init__(self, file_paths, config, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.config = config
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    @staticmethod
    def stft_chunk(x, n_fft, hop, win):
        pad = n_fft // 2
        x_pad = np.pad(x, pad, mode='reflect')
        frames = np.lib.stride_tricks.as_strided(
            x_pad, shape=(256, n_fft), strides=(x_pad.strides[0] * hop, x_pad.strides[0])
        )
        return np.fft.rfft(frames * win, n=n_fft, axis=1).T

    @staticmethod
    def istft_chunk(D, n_fft, hop, win, chunk_size):
        frames = np.fft.irfft(D.T, n=n_fft, axis=1) * win
        pad = n_fft // 2
        full_len = chunk_size + 2 * pad
        out = np.zeros(full_len, dtype=np.float32)
        win_sum = np.zeros(full_len, dtype=np.float32)
        win_sq = win ** 2
        for i in range(256):
            s = i * hop
            out[s:s + n_fft] += frames[i]
            win_sum[s:s + n_fft] += win_sq
        nz = win_sum > 1e-7
        out[nz] /= win_sum[nz]
        return out[pad:pad + chunk_size]

    @staticmethod
    def load_audio(path):
        global sf
        if sf is not None:
            try:
                data, sr = sf.read(path, dtype='float32')
                if sr == 44100:
                    if data.ndim == 1:
                        return np.stack([data, data], axis=0)
                    else:
                        return data.T[:2]
            except Exception:
                pass
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [ffmpeg_exe, "-y", "-i", path, "-vn", "-ar", "44100", "-ac", "2", "-f", "f32le", "-"]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        raw, err = p.communicate()
        if p.returncode != 0:
            raise Exception(f"音频格式解析失败: {err.decode('utf-8', 'ignore')}")
        return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).T

    def run(self):
        global ort, sf
        if ort is None:
            self.finished.emit(0, ["缺少必要组件 (onnxruntime)，请先安装依赖。"], [])
            return

        model_path = self.config.get('model_path')
        if not model_path or not os.path.exists(model_path):
            self.finished.emit(0, ["未找到MDX-Net模型文件，请先下载模型。"], [])
            return

        self.status_msg.emit("正在初始化 AI 模型...")
        try:
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = min(os.cpu_count() or 4, 8)
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess = ort.InferenceSession(model_path, sess_options=opts, providers=['CPUExecutionProvider'])
        except Exception as e:
            self.finished.emit(0, [f"加载模型失败: {e}"], [])
            return

        n_fft = 6144
        hop = 1024
        dim_f = 3072
        dim_t = 256
        chunk_size = hop * (dim_t - 1)  # 261120
        trim = n_fft // 2               # 3072
        gen_size = chunk_size - 2 * trim  # 254976
        win = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n_fft) / n_fft)).astype(np.float32)

        out_mode = self.config.get('out_mode', 'same_dir')
        custom_out_dir = self.config.get('custom_out_dir', '')
        out_fmt = self.config.get('out_fmt', 'wav').lower()
        use_suffix = self.config.get('use_suffix', True)
        vocal_suffix = self.config.get('vocal_suffix', '_人声')
        inst_suffix = self.config.get('inst_suffix', '_伴奏')
        denoise = self.config.get('denoise', False)

        success_count = 0
        errors = []
        new_paths = []
        total_files = len(self.file_paths)

        for idx, file_path in enumerate(self.file_paths):
            if self._is_cancelled:
                break

            filename = os.path.basename(file_path)
            self.file_progress.emit(idx + 1, total_files, filename)
            self.status_msg.emit(f"正在加载音频 ({idx + 1}/{total_files}): {filename}")

            try:
                mix = self.load_audio(file_path)

                n_sample = mix.shape[1]
                pad = gen_size - (n_sample % gen_size)
                mix_p = np.concatenate((
                    np.zeros((2, trim), dtype=np.float32), 
                    mix, 
                    np.zeros((2, pad), dtype=np.float32), 
                    np.zeros((2, trim), dtype=np.float32)
                ), axis=1)

                mix_waves = []
                i = 0
                while i < n_sample + pad:
                    mix_waves.append(mix_p[:, i : i + chunk_size])
                    i += gen_size
                mix_waves = np.array(mix_waves, dtype=np.float32)
                total_chunks = len(mix_waves)

                inst_chunks = []
                for c_idx in range(total_chunks):
                    if self._is_cancelled:
                        break
                    self.chunk_progress.emit(c_idx + 1, total_chunks)
                    self.status_msg.emit(f"正在分离 ({idx + 1}/{total_files}): {filename} [分块 {c_idx + 1}/{total_chunks}]")

                    chunk = mix_waves[c_idx]
                    spek = []
                    for ch in range(2):
                        D = self.stft_chunk(chunk[ch], n_fft, hop, win)
                        spek.append(D.real[:dim_f])
                        spek.append(D.imag[:dim_f])
                    spek = np.expand_dims(np.stack(spek, axis=0), 0)

                    pred = sess.run(None, {'input': spek})[0]
                    if denoise:
                        pred_neg = sess.run(None, {'input': -spek})[0]
                        pred = (pred - pred_neg) * 0.5

                    pad_f = np.zeros((1, 4, 1, dim_t), dtype=np.float32)
                    pred_padded = np.concatenate([pred, pad_f], axis=2)
                    rec_channels = []
                    for ch in range(2):
                        D = pred_padded[0, ch * 2] + 1j * pred_padded[0, ch * 2 + 1]
                        w = self.istft_chunk(D, n_fft, hop, win, chunk_size)
                        rec_channels.append(w)
                    tar_waves = np.stack(rec_channels, axis=0)
                    inst_chunks.append(tar_waves[:, trim:-trim])

                if self._is_cancelled:
                    break

                inst = np.concatenate(inst_chunks, axis=1)[:, :n_sample]
                vocals = mix - inst

                inst = np.clip(inst, -1.0, 1.0)
                vocals = np.clip(vocals, -1.0, 1.0)

                # Output directory
                target_base = os.path.dirname(file_path) if out_mode == 'same_dir' else custom_out_dir
                vocal_dir = os.path.join(target_base, "人声")
                inst_dir = os.path.join(target_base, "伴奏")
                os.makedirs(vocal_dir, exist_ok=True)
                os.makedirs(inst_dir, exist_ok=True)

                base_name = os.path.splitext(filename)[0]
                vocal_filename = f"{base_name}{vocal_suffix}.{out_fmt}" if use_suffix else f"{base_name}.{out_fmt}"
                inst_filename = f"{base_name}{inst_suffix}.{out_fmt}" if use_suffix else f"{base_name}.{out_fmt}"

                vocal_path = os.path.join(vocal_dir, vocal_filename)
                inst_path = os.path.join(inst_dir, inst_filename)

                # Save tracks
                self.save_track(vocals, vocal_path, out_fmt)
                self.save_track(inst, inst_path, out_fmt)

                success_count += 1
                new_paths.extend([vocal_path, inst_path])
                self.file_done.emit(filename, vocal_path, inst_path)
            except Exception as e:
                errors.append(f"{filename}: {str(e)}")

        self.finished.emit(success_count, errors, new_paths)

    def save_track(self, data, path, fmt):
        import soundfile as sf
        fmt = fmt.lower()
        if fmt == 'wav':
            sf.write(path, data.T, 44100, subtype='PCM_16')
        elif fmt == 'flac':
            sf.write(path, data.T, 44100, format='FLAC')
        elif fmt == 'mp3':
            temp_wav = path + ".tmp.wav"
            try:
                sf.write(temp_wav, data.T, 44100, subtype='PCM_16')
                import imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                cmd = [ffmpeg_exe, "-y", "-i", temp_wav, "-b:a", "320k", path]
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, startupinfo=startupinfo)
            finally:
                if os.path.exists(temp_wav):
                    try:
                        os.remove(temp_wav)
                    except Exception:
                        pass
        else:
            sf.write(path, data.T, 44100)


class VocalSeparationDialog(QDialog):
    def __init__(self, file_paths, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量人声与伴奏分离 (AI 智能分离)")
        self.resize(600, 560)
        self.file_paths = file_paths
        self.worker_thread = None
        self.download_thread = None
        self.generated_paths = []
        self.last_target_dir = ""

        layout = QVBoxLayout(self)

        lbl_header = QLabel(f"已选中 {len(file_paths)} 个音频文件准备进行人声与伴奏分离。")
        lbl_header.setStyleSheet("font-weight: bold; font-size: 15px; color: #409eff;")
        layout.addWidget(lbl_header)

        # Output settings group
        grp_output = QGroupBox("输出文件夹与格式设置")
        layout_output = QVBoxLayout(grp_output)

        self.rb_same_dir = QRadioButton("在原音频所在文件夹下分别创建【人声】与【伴奏】文件夹 (推荐)")
        self.rb_same_dir.setChecked(True)
        self.rb_same_dir.toggled.connect(self.on_output_mode_changed)
        layout_output.addWidget(self.rb_same_dir)

        self.rb_custom_dir = QRadioButton("指定统一输出文件夹，并在其下创建【人声】与【伴奏】文件夹")
        layout_output.addWidget(self.rb_custom_dir)

        hbox_custom = QHBoxLayout()
        self.le_custom_dir = QLineEdit()
        self.le_custom_dir.setPlaceholderText("请选择统一输出目标文件夹...")
        self.le_custom_dir.setEnabled(False)
        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.setEnabled(False)
        self.btn_browse.clicked.connect(self.browse_custom_dir)
        hbox_custom.addWidget(self.le_custom_dir)
        hbox_custom.addWidget(self.btn_browse)
        layout_output.addLayout(hbox_custom)

        hbox_fmt = QHBoxLayout()
        hbox_fmt.addWidget(QLabel("输出格式:"))
        self.cb_format = QComboBox()
        self.cb_format.addItems(["wav (无损高品质 - 推荐)", "mp3 (320kbps 极高音质)", "flac (无损压缩)"])
        hbox_fmt.addWidget(self.cb_format)
        layout_output.addLayout(hbox_fmt)

        hbox_suffix = QHBoxLayout()
        self.cb_use_suffix = QCheckBox("文件名添加后缀区分:")
        self.cb_use_suffix.setChecked(True)
        self.cb_use_suffix.toggled.connect(lambda c: (self.le_vocal_suffix.setEnabled(c), self.le_inst_suffix.setEnabled(c)))
        hbox_suffix.addWidget(self.cb_use_suffix)

        hbox_suffix.addWidget(QLabel("人声后缀:"))
        self.le_vocal_suffix = QLineEdit("_人声")
        self.le_vocal_suffix.setMaximumWidth(90)
        hbox_suffix.addWidget(self.le_vocal_suffix)

        hbox_suffix.addWidget(QLabel("伴奏后缀:"))
        self.le_inst_suffix = QLineEdit("_伴奏")
        self.le_inst_suffix.setMaximumWidth(90)
        hbox_suffix.addWidget(self.le_inst_suffix)
        hbox_suffix.addStretch()
        layout_output.addLayout(hbox_suffix)

        layout.addWidget(grp_output)

        # AI model settings group
        grp_ai = QGroupBox("AI 分离模型与性能")
        layout_ai = QVBoxLayout(grp_ai)

        hbox_model = QHBoxLayout()
        self.lbl_model_status = QLabel("检测中...")
        hbox_model.addWidget(self.lbl_model_status)
        hbox_model.addStretch()
        self.btn_download_model = QPushButton("下载/更新模型")
        self.btn_download_model.clicked.connect(self.start_download_model)
        hbox_model.addWidget(self.btn_download_model)
        layout_ai.addLayout(hbox_model)

        self.cb_denoise = QCheckBox("启用高质量双重去噪 (Denoise) - 消除微弱杂音，推理耗时增加1倍")
        self.cb_denoise.setChecked(False)
        layout_ai.addWidget(self.cb_denoise)

        layout.addWidget(grp_ai)

        # Progress group
        grp_prog = QGroupBox("处理进度")
        layout_prog = QVBoxLayout(grp_prog)

        hbox_f_prog = QHBoxLayout()
        hbox_f_prog.addWidget(QLabel("总体进度:"))
        self.pb_total = QProgressBar()
        self.pb_total.setRange(0, len(file_paths))
        self.pb_total.setValue(0)
        hbox_f_prog.addWidget(self.pb_total)
        layout_prog.addLayout(hbox_f_prog)

        hbox_c_prog = QHBoxLayout()
        hbox_c_prog.addWidget(QLabel("当前音频:"))
        self.pb_chunk = QProgressBar()
        self.pb_chunk.setRange(0, 100)
        self.pb_chunk.setValue(0)
        hbox_c_prog.addWidget(self.pb_chunk)
        layout_prog.addLayout(hbox_c_prog)

        self.lbl_status = QLabel("状态: 准备就绪，点击【开始分离】即可开始。")
        self.lbl_status.setStyleSheet("color: #606266; font-size: 13px; margin-top: 4px;")
        layout_prog.addWidget(self.lbl_status)

        layout.addWidget(grp_prog)

        # Dialog Buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始分离")
        self.btn_start.clicked.connect(self.start_separation)
        btn_layout.addWidget(self.btn_start)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_processing)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_open_folder = QPushButton("打开输出文件夹")
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.clicked.connect(self.open_output_folder)
        btn_layout.addWidget(self.btn_open_folder)

        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

        self.check_model_status()

    def on_output_mode_changed(self):
        is_custom = self.rb_custom_dir.isChecked()
        self.le_custom_dir.setEnabled(is_custom)
        self.btn_browse.setEnabled(is_custom)

    def browse_custom_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择统一输出文件夹")
        if dir_path:
            self.le_custom_dir.setText(os.path.abspath(dir_path))

    def check_model_status(self):
        model_path = get_mdx_model_path()
        if os.path.exists(model_path):
            size_mb = os.path.getsize(model_path) / (1024 * 1024)
            self.lbl_model_status.setText(f"✓ 模型就绪: UVR-MDX-NET-Inst_HQ_3 ({size_mb:.1f} MB)")
            self.lbl_model_status.setStyleSheet("color: #67c23a; font-weight: bold;")
            self.btn_download_model.setText("重新下载模型")
            self.btn_start.setEnabled(True)
        else:
            self.lbl_model_status.setText("⚠ 未检测到模型文件 (约64MB)，请点击右侧下载")
            self.lbl_model_status.setStyleSheet("color: #e6a23c; font-weight: bold;")
            self.btn_download_model.setText("一键下载模型")
            self.btn_start.setEnabled(False)

    def start_download_model(self):
        target_path = get_mdx_model_path()
        self.btn_download_model.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.lbl_status.setText("状态: 正在高速下载模型权重文件，请稍候...")

        self.download_thread = ModelDownloadThread(target_path, self)
        self.download_thread.progress_signal.connect(self.on_download_progress)
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.start()

    def on_download_progress(self, downloaded, total):
        if total > 0:
            pct = int((downloaded / total) * 100)
            d_mb = downloaded / (1024 * 1024)
            t_mb = total / (1024 * 1024)
            self.pb_chunk.setValue(pct)
            self.lbl_status.setText(f"状态: 模型下载中... {d_mb:.1f} MB / {t_mb:.1f} MB ({pct}%)")

    def on_download_finished(self, success, msg):
        self.btn_download_model.setEnabled(True)
        self.check_model_status()
        self.pb_chunk.setValue(100 if success else 0)
        self.lbl_status.setText(f"状态: {msg}")
        if success:
            QMessageBox.information(self, "下载完成", "UVR MDX-Net 伴奏与人声分离模型已成功下载并就绪！")
        else:
            QMessageBox.warning(self, "下载失败", f"模型下载未能完成:\n{msg}\n\n请检查网络连接后重试。")

    def start_separation(self):
        model_path = get_mdx_model_path()
        if not os.path.exists(model_path):
            QMessageBox.warning(self, "提示", "模型文件尚未就绪，请先点击【一键下载模型】！")
            return

        out_mode = 'same_dir' if self.rb_same_dir.isChecked() else 'custom_dir'
        custom_out_dir = self.le_custom_dir.text().strip()
        if out_mode == 'custom_dir':
            if not custom_out_dir or not os.path.isdir(custom_out_dir):
                QMessageBox.warning(self, "提示", "请选择有效的自定义输出文件夹！")
                return
            self.last_target_dir = custom_out_dir
        else:
            if self.file_paths:
                self.last_target_dir = os.path.dirname(self.file_paths[0])

        fmt_str = self.cb_format.currentText().split()[0].lower()
        use_suffix = self.cb_use_suffix.isChecked()
        vocal_suffix = self.le_vocal_suffix.text() if use_suffix else ""
        inst_suffix = self.le_inst_suffix.text() if use_suffix else ""
        denoise = self.cb_denoise.isChecked()

        config = {
            'model_path': model_path,
            'out_mode': out_mode,
            'custom_out_dir': custom_out_dir,
            'out_fmt': fmt_str,
            'use_suffix': use_suffix,
            'vocal_suffix': vocal_suffix,
            'inst_suffix': inst_suffix,
            'denoise': denoise
        }

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_close.setEnabled(False)
        self.btn_open_folder.setEnabled(False)
        self.pb_total.setValue(0)
        self.pb_chunk.setValue(0)
        self.lbl_status.setText("状态: 正在启动分离引擎...")

        self.worker_thread = VocalSeparationThread(self.file_paths, config, self)
        self.worker_thread.file_progress.connect(self.on_file_progress)
        self.worker_thread.chunk_progress.connect(self.on_chunk_progress)
        self.worker_thread.status_msg.connect(self.lbl_status.setText)
        self.worker_thread.finished.connect(self.on_separation_finished)
        self.worker_thread.start()

    def on_file_progress(self, current_file, total_files, filename):
        self.pb_total.setValue(current_file - 1)
        self.pb_chunk.setValue(0)

    def on_chunk_progress(self, current_chunk, total_chunks):
        if total_chunks > 0:
            pct = int((current_chunk / total_chunks) * 100)
            self.pb_chunk.setValue(pct)

    def cancel_processing(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.lbl_status.setText("状态: 正在取消处理，请稍候...")
            self.worker_thread.cancel()
            self.btn_cancel.setEnabled(False)

    def on_separation_finished(self, success_count, errors, new_paths):
        self.pb_total.setValue(len(self.file_paths))
        self.pb_chunk.setValue(100)
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_close.setEnabled(True)
        self.btn_open_folder.setEnabled(True)
        self.generated_paths = new_paths

        self.lbl_status.setText(f"状态: 处理完毕！成功分离 {success_count}/{len(self.file_paths)} 个音频。")

        if self.parent() and hasattr(self.parent(), 'refresh_list'):
            self.parent().refresh_list(paths_to_select=new_paths)

        if errors:
            err_msg = "\n".join(errors[:5])
            if len(errors) > 5:
                err_msg += f"\n...等共 {len(errors)} 个错误"
            QMessageBox.warning(self, "完成，但存在部分错误", f"成功处理: {success_count} 个音频\n失败: {len(errors)} 个音频\n\n错误信息:\n{err_msg}")
        else:
            QMessageBox.information(
                self, "分离完成", 
                f"人声与伴奏分离完成！\n成功处理: {success_count}/{len(self.file_paths)} 个音频文件。\n\n"
                f"已自动创建【人声】与【伴奏】文件夹存放分离音轨。"
            )

    def open_output_folder(self):
        target = self.last_target_dir
        if not target and self.generated_paths:
            target = os.path.dirname(os.path.dirname(self.generated_paths[0]))
        if target and os.path.exists(target):
            try:
                os.startfile(target)
            except Exception as e:
                QMessageBox.warning(self, "提示", f"无法打开文件夹:\n{e}")
        else:
            QMessageBox.warning(self, "提示", "输出文件夹不存在。")


class AudioProcessDialog(QDialog):
    def __init__(self, file_paths, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量音频处理 (转码与防削波)")
        self.resize(500, 300)
        self.file_paths = file_paths
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel(f"已选中 {len(file_paths)} 个音频文件准备处理。")
        lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #409eff;")
        layout.addWidget(lbl)
        
        # Format and Bitrate
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel("目标格式:"))
        self.cb_format = QComboBox()
        self.cb_format.addItems(["wav", "mp3", "flac"])
        hbox1.addWidget(self.cb_format)
        
        hbox1.addWidget(QLabel("目标码率:"))
        self.le_bitrate = QLineEdit("320k")
        hbox1.addWidget(self.le_bitrate)
        layout.addLayout(hbox1)
        
        # dBFS setting
        lbl_dbfs = QLabel("防削波电平处理 (检测系统通常要求低于 -1dBFS):")
        lbl_dbfs.setStyleSheet("margin-top: 10px;")
        layout.addWidget(lbl_dbfs)
        
        hbox2 = QHBoxLayout()
        self.cb_dbfs = QCheckBox("启用峰值电平调整 (消除超标和削波)")
        self.cb_dbfs.setChecked(True)
        hbox2.addWidget(self.cb_dbfs)
        
        hbox2.addWidget(QLabel("目标峰值 (dBFS):"))
        self.sp_dbfs = QDoubleSpinBox()
        self.sp_dbfs.setRange(-20.0, -0.1)
        self.sp_dbfs.setSingleStep(0.1)
        self.sp_dbfs.setValue(-1.5)
        hbox2.addWidget(self.sp_dbfs)
        layout.addLayout(hbox2)
        
        self.lbl_status = QLabel("状态: 准备就绪")
        self.lbl_status.setStyleSheet("color: #909399; margin-top: 10px;")
        layout.addWidget(self.lbl_status)
        
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始处理")
        self.btn_start.clicked.connect(self.process_files)
        btn_layout.addWidget(self.btn_start)
        layout.addLayout(btn_layout)

    def process_files(self):
        try:
            import imageio_ffmpeg
            import subprocess
            import re
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            QMessageBox.warning(self, "缺少依赖", "请先在命令行运行: pip install imageio-ffmpeg")
            return
            
        fmt = self.cb_format.currentText()
        bitrate = self.le_bitrate.text()
        do_dbfs = self.cb_dbfs.isChecked()
        target_dbfs = self.sp_dbfs.value()
        
        self.btn_start.setEnabled(False)
        self.lbl_status.setText("状态: 正在处理音频，这可能需要一些时间，请稍候...")
        QApplication.processEvents()
        
        success = 0
        new_paths = []
        errors = []
        
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        for path in self.file_paths:
            try:
                volume_filter = ""
                # Adjust dBFS if requested
                if do_dbfs:
                    cmd_detect = [ffmpeg_exe, "-i", path, "-af", "volumedetect", "-f", "null", "-"]
                    res_detect = subprocess.run(cmd_detect, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore", startupinfo=startupinfo)
                    
                    match = re.search(r"max_volume:\s*([-0-9.]+)\s*dB", res_detect.stderr)
                    if match:
                        max_volume = float(match.group(1))
                        if max_volume > target_dbfs:
                            diff = target_dbfs - max_volume
                            volume_filter = f"volume={diff:.2f}dB"
                
                base_name = os.path.splitext(os.path.basename(path))[0]
                new_name = f"{base_name}_processed.{fmt}"
                new_path = os.path.join(os.path.dirname(path), new_name)
                
                cmd_convert = [ffmpeg_exe, "-y", "-i", path]
                if volume_filter:
                    cmd_convert.extend(["-af", volume_filter])
                cmd_convert.extend(["-b:a", bitrate, new_path])
                
                res_convert = subprocess.run(cmd_convert, stderr=subprocess.PIPE, stdout=subprocess.PIPE, startupinfo=startupinfo)
                if res_convert.returncode != 0:
                    raise Exception(res_convert.stderr.decode('utf-8', 'ignore'))
                    
                success += 1
                new_paths.append(new_path)
                
                self.lbl_status.setText(f"状态: 已处理 {success}/{len(self.file_paths)}")
                QApplication.processEvents()
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {str(e)}")
                
        self.btn_start.setEnabled(True)
        self.lbl_status.setText(f"状态: 处理完成！")
        
        if errors:
            err_msg = "\n".join(errors[:5])
            if len(errors) > 5:
                err_msg += f"\n...等共 {len(errors)} 个错误"
            QMessageBox.warning(self, "完成，但有错误", f"成功: {success}\n失败: {len(errors)}\n\n错误信息:\n{err_msg}")
        else:
            QMessageBox.information(self, "完成", f"音频处理完成！\n成功处理了 {success}/{len(self.file_paths)} 个文件。\n\n新文件已在原目录生成，带有 '_processed' 后缀。")
        
        if self.parent() and hasattr(self.parent(), 'refresh_list'):
            self.parent().refresh_list(paths_to_select=new_paths)
            
        self.accept()


class DuplicateConfigDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("查重分析配置")
        self.resize(450, 280)
        
        layout = QVBoxLayout(self)
        
        lbl1 = QLabel("选择总表中的 [歌曲名称] 所在列:")
        self.name_cb = QComboBox()
        self.name_cb.addItems(columns)
        layout.addWidget(lbl1)
        layout.addWidget(self.name_cb)
        
        lbl2 = QLabel("多歌名分隔符 (例如 '|' 或 ','，不填则不分割):")
        self.sep_le = QLineEdit("|")
        layout.addWidget(lbl2)
        layout.addWidget(self.sep_le)

        lbl3 = QLabel("相似度判断阈值 (0-100，建议80以上):")
        self.threshold_sp = QSpinBox()
        self.threshold_sp.setRange(1, 100)
        self.threshold_sp.setValue(80)
        layout.addWidget(lbl3)
        layout.addWidget(self.threshold_sp)
        
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("开始查重")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        layout.addLayout(btn_layout)

    def get_config(self):
        return self.name_cb.currentText(), self.sep_le.text(), self.threshold_sp.value()


class DuplicateCheckDialog(QDialog):
    def __init__(self, duplicates_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("查重结果")
        self.resize(800, 500)
        self.duplicates_data = duplicates_data  # list of dicts
        
        layout = QVBoxLayout(self)
        
        self.lbl_info = QLabel(f"共发现 {len(duplicates_data)} 个疑似重复的文件。")
        self.lbl_info.setStyleSheet("font-weight: bold; font-size: 15px; color: #e6a23c;")
        layout.addWidget(self.lbl_info)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["文件名", "文件路径", "总表中匹配的歌曲名", "匹配度"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)
        
        self.populate_table()
        
        btn_layout = QHBoxLayout()
        
        self.del_btn = QPushButton("删除选中文件")
        self.del_btn.setStyleSheet("background-color: #f56c6c; color: white;")
        self.del_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(self.del_btn)
        
        btn_layout.addStretch()
        
        self.export_btn = QPushButton("导出重复清单 (.xlsx)")
        self.export_btn.setStyleSheet("background-color: #67c23a; color: white;")
        self.export_btn.clicked.connect(self.export_excel)
        btn_layout.addWidget(self.export_btn)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.setStyleSheet("background-color: #909399; color: white;")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)

    def populate_table(self):
        self.table.setRowCount(len(self.duplicates_data))
        # Sort by match score descending
        self.duplicates_data.sort(key=lambda x: x["匹配度"], reverse=True)
        
        for row, data in enumerate(self.duplicates_data):
            self.table.setItem(row, 0, QTableWidgetItem(data["文件名"]))
            self.table.setItem(row, 1, QTableWidgetItem(data["文件路径"]))
            self.table.setItem(row, 2, QTableWidgetItem(data["匹配的歌曲名"]))
            self.table.setItem(row, 3, QTableWidgetItem(f"{data['匹配度']}%"))

    def delete_selected(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self, "提示", "请先在表格中选中要删除的行（支持按住 Ctrl 或 Shift 多选）！")
            return
            
        rows = set()
        for r in selected_ranges:
            for i in range(r.topRow(), r.bottomRow() + 1):
                rows.add(i)
                
        if not rows: return
        
        reply = QMessageBox.question(self, "危险警告", f"确定要永久删除选中的 {len(rows)} 个文件吗？\n删除后将无法恢复！", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success = 0
            failed = []
            
            # Sort descending to safely delete from bottom up
            for row in sorted(list(rows), reverse=True):
                filepath = self.table.item(row, 1).text()
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    self.table.removeRow(row)
                    del self.duplicates_data[row]
                    success += 1
                except Exception as e:
                    failed.append(filepath)
                    
            self.lbl_info.setText(f"共发现 {len(self.duplicates_data)} 个疑似重复的文件。")
            
            # Refresh main window tree
            if self.parent() and hasattr(self.parent(), 'refresh_list'):
                self.parent().refresh_list()
                
            if failed:
                QMessageBox.warning(self, "删除完成", f"成功删除 {success} 个文件。\n失败 {len(failed)} 个，文件可能正在被其他程序占用。")
            else:
                QMessageBox.information(self, "删除完成", f"已成功删除 {success} 个文件。")


    def export_excel(self):
        if not self.duplicates_data:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "保存查重结果", "重复文件清单.xlsx", "Excel Files (*.xlsx)")
        if file_path:
            try:
                df = pd.DataFrame(self.duplicates_data)
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "成功", "导出成功！")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出失败:\n{str(e)}")


class MatchDialog(QDialog):
    def __init__(self, file_paths, df, name_col, id_col, format_str, current_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("匹配确认")
        self.resize(900, 500)
        self.file_paths = file_paths  # absolute paths
        self.df = df
        self.name_col = name_col
        self.id_col = id_col
        self.format_str = format_str
        self.current_dir = current_dir

        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["原文件名", "匹配的歌曲", "匹配度", "新文件名"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("确认修改")
        self.apply_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)

        self.populate_table()

    def populate_table(self):
        self.table.setRowCount(len(self.file_paths))
        choices = self.df[self.name_col].astype(str).tolist()
        
        for row, filepath in enumerate(self.file_paths):
            filename = os.path.basename(filepath)
            file_no_ext, ext = os.path.splitext(filename)
            
            matches = process.extract(file_no_ext, choices, limit=5)
            
            self.table.setItem(row, 0, QTableWidgetItem(filename))
            
            combo = QComboBox()
            combo.addItem("-- 跳过不修改 --")
            for match_str, score, *rest in matches:
                combo.addItem(f"{match_str} (匹配度: {score}%)", userData=(match_str, score))
            
            combo.currentIndexChanged.connect(lambda idx, r=row, c=combo, orig=filename, e=ext: self.update_new_name(r, c, orig, e))
            self.table.setCellWidget(row, 1, combo)
            
            self.table.setItem(row, 2, QTableWidgetItem("-"))
            self.table.setItem(row, 3, QTableWidgetItem(filename))
            
            if matches and matches[0][1] >= 60:
                combo.setCurrentIndex(1)
            else:
                combo.setCurrentIndex(0)

    def update_new_name(self, row, combo, orig_file, ext):
        idx = combo.currentIndex()
        if idx == 0:
            self.table.setItem(row, 2, QTableWidgetItem("-"))
            self.table.setItem(row, 3, QTableWidgetItem(orig_file))
        else:
            data = combo.itemData(idx)
            if data:
                match_str, score = data
                self.table.setItem(row, 2, QTableWidgetItem(f"{score}%"))
                
                matched_row = self.df[self.df[self.name_col].astype(str) == match_str].iloc[0]
                song_id = str(matched_row[self.id_col])
                
                new_name_base = self.format_str.replace("{name}", match_str).replace("{id}", song_id)
                self.table.setItem(row, 3, QTableWidgetItem(new_name_base + ext))
                
    def get_renames(self):
        renames = []
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            if combo.currentIndex() != 0:
                filepath = self.file_paths[row]
                new_name = self.table.item(row, 3).text()
                old_name = os.path.basename(filepath)
                if old_name != new_name:
                    renames.append((filepath, new_name))
        return renames

class BatchAddPrefixSuffixDialog(QDialog):
    def __init__(self, file_paths, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量添加前缀/后缀")
        self.resize(400, 200)
        self.file_paths = file_paths
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel(f"已选中 {len(file_paths)} 个文件。")
        layout.addWidget(lbl)
        
        form = QFormLayout()
        
        self.cb_type = QComboBox()
        self.cb_type.addItems(["添加前缀", "添加后缀"])
        form.addRow("操作类型:", self.cb_type)
        
        self.le_text = QLineEdit()
        self.le_text.setPlaceholderText("输入要添加的文本")
        form.addRow("添加文本:", self.le_text)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("确定修改")
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

    def get_config(self):
        return self.cb_type.currentIndex(), self.le_text.text()

class ConfigDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置匹配参数")
        self.resize(450, 250)
        
        layout = QVBoxLayout(self)
        
        lbl1 = QLabel("选择表格中的 [歌曲名] 所在列:")
        self.name_cb = QComboBox()
        self.name_cb.addItems(columns)
        layout.addWidget(lbl1)
        layout.addWidget(self.name_cb)
        
        lbl2 = QLabel("选择表格中的 [歌曲ID] 所在列:")
        self.id_cb = QComboBox()
        self.id_cb.addItems(columns)
        layout.addWidget(lbl2)
        layout.addWidget(self.id_cb)
        
        lbl3 = QLabel("新文件名格式 (支持自定义文本和符号):")
        lbl4 = QLabel("提示: {name} 代表歌名，{id} 代表ID。例如: {id} - {name}")
        lbl4.setStyleSheet("color: #909399; font-size: 13px;")
        self.format_le = QLineEdit("{id} {name}")
        layout.addWidget(lbl3)
        layout.addWidget(lbl4)
        layout.addWidget(self.format_le)
        
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定并保存设置")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        layout.addLayout(btn_layout)

    def get_config(self):
        return self.name_cb.currentText(), self.id_cb.currentText(), self.format_le.text()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("快捷文件管理助手 - 现代化界面版")
        self.resize(950, 700)
        self.current_dir = ""
        self.icon_provider = QFileIconProvider()

        # Table data state for ID matching
        self.match_df = None
        self.match_name_col = None
        self.match_id_col = None
        self.match_format = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        top_layout = QHBoxLayout()
        self.btn_select_dir = QPushButton("选择根文件夹")
        self.btn_select_dir.clicked.connect(self.select_directory)
        self.lbl_current_dir = QLabel("当前未选择文件夹")
        self.lbl_current_dir.setStyleSheet("font-weight: bold; font-size: 15px; color: #303133;")
        top_layout.addWidget(self.btn_select_dir)
        top_layout.addWidget(self.lbl_current_dir)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        tip_lbl = QLabel("提示：展开文件夹可查看文件。右键选中文件可快速移动、复制或进行各类批量操作。")
        tip_lbl.setStyleSheet("color: #909399; font-size: 13px; margin-top: 5px;")
        main_layout.addWidget(tip_lbl)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        main_layout.addWidget(self.tree)

        bottom_layout = QHBoxLayout()
        
        self.btn_duplicate_check = QPushButton("查重分析 (导入总表)")
        self.btn_duplicate_check.setMinimumHeight(40)
        self.btn_duplicate_check.setStyleSheet("background-color: #e6a23c;")
        self.btn_duplicate_check.clicked.connect(self.duplicate_check)
        
        self.btn_import_table = QPushButton("导入表格作为数据源")
        self.btn_import_table.setMinimumHeight(40)
        self.btn_import_table.clicked.connect(self.import_table)
        
        self.lbl_table_status = QLabel("状态：未导入表格，请先导入以启用右键匹配功能")
        self.lbl_table_status.setStyleSheet("color: #909399; font-size: 13px;")
        
        bottom_layout.addWidget(self.btn_duplicate_check)
        bottom_layout.addWidget(self.btn_import_table)
        
        self.btn_vocal_sep = QPushButton("批量人声/伴奏分离 (AI)")
        self.btn_vocal_sep.setMinimumHeight(40)
        self.btn_vocal_sep.setStyleSheet("background-color: #67c23a;")
        self.btn_vocal_sep.clicked.connect(self.batch_vocal_separation)
        bottom_layout.addWidget(self.btn_vocal_sep)

        bottom_layout.addWidget(self.lbl_table_status)
        bottom_layout.addStretch()
        main_layout.addLayout(bottom_layout)

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if dir_path:
            self.current_dir = os.path.abspath(dir_path)
            self.lbl_current_dir.setText(f"当前管理: {self.current_dir}")
            self.refresh_list()

    def refresh_list(self, paths_to_select=None):
        self.tree.clear()
        if not self.current_dir: return
        
        items_to_select = []
        
        try:
            items = sorted(os.listdir(self.current_dir))
            
            # List directories first
            for item_name in items:
                item_path = os.path.join(self.current_dir, item_name)
                
                if os.path.isdir(item_path):
                    dir_node = QTreeWidgetItem(self.tree)
                    dir_node.setText(0, item_name)
                    dir_node.setIcon(0, self.icon_provider.icon(QFileInfo(item_path)))
                    dir_node.setData(0, Qt.UserRole, item_path)
                    
                    try:
                        sub_items = sorted(os.listdir(item_path))
                        for sub_item in sub_items:
                            sub_path = os.path.join(item_path, sub_item)
                            if os.path.isfile(sub_path):
                                file_node = QTreeWidgetItem(dir_node)
                                file_node.setText(0, sub_item)
                                file_node.setIcon(0, self.icon_provider.icon(QFileInfo(sub_path)))
                                file_node.setData(0, Qt.UserRole, sub_path)
                                
                                if paths_to_select and sub_path in paths_to_select:
                                    items_to_select.append(file_node)
                    except Exception:
                        pass
                    
                    dir_node.setExpanded(True)
            
            # Then list files in root directory
            for item_name in items:
                item_path = os.path.join(self.current_dir, item_name)
                if os.path.isfile(item_path):
                    file_node = QTreeWidgetItem(self.tree)
                    file_node.setText(0, item_name)
                    file_node.setIcon(0, self.icon_provider.icon(QFileInfo(item_path)))
                    file_node.setData(0, Qt.UserRole, item_path)
                    
                    if paths_to_select and item_path in paths_to_select:
                        items_to_select.append(file_node)

            # Re-select and scroll to the items that were modified
            if items_to_select:
                for item in items_to_select:
                    item.setSelected(True)
                self.tree.scrollToItem(items_to_select[0])

        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取文件夹: {str(e)}")

    def show_context_menu(self, position):
        if not self.current_dir: return
        selected_items = self.tree.selectedItems()
        if not selected_items: return

        # Only operate on actual files
        valid_files = [item for item in selected_items if os.path.isfile(item.data(0, Qt.UserRole))]
        if not valid_files:
            return

        menu = QMenu()

        if len(valid_files) == 1:
            normal_rename_action = QAction("普通重命名...", self)
            normal_rename_action.triggered.connect(lambda checked: self.normal_rename(valid_files[0]))
            menu.addAction(normal_rename_action)
            menu.addSeparator()
            
        # 1. Batch Audio Process Action
        audio_action = QAction("批量音频处理 (转码与防削波)...", self)
        audio_action.triggered.connect(lambda checked: self.open_audio_dialog(valid_files))
        menu.addAction(audio_action)

        # 1.1 Vocal Separation Action
        sep_action = QAction("批量人声与伴奏分离 (AI)...", self)
        sep_action.triggered.connect(lambda checked: self.open_vocal_separation_dialog(valid_files))
        menu.addAction(sep_action)
        menu.addSeparator()

        # 2. Add match ID action
        match_action = QAction("匹配表格添加ID...", self)
        if self.match_df is None:
            match_action.setEnabled(False)
            match_action.setText("匹配表格添加ID (需先在底部导入表格)")
        match_action.triggered.connect(lambda checked: self.open_match_dialog(valid_files))
        menu.addAction(match_action)
        menu.addSeparator()

        subfolders = [f for f in os.listdir(self.current_dir) if os.path.isdir(os.path.join(self.current_dir, f))]
        
        move_menu = QMenu("快速移动到...", self)
        copy_menu = QMenu("快速复制到...", self)

        if subfolders:
            for folder in subfolders:
                m_action = QAction(folder, self)
                m_action.triggered.connect(lambda checked, f=folder: self.action_files(valid_files, f, 'move'))
                move_menu.addAction(m_action)
                
                c_action = QAction(folder, self)
                c_action.triggered.connect(lambda checked, f=folder: self.action_files(valid_files, f, 'copy'))
                copy_menu.addAction(c_action)
        else:
            no_folder_action = QAction("当前目录下无子文件夹", self)
            no_folder_action.setEnabled(False)
            move_menu.addAction(no_folder_action)
            copy_menu.addAction(no_folder_action)
            
        menu.addMenu(move_menu)
        menu.addMenu(copy_menu)
        menu.addSeparator()

        rename_menu = QMenu("快速重命名...", self)
        
        add_ps_action = QAction("批量添加前缀/后缀...", self)
        add_ps_action.triggered.connect(lambda checked: self.open_add_prefix_suffix_dialog(valid_files))
        rename_menu.addAction(add_ps_action)
        rename_menu.addSeparator()
        
        for sep, sep_name in [("_", "下划线 (_)"), ("-", "横杠 (-)"), (" ", "空格 ( )")]:
            a_before = QAction(f"删除 {sep_name} 及之前的所有文本", self)
            a_before.triggered.connect(lambda checked, s=sep: self.strip_name(valid_files, s, 'before'))
            rename_menu.addAction(a_before)
            
            a_after = QAction(f"删除 {sep_name} 及之后的所有文本", self)
            a_after.triggered.connect(lambda checked, s=sep: self.strip_name(valid_files, s, 'after'))
            rename_menu.addAction(a_after)
            
            if sep != " ":
                rename_menu.addSeparator()
            
        menu.addMenu(rename_menu)

        menu.exec_(self.tree.viewport().mapToGlobal(position))
        
    def open_add_prefix_suffix_dialog(self, valid_files):
        files_to_process = [item.data(0, Qt.UserRole) for item in valid_files]
        if not files_to_process:
            return
            
        dlg = BatchAddPrefixSuffixDialog(files_to_process, self)
        if dlg.exec_() == QDialog.Accepted:
            op_type, add_text = dlg.get_config()
            if not add_text:
                return
                
            success_count = 0
            new_paths = []
            
            for path in files_to_process:
                dir_name = os.path.dirname(path)
                old_name = os.path.basename(path)
                name_no_ext, ext = os.path.splitext(old_name)
                
                if op_type == 0:
                    new_name = add_text + name_no_ext + ext
                else:
                    new_name = name_no_ext + add_text + ext
                    
                new_path = os.path.join(dir_name, new_name)
                
                if path != new_path and not os.path.exists(new_path):
                    try:
                        os.rename(path, new_path)
                        success_count += 1
                        new_paths.append(new_path)
                    except Exception as e:
                        print(f"Error renaming {path}: {e}")
                        new_paths.append(path)
                else:
                    new_paths.append(path)
                    
            self.refresh_list(paths_to_select=new_paths)
            if success_count > 0:
                QMessageBox.information(self, "完成", f"成功修改了 {success_count} 个文件名。")

    def open_audio_dialog(self, valid_files):
        files_to_process = [item.data(0, Qt.UserRole) for item in valid_files]
        if not files_to_process:
            return
            
        dlg = AudioProcessDialog(files_to_process, self)
        dlg.exec_()

    def batch_vocal_separation(self):
        selected_items = self.tree.selectedItems()
        valid_files = []
        if selected_items:
            valid_files = [item.data(0, Qt.UserRole) for item in selected_items 
                           if os.path.isfile(item.data(0, Qt.UserRole)) and 
                           os.path.splitext(item.data(0, Qt.UserRole))[1].lower() in AUDIO_EXTENSIONS]
        if not valid_files:
            start_dir = self.current_dir if self.current_dir else ""
            files, _ = QFileDialog.getOpenFileNames(
                self, "选择要分离人声与伴奏的音频文件", start_dir, 
                "音频文件 (*.wav *.mp3 *.flac *.m4a *.aac *.ogg *.wma *.ape *.alac);;所有文件 (*.*)"
            )
            if not files:
                return
            valid_files = files

        dlg = VocalSeparationDialog(valid_files, self)
        dlg.exec_()

    def open_vocal_separation_dialog(self, valid_items):
        files = [item.data(0, Qt.UserRole) for item in valid_items]
        audio_files = [f for f in files if os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS]
        if not audio_files:
            QMessageBox.warning(self, "提示", "所选文件中没有检测到支持的音频文件（支持 .wav, .mp3, .flac, .m4a 等）。")
            return
        dlg = VocalSeparationDialog(audio_files, self)
        dlg.exec_()

    def duplicate_check(self):
        if not self.current_dir:
            QMessageBox.warning(self, "提示", "请先在顶部选择需要管理的文件夹！")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(self, "选择总表文件", "", "表格文件 (*.xlsx *.xls *.csv)")
        if not file_path: return

        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取表格失败:\n{str(e)}")
            return

        cols = [str(c) for c in df.columns.tolist()]
        if not cols:
            QMessageBox.warning(self, "错误", "表格为空或无法解析列名。")
            return
            
        config_dlg = DuplicateConfigDialog(cols, self)
        if config_dlg.exec_() == QDialog.Accepted:
            name_col, sep, threshold = config_dlg.get_config()
            
            # Extract known songs
            known_songs = set()
            for idx, row in df.iterrows():
                val = str(row[name_col])
                if pd.isna(val) or val == 'nan' or not val.strip(): continue
                if sep:
                    parts = [p.strip() for p in val.split(sep) if p.strip()]
                    for p in parts:
                        known_songs.add(p)
                else:
                    known_songs.add(val.strip())
            
            known_songs = list(known_songs)
            if not known_songs:
                QMessageBox.warning(self, "提示", "总表中未提取到任何有效的歌曲名称！")
                return

            # Gather all files in the tree
            files_to_check = []
            for i in range(self.tree.topLevelItemCount()):
                node = self.tree.topLevelItem(i)
                path = node.data(0, Qt.UserRole)
                if os.path.isfile(path):
                    files_to_check.append(path)
                else:
                    for j in range(node.childCount()):
                        child = node.child(j)
                        child_path = child.data(0, Qt.UserRole)
                        if os.path.isfile(child_path):
                            files_to_check.append(child_path)

            if not files_to_check:
                QMessageBox.warning(self, "提示", "当前文件夹下没有找到任何文件。")
                return

            # Perform fuzzy matching
            duplicates_data = []
            for filepath in files_to_check:
                filename = os.path.basename(filepath)
                file_no_ext, _ = os.path.splitext(filename)
                
                best_match = process.extractOne(file_no_ext, known_songs)
                if best_match and best_match[1] >= threshold:
                    duplicates_data.append({
                        "文件名": filename,
                        "文件路径": filepath,
                        "匹配的歌曲名": best_match[0],
                        "匹配度": best_match[1]
                    })
                    
            if duplicates_data:
                res_dlg = DuplicateCheckDialog(duplicates_data, self)
                res_dlg.exec_()
            else:
                QMessageBox.information(self, "查重结果", f"未发现重复文件。\n\n当前设置的匹配度阈值为 {threshold}，没有文件的相似度达到此要求。")


    def import_table(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择表格文件", "", "表格文件 (*.xlsx *.xls *.csv)")
        if not file_path: return

        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取表格失败:\n{str(e)}")
            return

        cols = [str(c) for c in df.columns.tolist()]
        if not cols:
            QMessageBox.warning(self, "错误", "表格为空或无法解析列名。")
            return
            
        config_dlg = ConfigDialog(cols, self)
        if config_dlg.exec_() == QDialog.Accepted:
            self.match_name_col, self.match_id_col, self.match_format = config_dlg.get_config()
            self.match_df = df
            self.lbl_table_status.setText(f"状态：已成功导入表格 ({len(df)} 条数据)。请右键选中文件以匹配。")
            self.lbl_table_status.setStyleSheet("color: #67c23a; font-weight: bold; font-size: 13px;")

    def open_match_dialog(self, valid_files):
        if self.match_df is None:
            return
            
        files_to_match = [item.data(0, Qt.UserRole) for item in valid_files]
        if not files_to_match:
            return
            
        match_dlg = MatchDialog(files_to_match, self.match_df, self.match_name_col, self.match_id_col, self.match_format, self.current_dir, self)
        if match_dlg.exec_() == QDialog.Accepted:
            renames = match_dlg.get_renames()
            if not renames:
                return
            
            new_paths = []
            success_count = 0
            for filepath, new_name in renames:
                dst = os.path.join(os.path.dirname(filepath), new_name)
                
                if filepath != dst and not os.path.exists(dst):
                    try:
                        os.rename(filepath, dst)
                        success_count += 1
                        new_paths.append(dst)
                    except Exception as e:
                        QMessageBox.warning(self, "错误", f"重命名 {os.path.basename(filepath)} 失败:\n{str(e)}")
                        new_paths.append(filepath)
                else:
                    new_paths.append(filepath)
                        
            self.refresh_list(paths_to_select=new_paths)
            QMessageBox.information(self, "完成", f"成功重命名 {success_count} 个文件。")

    def normal_rename(self, item):
        src = item.data(0, Qt.UserRole)
        old_name = os.path.basename(src)
        name_no_ext, ext = os.path.splitext(old_name)
        
        new_name_base, ok = QInputDialog.getText(self, "普通重命名", "请输入新的文件名（不含扩展名）:", QLineEdit.Normal, name_no_ext)
        if ok and new_name_base and new_name_base.strip():
            new_name = new_name_base.strip() + ext
            dst = os.path.join(os.path.dirname(src), new_name)
            
            if src != dst:
                if os.path.exists(dst):
                    QMessageBox.warning(self, "错误", "目标文件名已存在！")
                    return
                try:
                    os.rename(src, dst)
                    self.refresh_list(paths_to_select=[dst])
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"重命名失败:\n{str(e)}")

    def action_files(self, items, target_folder, action_type):
        target_path = os.path.join(self.current_dir, target_folder)
        success_count = 0
        new_paths = []
        for item in items:
            src = item.data(0, Qt.UserRole)
            filename = os.path.basename(src)
            dst = os.path.join(target_path, filename)
            
            if src == dst:
                new_paths.append(src)
                continue
                
            try:
                if action_type == 'copy':
                    shutil.copy2(src, dst)
                    new_paths.append(dst)
                elif action_type == 'move':
                    shutil.move(src, dst)
                    new_paths.append(dst)
                success_count += 1
            except Exception as e:
                QMessageBox.warning(self, "错误", f"操作文件 {filename} 失败:\n{str(e)}")
                new_paths.append(src)
        
        self.refresh_list(paths_to_select=new_paths)

    def strip_name(self, items, sep, direction):
        success_count = 0
        new_paths = []
        for item in items:
            src = item.data(0, Qt.UserRole)
            old_name = os.path.basename(src)
            name_no_ext, ext = os.path.splitext(old_name)
            
            if sep in name_no_ext:
                if direction == 'before':
                    new_name_base = name_no_ext.split(sep, 1)[1]
                else:
                    new_name_base = name_no_ext.rsplit(sep, 1)[0]
                
                if not new_name_base.strip():
                    new_paths.append(src)
                    continue

                new_name = new_name_base + ext
                dst = os.path.join(os.path.dirname(src), new_name)
                
                if src != dst and not os.path.exists(dst):
                    try:
                        os.rename(src, dst)
                        success_count += 1
                        new_paths.append(dst)
                    except Exception as e:
                        QMessageBox.warning(self, "错误", f"重命名 {old_name} 失败:\n{str(e)}")
                        new_paths.append(src)
                else:
                    new_paths.append(src)
            else:
                new_paths.append(src)
                
        self.refresh_list(paths_to_select=new_paths)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_SHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

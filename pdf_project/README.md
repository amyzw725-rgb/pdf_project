# Invoice PDF Helper（PDF 发票 → Excel）

本地运行的 **Streamlit** 小工具：上传发票 PDF，批量解析字段，导出 **Excel**；数据与处理均在当前电脑完成，不依赖云端推理。

**适合作为 GitHub 仓库简介的一句话：**

> Windows 桌面端发票 PDF 批量解析工具：Streamlit 界面 + pdfplumber / Tesseract OCR + Poppler，导出 Excel；支持一键启动与依赖自检。

---

## 功能概览

- 浏览器内 **上传多个 PDF**，一键 **Run** 批量处理  
- **规则 + OCR** 管线：先文本抽取，文本过少时 Poppler 转图 + Tesseract（含中英文语言包配置）  
- 输出 **`.xlsx`**，主页面 **快捷打开** `input`、`output`、`archive` 文件夹（Windows 资源管理器）  
- 可选的 **耗时 / “时间返还”** 等本地统计（JSON 存于项目目录，不上传）  
- **Klero.vbs** / **run_app.bat**：Windows 下一键启动；启动前 **自动检查并 pip 安装** 缺失的 Python 依赖（可关闭，见下文）

---

## 技术栈

| 用途 | 依赖 |
|------|------|
| Web UI | Streamlit |
| PDF 文本 | pdfplumber |
| 表格与导出 | pandas、openpyxl |
| 扫描件 OCR | pytesseract、pdf2image、Pillow、OpenCV、NumPy |
| PDF 转图 | Poppler（`pdfinfo` / `pdftoppm` 等） |

Python 版本建议 **3.10+**（与当前 `py` / `python` 环境一致即可）。

---

## 仓库结构（核心文件）

| 路径 | 说明 |
|------|------|
| `streamlit_app.py` | 前端页面与交互 |
| `process_pdfs.py` | 批处理入口、路径配置、解析与写 Excel |
| `poppler_setup.py` | Poppler 路径解析；缺失时可自动下载 Windows 发行包到项目内 |
| `check_imports.py` | 导入检查；支持 `--install` 安装 `requirements.txt` |
| `requirements.txt` | Python 依赖列表 |
| `run_app.bat` | 启动：依赖检查 → Streamlit（`--server.headless=false`） |
| `install_deps.bat` | 仅执行 `pip install -r requirements.txt` |
| `Klero.vbs` | 双击打开发起 `run_app.bat`（工作目录为脚本所在文件夹） |
| `.streamlit/config.toml` | 本地端口、非 headless 等 Streamlit 配置 |
| `build_release.ps1` | 打包 Windows 分发 ZIP（见下文「下载安装包」） |
| `安装说明.txt` | 随 ZIP 分发给最终用户的安装步骤（中文） |
| `installer/` | 可选：Inno Setup 脚本生成 `setup.exe`（见 `installer/README.md`）；**不是**自带 Python 的单文件 exe |
| `release/v1.0/README.md` | **1.0 版 GitHub 发布说明**（可上传目录的生成方式与常见误解澄清） |
| `scripts/export_github_v1.ps1` | 在**桌面**生成 **`InvoicePDFHelper-v1.0-GitHub`**，并删除项目内旧的 `release\v1.0\github-ready`（若存在） |

其他目录（如 `PDF Processor/`、`Old File/`、`Tesseract-OCR/`）多为历史脚本或本地工具链；**日常运行以仓库根目录上述文件为准**。**不要**将含真实发票的 `input` / `output` 提交到公开仓库。

---

## 下载安装包（给最终用户）

本应用是 **Python + Streamlit**，不提供内置 Python 的单一 `.exe` 安装器；标准做法是分发 **ZIP 安装包**（源码 + 批处理 + 说明），用户在 Windows 上安装 [Python](https://www.python.org/downloads/windows/) 后解压使用。

### 维护者如何生成 ZIP

在仓库根目录执行：

```powershell
pwsh -File .\build_release.ps1
pwsh -File .\build_release.ps1 -Version "1.0.0"
```

产物：`dist\InvoicePDFHelper-Windows-<版本>.zip`（内含 `安装说明.txt`）。

### 在 GitHub 上提供下载

1. **GitHub Actions**：推送后打开 **Actions → “Build Windows package (ZIP)”**  
   - **Run workflow** 手动运行：在 Artifacts 中下载 ZIP。  
   - 推送 **`v*` 标签**（例如 `v1.0.0`）：同一工作流会把 ZIP **附加到该标签的 Release**（自动生成 Release 说明）。
2. **Releases 页面**：用户到 **Releases** 下载 `InvoicePDFHelper-Windows-*.zip` 即可。

### 可选：Inno Setup 的 setup.exe（≠ 自带 Python 的 exe）

若需要 Windows 安装向导，可在本机安装 [Inno Setup](https://jrsoftware.org/isinfo.php)，先执行上面的 `build_release.ps1`，再按 **`installer/README.md`** 编译 `InvoicePDFHelper.iss`。  
安装程序只负责解压文件与快捷方式，**用户电脑仍需单独安装 Python**；与「下载一个 exe 即内含运行时」不是同一形态。

---

## GitHub 1.0 干净上传目录

要把 **v1.0 源码树** 单独作为新仓库推送（不含个人票据、不含 Tesseract / Poppler 大目录）：

```powershell
pwsh -File .\scripts\export_github_v1.ps1
```

生成：**桌面上的文件夹 `InvoicePDFHelper-v1.0-GitHub`**（用法与自检见 **`release/v1.0/README.md`**）。若项目里曾有过 `release\v1.0\github-ready`，会被自动删除以免重复。

---

## 快速开始（Windows）

1. 克隆或解压本仓库到任意路径（**勿依赖**旧机器上的 `C:\Users\...\Desktop\...` 硬编码）。  
2. 双击 **`run_app.bat`** 或 **`Klero.vbs`**（首次会尝试 `pip install` 缺失包，需联网）。  
3. 浏览器打开 **`http://localhost:8501`**（若未自动弹出）。  
4. 上传 PDF → **Run** → 下载生成的 Excel；中间文件默认在同级 **`input` / `output` / `archive`**。

手动安装依赖：

```bash
py -m pip install -r requirements.txt
py -m streamlit run streamlit_app.py
```

---

## 路径与环境变量

项目根目录 = **`process_pdfs.py` 所在目录**。默认数据目录：

- `input/`、`output/`、`archive/`

可选环境变量（覆盖默认或工具位置）：

| 变量 | 含义 |
|------|------|
| `TESSERACT_CMD` | `tesseract.exe` 绝对路径 |
| `POPPLER_PATH` | Poppler **bin** 目录（需含 `pdfinfo.exe`） |
| `INVOICE_AUTO_INSTALL_POPPLER` | 设为 `0` / `false` 关闭自动下载 Poppler |
| `INVOICE_INPUT_DIR` / `INVOICE_OUTPUT_DIR` / `INVOICE_ARCHIVE_DIR` | 自定义输入、输出、归档目录 |

**Tesseract**：优先项目内 `Tesseract-OCR/tesseract.exe`，否则常见安装路径 `C:\Program Files\Tesseract-OCR\tesseract.exe`。

**Poppler**：优先已有 `POPPLER_PATH` 或项目内 `poppler/`，否则可自动下载（见 `poppler_setup.py`）；也可自行安装并设置 `POPPLER_PATH`。

---

## 上传到 GitHub 时的建议

- **不要**把体积巨大的二进制目录（完整 `Tesseract-OCR/`、自动下载的 `poppler/`、`.cache/`）提交进仓库，除非你有意用 Git LFS；本仓库 `.gitignore` 已包含 `poppler/` 与 `.cache/`。  
- 提交 **`requirements.txt`**、**`README.md`**、**源码**；协作者本地再安装 Tesseract / Poppler 或使用脚本自动拉取 Poppler。  
- 勿将含隐私的 **真实发票 PDF**、**含密钥的 `.env`** 推送到公开仓库。

---

## 许可证

未随仓库指定默认许可证；若开源请在仓库根目录添加 `LICENSE` 并在此 README 中注明。

---

## 致谢

- [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows)（自动安装脚本使用的预编译包来源之一）  
- [Streamlit](https://streamlit.io/)、[pdfplumber](https://github.com/jsvine/pdfplumber)、[Tesseract](https://github.com/tesseract-ocr/tesseract)

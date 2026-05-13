"""
Resolve Poppler bin directory for pdf2image on Windows.

Search order:
  1. POPPLER_PATH env (if pdfinfo.exe exists there)
  2. <project>/poppler/.../pdfinfo.exe (bundled / previous install)
  3. pdfinfo.exe on PATH
  4. C:\\poppler\\Library\\bin
  5. Auto-download Release zip from oschwartz10612/poppler-windows into <project>/poppler/

Disable auto-download: set INVOICE_AUTO_INSTALL_POPPLER=0
"""

from __future__ import annotations

import logging
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

VERSION_TAG = "v24.08.0-0"
ZIP_NAME = "Release-24.08.0-0.zip"
DOWNLOAD_URL = (
    f"https://github.com/oschwartz10612/poppler-windows/releases/download/"
    f"{VERSION_TAG}/{ZIP_NAME}"
)
USER_AGENT = "pdf_project-poppler-setup/1.0"


def _auto_install_enabled() -> bool:
    v = (os.environ.get("INVOICE_AUTO_INSTALL_POPPLER") or "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def _pdfinfo_exists(bin_dir: Path) -> bool:
    return bin_dir.is_dir() and (bin_dir / "pdfinfo.exe").is_file()


def _find_poppler_bin_under(root: Path) -> Optional[Path]:
    """Return the directory containing pdfinfo.exe (normally .../Library/bin)."""
    if not root.is_dir():
        return None
    for pdfinfo in root.rglob("pdfinfo.exe"):
        if pdfinfo.is_file():
            return pdfinfo.parent.resolve()
    return None


def _candidate_dirs(project_root: Path) -> list[Path]:
    out: list[Path] = []
    env = (os.environ.get("POPPLER_PATH") or "").strip()
    if env:
        out.append(Path(env))
    out.append(project_root / "poppler" / "Library" / "bin")
    out.append(project_root / "poppler" / "bin")
    which = shutil.which("pdfinfo")
    if which:
        out.append(Path(which).resolve().parent)
    out.append(Path(r"C:\poppler\Library\bin"))
    return out


def _pick_existing_bin(project_root: Path) -> Optional[Path]:
    for c in _candidate_dirs(project_root):
        try:
            if _pdfinfo_exists(c):
                return c.resolve()
        except OSError:
            continue
    bundled = _find_poppler_bin_under(project_root / "poppler")
    if bundled is not None and _pdfinfo_exists(bundled):
        return bundled
    return None


def _download_zip(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
    dest.write_bytes(data)


def _install_poppler_windows(project_root: Path) -> Path:
    """Download official Windows Poppler bundle into project_root/poppler."""
    cache_dir = project_root / ".cache"
    zip_path = cache_dir / ZIP_NAME
    install_root = project_root / "poppler"

    logging.info("Poppler 未找到，正在下载 Windows 发行包（约 15MB）…")
    logging.info("URL: %s", DOWNLOAD_URL)
    try:
        _download_zip(DOWNLOAD_URL, zip_path)
    except Exception as e:
        logging.error("Poppler 下载失败: %s", e)
        raise

    if install_root.exists():
        shutil.rmtree(install_root, ignore_errors=True)
    install_root.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(install_root)
    except zipfile.BadZipFile as e:
        logging.error("Poppler zip 损坏，将删除缓存后重试: %s", e)
        try:
            zip_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    bin_dir = _find_poppler_bin_under(install_root)
    if bin_dir is None or not _pdfinfo_exists(bin_dir):
        raise RuntimeError(
            f"解压后未找到 pdfinfo.exe，请检查发行包结构或手动设置 POPPLER_PATH。"
        )

    logging.info("Poppler 已安装到: %s", bin_dir)
    return bin_dir


def resolve_poppler_bin(project_root: Path) -> str:
    """
    Return absolute path to Poppler *bin* directory (containing pdfinfo.exe).
    """
    found = _pick_existing_bin(project_root)
    if found is not None:
        logging.info("使用 Poppler: %s", found)
        return str(found)

    if not _auto_install_enabled():
        logging.warning(
            "未检测到 Poppler，且 INVOICE_AUTO_INSTALL_POPPLER 已关闭；"
            "将回退到 C:\\poppler\\Library\\bin（可能仍不可用）。"
        )
        return r"C:\poppler\Library\bin"

    try:
        bin_dir = _install_poppler_windows(project_root)
        logging.info("使用 Poppler: %s", bin_dir)
        return str(bin_dir)
    except Exception:
        logging.warning(
            "Poppler 自动安装失败，回退到 C:\\poppler\\Library\\bin。"
            "请手动安装 Poppler 或设置环境变量 POPPLER_PATH 指向含 pdfinfo.exe 的 bin 目录。"
        )
        return r"C:\poppler\Library\bin"

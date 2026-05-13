# v1.0 — 可上传 GitHub 的源码快照（桌面版）

## 先澄清两件事（避免理解偏差）

1. **个人票据**  
   导出目录**不包含**真实 PDF、Excel；只带空的 `input`、`output`、`archive` 和 `.gitkeep`。

2. **「一键 exe」**  
   当前**没有**自带 Python 的单文件 exe；有 **ZIP** 与可选 Inno **setup.exe**（仍要本机装 Python）。详见主 `README.md`。

---

## 生成位置（重要）

在**开发仓库根目录**执行：

```powershell
pwsh -File .\scripts\export_github_v1.ps1
```

会在**当前用户桌面**新建（或覆盖）文件夹：

**`桌面\InvoicePDFHelper-v1.0-GitHub\`**

该文件夹内容即可作为 **新 Git 仓库根目录** 上传 GitHub。

脚本会**删除**开发仓库里旧的重复目录（若仍存在）：

**`<项目>\release\v1.0\github-ready\`**

避免项目内与桌面各有一份拷贝。

---

## 生成后建议自检

- [ ] 桌面文件夹内**没有** `.pdf` / `.xlsx` 业务文件  
- [ ] **没有** `Tesseract-OCR/`、`poppler/`、`.cache/`  
- [ ] `README.md`、`安装说明.txt`、`VERSION.txt` 齐全  
- [ ] 在桌面该文件夹内 `py -m pip install -r requirements.txt` 与 `streamlit run streamlit_app.py` 能跑通  

---

## 与 `dist/*.zip` 的区别

| 产物 | 用途 |
|------|------|
| **桌面** `InvoicePDFHelper-v1.0-GitHub\` | **Git 仓库根**：`git init` 后 push。 |
| `dist\InvoicePDFHelper-Windows-*.zip` | **最终用户 ZIP**：`build_release.ps1` 生成。 |

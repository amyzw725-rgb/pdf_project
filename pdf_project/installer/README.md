# Windows 安装包（可选）

## 方式 A：ZIP（推荐，与 CI 一致）

在仓库根目录执行：

```powershell
pwsh -File .\build_release.ps1
pwsh -File .\build_release.ps1 -Version "1.0.0"
```

生成：`dist\InvoicePDFHelper-Windows-<版本>.zip`  
用户解压后按 `安装说明.txt` 安装 Python、运行 `install_deps.bat` 或 `run_app.bat` 即可。

GitHub 上：打标签 `v1.0.0` 并推送，或手动运行 **Actions → Build Windows package**，在 Artifacts 里下载 ZIP；推送 `v*` 标签时工作流会把 ZIP 挂到 **Releases** 资源上。

## 方式 B：Inno Setup 生成 setup.exe

1. 安装 [Inno Setup 6](https://jrsoftware.org/isdl.php)。
2. 先执行 **方式 A** 生成 `dist\InvoicePDFHelper_package\`。
3. 用 Inno Compiler 打开本目录下的 `InvoicePDFHelper.iss` 并编译。  
4. 安装程序输出在 `installer\Output\`。

安装程序会把文件解压到 `%LOCALAPPDATA%\InvoicePDFHelper` 并创建开始菜单 / 桌面快捷方式（仍依赖用户本机已安装 Python）。

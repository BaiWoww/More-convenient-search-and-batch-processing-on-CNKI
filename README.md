# CNKI 论文检索助手

CNKI 论文检索助手是一个基于 Python、PySide6 和 Playwright 的桌面应用，用于辅助检索 CNKI 文献、获取论文详情、下载可用文档，并导出论文列表、摘要与参考文献。

## 功能特性

- 图形化检索界面，支持主题、篇名、关键词、摘要、作者、单位、刊名和 DOI 等字段。
- 支持学术期刊、硕士论文、博士论文、会议论文、报纸、年鉴、专利、标准等数据库类型。
- 使用 Playwright 管理浏览器会话，便于处理登录状态、验证码和下载流程。
- 支持获取论文详情信息，包括作者、机构、摘要、关键词、DOI、基金、被引与下载信息。
- 支持批量下载可访问的 PDF/CAJ 文件。
- 支持导出 TXT、XLSX、DOCX 格式的论文列表、摘要和 GB/T 7714-2025 参考文献。
- 支持通过 PyInstaller 打包为 Windows 桌面程序。

## 项目结构

```text
cnki-desktop/
├── cnki_desktop/          # PySide6 桌面界面与工作线程
├── core/                  # CNKI 检索、解析、下载、导出和引文格式化核心逻辑
├── main.py                # 应用入口
├── requirements.txt       # 运行与打包依赖
├── build.bat              # Windows 一键构建脚本
└── build.spec             # PyInstaller 打包配置
```

## 环境要求

- Python 3.10 或更高版本
- Windows 10/11
- Microsoft Edge 或 Playwright Chromium 浏览器
- 可访问 CNKI 的网络环境与相应权限

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-name/cnki-desktop.git
cd cnki-desktop
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. 安装依赖

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

### 4. 启动应用

```bash
python main.py
```

首次启动后，应用会打开浏览器并建立 CNKI 会话。如遇验证码或登录要求，请按页面提示手动完成。

## 打包发布

Windows 环境下可以直接运行：

```bash
build.bat
```

构建完成后，可执行文件位于：

```text
dist\CNKI_Desktop\CNKI_Desktop.exe
```

## 使用说明

1. 启动应用后等待浏览器状态变为已连接。
2. 选择检索字段、数据库类型并输入关键词。
3. 执行搜索后，在结果表格中选择需要处理的论文。
4. 按需获取详情、下载文档或导出结果。
5. 导出的文件默认由用户在界面中选择保存位置。

## 合规说明

- 本项目仅用于学习、研究与个人效率提升，不隶属于 CNKI 或其关联机构。
- 使用者应遵守 CNKI 网站条款、版权规则、机构授权范围和当地法律法规。
- 本项目不会绕过付费、授权、登录、验证码或访问控制机制。
- 请勿将本项目用于高频抓取、批量滥用、未授权下载或商业化侵权用途。

## 开发

基础语法检查：

```bash
python -m compileall main.py cnki_desktop core
```

建议在提交前至少确认应用可启动、核心模块可编译，并避免提交 `dist/`、`build/`、`build_temp/`、下载文档、导出文件和本地缓存。

## 贡献

欢迎通过 Issue 和 Pull Request 参与改进。提交前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 安全

如发现安全问题，请参考 [SECURITY.md](SECURITY.md) 中的方式进行报告。

## 许可证

本项目基于 [MIT License](LICENSE) 开源。

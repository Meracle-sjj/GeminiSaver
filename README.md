# GeminiSaver - Gemini 完美存档工具

专为保存 Google Gemini 对话设计的桌面工具。能够将 Gemini 分享链接（Share Links）一键保存为 **MHTML** 网页快照和高质量 **PDF** 文档。

解决了直接打印 Gemini 页面时出现的滚动截断、元素遮挡、懒加载内容缺失等问题。

## ✨ 核心功能

*   **双格式存档**：同时生成 MHTML（完整网页结构）和 PDF（便于阅读和分享）。
*   **智能滚动加载**：自动执行页面滚动，确保长对话内容被完整加载。
*   **完美净化**：
    *   自动移除顶部导航栏、底部输入框、侧边栏等干扰元素。
    *   智能识别并屏蔽“Google 隐私权政策”、“服务条款”、“试用 Advanced”等遮挡阅读的提示条，生成纯净文档。
*   **跨平台支持**：完美适配 **Windows** 和 **macOS**，针对不同系统优化字体和操作逻辑。
*   **网络代理支持**：
    *   支持配置 HTTP/HTTPS 代理，解决地区限制问题。
    *   不仅支持网页抓取时的代理，还支持**浏览器内核组件下载**时的代理加速。
*   **一键环境配置**：内置依赖修复功能，无需手动安装复杂的浏览器内核，支持查看实时下载进度。

## 📥 下载与使用

请前往 [Releases 页面](https://github.com/Meracle-sjj/GeminiSaver/releases) 下载最新版本的对应系统安装包：

*   **Windows**: 下载 `GeminiSaver-Windows.exe`
*   **macOS**: 下载 `GeminiSaver-MacOS` (首次运行可能需要并在“安全性与隐私”中允许打开)

### 使用步骤

1.  **输入链接**：填入 Gemini 对话的分享链接（点击 Gemini 网页右上角分享 -> 创建公开链接）。
2.  **设置文件名**：输入您希望保存的文件名。
3.  **代理设置**（可选）：
    *   如果您在中国大陆等需要代理的网络环境，请填入本地代理地址。
    *   macOS 默认检测 `http://127.0.0.1:7897`
    *   Windows 默认检测 `http://127.0.0.1:10808`
4.  **点击运行**：
    *   如果是首次运行，请先点击右下角的 **“修复/安装依赖组件”**，等待浏览器内核安装完成（日志区会提示进度，约 150MB）。
    *   点击 **“开始运行”**，程序将自动拉起浏览器进行抓取。

## 🛠️ 本地开发与编译

如果您希望修改源码或自行编译，请参考以下步骤。

### 依赖环境

*   Python 3.10+
*   Playwright

### 安装步骤

1.  克隆仓库：
    ```bash
    git clone https://github.com/Meracle-sjj/GeminiSaver.git
    cd GeminiSaver
    ```

2.  安装 Python 依赖：
    ```bash
    pip install -r requirements.txt
    ```

3.  安装 Playwright 浏览器内核：
    ```bash
    playwright install chromium
    ```

4.  运行代码：
    ```bash
    python GeminiGUI.py
    ```

### 打包 (PyInstaller)

项目集成了 GitHub Actions 自动打包。如果您需要在本地打包：

**Windows:**
```bash
pyinstaller --noconsole --onefile --name "GeminiSaver" GeminiGUI.py
```

**macOS:**
```bash
pyinstaller --noconsole --onefile --name "GeminiSaver" GeminiGUI.py
```

## ⚠️ 常见问题

**Q: 为什么生成的 PDF 是空白的？**
A: 这通常是由于文件路径编码或代理设置问题。v1.3 版本已修复 Windows 下的路径 URI 问题和换行符问题。请确保下载的是最新版本。

**Q: 点击“安装组件”没反应或报错？**
A: 请检查代理地址是否填写正确。程序会通过您设置的代理环境变量来加速下载 Playwright 内核。

**Q: Windows 上杀毒软件报毒？**
A: 由于使用了 PyInstaller 打包 unsigned exe，可能会被误报。这是 Python 打包工具的常见误报，请添加到信任列表。

## 📝 更新日志

### v1.3 (2025-01-07)
*   **修复**：Windows 下 MHTML 文件因换行符问题导致内容无法识别（白屏）的问题。
*   **修复**：Windows 下 PDF 生成路径 URI 问题。
*   **优化**：Windows 组件安装逻辑，移除CMD黑框，支持在 GUI 内查看实时下载进度。
*   **优化**：Windows 字体适配（微软雅黑），解决中文字体显示不自然的问题。
*   **功能**：增强 PDF 净化算法，彻底移除底部固定的隐私条款及横幅遮挡。
*   **调整**：移除日志中的 Emoji，统一使用简洁专业的提示语。

## ⚖️ 免责声明

本工具仅用于个人存档自己的 Gemini 对话记录。请勿用于抓取未经授权的内容或进行高频请求。

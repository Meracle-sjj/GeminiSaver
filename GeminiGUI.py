import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from playwright.sync_api import sync_playwright

# ==========================================
# 核心逻辑类
# ==========================================
class GeminiArchiver:
    def __init__(self, logger_func, proxy_server=None, headless_fetch=False, headless_print=True):
        """
        :param proxy_server: 代理地址字符串 (例如 "http://127.0.0.1:7897")，None 则不使用
        """
        self.logger = logger_func 
        self.headless_fetch = headless_fetch
        self.headless_print = headless_print
        
        # 构造 playwright 需要的 proxy 字典格式
        if proxy_server:
            self.proxy = {"server": proxy_server}
            self.log(f"🌐 使用代理: {proxy_server}")
        else:
            self.proxy = None
            self.log(f"🌐 代理未配置，使用直连模式")

    def log(self, message):
        if self.logger:
            self.logger(message)
        print(message) 

    def fetch_mhtml(self, url, output_mhtml_path):
        self.log(f"Phase 1: 正在抓取网页快照...")
        
        with sync_playwright() as p:
            self.log("🚀 启动浏览器 (抓取模式)...")
            # 关键修改：传入 self.proxy
            browser = p.chromium.launch(headless=self.headless_fetch, proxy=self.proxy)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                self.log(f"🔗 加载页面: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=120000)
                
                self.log("⏳ 页面骨架加载完毕，准备滚动...")
                time.sleep(5)

                self.log("📜 执行智能滚动 (约 30秒)...")
                for i in range(30): 
                    page.mouse.wheel(0, 4000)
                    time.sleep(1)
                    if i % 5 == 0:
                        self.log(f"   ...进度 {i}/30")
                
                self.log("🔄 执行回马枪检查...")
                page.mouse.wheel(0, -5000)
                time.sleep(2)
                page.mouse.wheel(0, 5000)
                time.sleep(3)

                self.log("💾 捕获 MHTML 数据...")
                cdp = context.new_cdp_session(page)
                result = cdp.send("Page.captureSnapshot", {"format": "mhtml"})
                
                with open(output_mhtml_path, "w", encoding="utf-8") as f:
                    f.write(result["data"])
                
                browser.close()
                self.log("✅ MHTML 保存成功！")
            except Exception as e:
                browser.close()
                raise e

    def convert_to_pdf(self, mhtml_path, output_pdf_path):
        abs_path = os.path.abspath(mhtml_path)
        file_url = f"file://{abs_path}"
        self.log(f"Phase 2: 处理排版并生成 PDF...")

        with sync_playwright() as p:
            self.log("🚀 启动渲染引擎 (打印模式)...")
            # 打印阶段不需要代理，因为是加载本地文件
            browser = p.chromium.launch(headless=self.headless_print)
            page = browser.new_page()
            page.emulate_media(media="screen")
            
            self.log("📂 加载本地 MHTML...")
            page.goto(file_url, wait_until="networkidle")
            time.sleep(3)

            self.log("✂️ 执行外科手术 (去头 + 展开)...")
            page.evaluate("""() => {
                const style = document.createElement('style');
                style.innerHTML = `
                    header, nav, footer, aside, [role="banner"], [role="navigation"],
                    .input-area, .sticky-container, button, mat-icon { display: none !important; }
                    body, html { background: white !important; }
                    @media print { @page { margin-top: 0; } body { margin-top: 0; } }
                `;
                document.head.appendChild(style);

                const keywords = ["企业应用场景", "Gemini 应用", "试用 Gemini Advanced", "订阅"];
                keywords.forEach(text => {
                    const xpath = `//*[contains(text(), '${text}')]`;
                    const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    for (let i = 0; i < result.snapshotLength; i++) {
                        let element = result.snapshotItem(i);
                        let parent = element.parentElement;
                        while (parent && parent !== document.body) {
                            const h = parent.offsetHeight;
                            const w = parent.offsetWidth;
                            if (w > 500 && h > 0 && h < 150) {
                                parent.style.display = 'none';
                                break;
                            }
                            parent = parent.parentElement;
                        }
                    }
                });

                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    if (el.style.display === 'none') continue;
                    const computed = window.getComputedStyle(el);
                    if (computed.position === 'fixed' || computed.position === 'sticky') {
                        if (parseInt(computed.top) < 100) {
                            el.style.display = 'none'; 
                        } else {
                            el.style.position = 'absolute';
                        }
                    }
                }

                let maxScrollHeight = 0;
                let mainContainer = null;
                document.querySelectorAll('div, main, article, section').forEach(el => {
                    if (el !== document.body && el !== document.documentElement) {
                        if (el.scrollHeight > maxScrollHeight) {
                            maxScrollHeight = el.scrollHeight;
                            mainContainer = el;
                        }
                    }
                });

                if (mainContainer) {
                    let curr = mainContainer;
                    while (curr && curr !== document.body) {
                        curr.style.height = 'auto';
                        curr.style.minHeight = '0';
                        curr.style.maxHeight = 'none';
                        curr.style.overflow = 'visible';
                        curr.style.display = 'block'; 
                        curr.style.position = 'static'; 
                        curr = curr.parentElement;
                    }
                    mainContainer.style.height = 'auto';
                    mainContainer.style.overflow = 'visible';
                    mainContainer.style.display = 'block';
                    Array.from(mainContainer.children).forEach(child => {
                        child.style.overflow = 'visible';
                        child.style.height = 'auto';
                    });
                }
                
                document.body.style.height = 'auto';
                document.body.style.overflow = 'visible';
            }""")
            
            time.sleep(2)

            self.log("🖨️ 正在生成 PDF...")
            page.pdf(
                path=output_pdf_path,
                format="A4",
                print_background=True,
                margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"},
                scale=0.8
            )
            browser.close()
            self.log("✅ PDF 生成成功！")

# ==========================================
# GUI 界面类
# ==========================================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini 完美存档工具 v1.1")
        self.root.geometry("600x600") # 稍微拉高一点以容纳新选项
        self.root.resizable(False, False)

        # 样式设置
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#ccc")

        # --- 第一部分：输入区 ---
        input_frame = ttk.LabelFrame(root, text=" 任务设置 ", padding=(10, 10))
        input_frame.pack(fill="x", padx=15, pady=10)

        # 1. 链接输入
        ttk.Label(input_frame, text="Gemini 分享链接:").grid(row=0, column=0, sticky="w", pady=5)
        self.url_entry = ttk.Entry(input_frame, width=50)
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.url_entry.insert(0, "https://gemini.google.com/share/...")

        # 2. 文件名输入
        ttk.Label(input_frame, text="保存文件名 (不带后缀):").grid(row=1, column=0, sticky="w", pady=5)
        self.filename_entry = ttk.Entry(input_frame, width=50)
        self.filename_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.filename_entry.insert(0, "My_Conversation")

        # 3. 代理设置 (新增功能)
        ttk.Label(input_frame, text="代理地址 (可选):").grid(row=2, column=0, sticky="w", pady=5)
        self.proxy_entry = ttk.Entry(input_frame, width=50)
        self.proxy_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # 智能判断默认代理
        default_proxy = ""
        if sys.platform == 'darwin': # macOS
            default_proxy = "http://127.0.0.1:7897" # Clash 默认
        elif sys.platform == 'win32': # Windows
            default_proxy = "http://127.0.0.1:10808" # v2rayN 默认
        
        self.proxy_entry.insert(0, default_proxy)
        ttk.Label(input_frame, text="*留空则直连。Mac常见7897，Win常见10808", font=("Arial", 8), foreground="gray").grid(row=3, column=1, sticky="w")

        # 默认位置提示
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        ttk.Label(input_frame, text=f"默认保存位置: {self.desktop_path}", font=("Arial", 8, "italic"), foreground="gray").grid(row=4, column=1, sticky="w", pady=(5,0))

        # --- 第二部分：控制区 ---
        control_frame = ttk.Frame(root)
        control_frame.pack(fill="x", padx=15, pady=5)

        self.start_btn = ttk.Button(control_frame, text="开始运行", command=self.start_thread, width=20)
        self.start_btn.pack(side="left", padx=5)

        self.install_btn = ttk.Button(control_frame, text="⚠️ 修复/安装依赖组件", command=self.install_browsers, width=20)
        self.install_btn.pack(side="right", padx=5)
        
        self.check_dependencies()

        # --- 第三部分：日志区 ---
        log_frame = ttk.LabelFrame(root, text=" 运行日志 ", padding=(10, 10))
        log_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', height=15)
        self.log_area.pack(fill="both", expand=True)
        self.log_area.tag_config("INFO", foreground="black")
        self.log_area.tag_config("SUCCESS", foreground="green")
        self.log_area.tag_config("ERROR", foreground="red")

        self.append_log("欢迎使用！请确认代理设置后点击“开始运行”。", "INFO")

    def append_log(self, text, level="INFO"):
        def _update():
            self.log_area.configure(state='normal')
            self.log_area.insert(tk.END, text + "\n", level)
            self.log_area.see(tk.END)
            self.log_area.configure(state='disabled')
        self.root.after(0, _update)

    def check_dependencies(self):
        def _check():
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    browser.close()
                self.root.after(0, lambda: self.install_btn.configure(state="disabled", text="✅ 组件已就绪"))
            except Exception as e:
                self.append_log(f"检测到组件缺失，请点击“修复依赖组件”。", "ERROR")
                self.root.after(0, lambda: self.install_btn.configure(state="normal", text="⚠️ 点击修复组件"))
        threading.Thread(target=_check, daemon=True).start()

    def install_browsers(self):
        def _install():
            self.install_btn.configure(state="disabled")
            self.append_log("正在下载浏览器内核 (约 150MB)，请耐心等待...", "INFO")
            try:
                import subprocess
                # 针对不同系统的打包环境，playwright 命令可能找不到，改用 python -m playwright
                cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for line in process.stdout:
                    self.append_log(line.strip(), "INFO")
                process.wait()
                
                if process.returncode == 0:
                    self.append_log("组件安装成功！", "SUCCESS")
                    self.install_btn.configure(text="✅ 组件已就绪")
                else:
                    self.append_log("组件安装失败，请检查网络或使用 pip 手动安装。", "ERROR")
                    self.install_btn.configure(state="normal")
            except Exception as e:
                self.append_log(f"安装出错: {str(e)}", "ERROR")
                self.install_btn.configure(state="normal")
        threading.Thread(target=_install, daemon=True).start()

    def start_thread(self):
        url = self.url_entry.get().strip()
        filename = self.filename_entry.get().strip()
        proxy_val = self.proxy_entry.get().strip()

        if not url.startswith("http"):
            messagebox.showerror("错误", "请输入有效的 Gemini 分享链接")
            return
        
        if not filename:
            messagebox.showerror("错误", "请输入文件名")
            return
            
        # 代理处理：如果用户留空，则传 None
        if not proxy_val:
            proxy_val = None

        self.start_btn.configure(state="disabled")
        threading.Thread(target=self.run_task, args=(url, filename, proxy_val), daemon=True).start()

    def run_task(self, url, filename, proxy_val):
        try:
            mhtml_path = os.path.join(self.desktop_path, f"{filename}.mhtml")
            pdf_path = os.path.join(self.desktop_path, f"{filename}.pdf")

            # 实例化工具，传入代理
            archiver = GeminiArchiver(
                logger_func=lambda msg: self.append_log(msg, "INFO"),
                proxy_server=proxy_val
            )
            
            archiver.fetch_mhtml(url, mhtml_path)
            archiver.convert_to_pdf(mhtml_path, pdf_path)

            self.append_log("🎉 全部任务完成！", "SUCCESS")
            messagebox.showinfo("成功", f"文件已保存至桌面:\n{pdf_path}")
            
            try:
                if sys.platform == 'win32':
                    os.startfile(pdf_path)
                elif sys.platform == 'darwin':
                    os.system(f'open "{pdf_path}"')
            except:
                pass

        except Exception as e:
            self.append_log(f"❌ 发生错误: {str(e)}", "ERROR")
            messagebox.showerror("运行出错", str(e))
        finally:
            self.root.after(0, lambda: self.start_btn.configure(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
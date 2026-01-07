import os
import time
from playwright.sync_api import sync_playwright

class GeminiArchiver:
    def __init__(self, headless_fetch=False, headless_print=True):
        """
        初始化存档工具
        :param headless_fetch: 抓取 MHTML 时是否隐藏浏览器 (建议 False 以便观察滚动)
        :param headless_print: 转换 PDF 时是否隐藏浏览器 (建议 True)
        """
        self.headless_fetch = headless_fetch
        self.headless_print = headless_print
        # 如果需要代理，请取消注释并修改下方
        self.proxy = None # {"server": "http://127.0.0.1:7897"} 

    def fetch_mhtml(self, url, output_mhtml_path):
        """第一步：滚动页面并抓取 MHTML 快照"""
        print(f"Phase 1: 正在抓取网页快照 -> {output_mhtml_path}")
        
        with sync_playwright() as p:
            print("  🚀 启动浏览器 (抓取模式)...")
            browser = p.chromium.launch(
                headless=self.headless_fetch,
                proxy=self.proxy
            )
            context = browser.new_context()
            page = context.new_page()
            
            print(f"  🔗 加载页面: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            
            print("  ⏳ 页面骨架加载完毕，准备滚动...")
            time.sleep(5)

            # --- 滚动逻辑 ---
            print("  📜 执行智能滚动 (预计 30秒)...")
            # 1. 向下猛滚
            for i in range(30): 
                page.mouse.wheel(0, 4000)
                time.sleep(1) # 给 React 渲染留时间
                if i % 5 == 0:
                    print(f"    ...进度 {i}/30")
            
            # 2. 回马枪 (防止中间漏加载)
            print("  🔄 执行回马枪检查...")
            page.mouse.wheel(0, -5000)
            time.sleep(2)
            page.mouse.wheel(0, 5000)
            time.sleep(3)

            print("  💾 调用 CDP 捕获 MHTML...")
            cdp = context.new_cdp_session(page)
            result = cdp.send("Page.captureSnapshot", {"format": "mhtml"})
            
            with open(output_mhtml_path, "w", encoding="utf-8") as f:
                f.write(result["data"])
            
            browser.close()
            print("  ✅ MHTML 保存成功！")

    def convert_to_pdf(self, mhtml_path, output_pdf_path):
        """第二步：清洗 MHTML 并打印为 PDF"""
        abs_path = os.path.abspath(mhtml_path)
        file_url = f"file://{abs_path}"
        print(f"Phase 2: 正在处理排版并生成 PDF -> {output_pdf_path}")

        with sync_playwright() as p:
            print("  🚀 启动渲染引擎 (打印模式)...")
            browser = p.chromium.launch(headless=self.headless_print)
            page = browser.new_page()
            
            # 必须模拟屏幕，否则会触发网页自带的打印隐藏样式
            page.emulate_media(media="screen")
            
            print("  📂 加载本地 MHTML...")
            page.goto(file_url, wait_until="networkidle")
            time.sleep(3)

            print("  ✂️ 执行外科手术 (去头 + 展开)...")
            page.evaluate("""() => {
                // --- A. 基础 CSS 隐藏 ---
                const style = document.createElement('style');
                style.innerHTML = `
                    /* 屏蔽常见标签 */
                    header, nav, footer, aside, [role="banner"], [role="navigation"],
                    .input-area, .sticky-container, button, mat-icon { display: none !important; }
                    /* 强制白底 */
                    body, html { background: white !important; }
                    /* 隐藏 Print 媒体查询产生的页边距 */
                    @media print { @page { margin-top: 0; } body { margin-top: 0; } }
                `;
                document.head.appendChild(style);

                // --- B. 猎杀行动：基于文本内容隐藏 Header ---
                const keywords = ["企业应用场景", "Gemini 应用", "试用 Gemini Advanced", "订阅"];
                keywords.forEach(text => {
                    const xpath = `//*[contains(text(), '${text}')]`;
                    const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    for (let i = 0; i < result.snapshotLength; i++) {
                        let element = result.snapshotItem(i);
                        let parent = element.parentElement;
                        // 向上寻找高度较小且宽的容器
                        while (parent && parent !== document.body) {
                            const h = parent.offsetHeight;
                            const w = parent.offsetWidth;
                            if (w > 500 && h > 0 && h < 150) {
                                parent.style.display = 'none';
                                break; // 找到一个就隐藏，继续下一个关键词
                            }
                            parent = parent.parentElement;
                        }
                    }
                });

                // --- C. 降维打击：扫描并隐藏顶部的 Fixed 元素 ---
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    if (el.style.display === 'none') continue;
                    const computed = window.getComputedStyle(el);
                    if (computed.position === 'fixed' || computed.position === 'sticky') {
                        if (parseInt(computed.top) < 100) { // 顶部 100px 内的固定元素直接杀掉
                            el.style.display = 'none'; 
                        } else {
                            el.style.position = 'absolute'; // 其他位置改为绝对定位
                        }
                    }
                }

                // --- D. 核弹级展开：找到主内容框并撑开 ---
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
                    // 确保子元素可见
                    Array.from(mainContainer.children).forEach(child => {
                        child.style.overflow = 'visible';
                        child.style.height = 'auto';
                    });
                }
                
                document.body.style.height = 'auto';
                document.body.style.overflow = 'visible';
            }""")
            
            time.sleep(2) # 等待 DOM 变动生效

            print("  🖨️ 正在生成 PDF...")
            page.pdf(
                path=output_pdf_path,
                format="A4",
                print_background=True,
                margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"},
                scale=0.8
            )
            browser.close()
            print(f"  ✅ PDF 生成成功！")

    def run(self, url, output_name):
        """一键运行主入口"""
        mhtml_file = f"{output_name}.mhtml"
        pdf_file = f"{output_name}.pdf"
        
        print(f"=== 开始处理任务: {output_name} ===")
        self.fetch_mhtml(url, mhtml_file)
        self.convert_to_pdf(mhtml_file, pdf_file)
        
        print("\n" + "="*30)
        print(f"🎉 全部完成！")
        print(f"1. MHTML 源文件: {os.path.abspath(mhtml_file)}")
        print(f"2. PDF 最终文件: {os.path.abspath(pdf_file)}")
        print("="*30)

# --- 使用示例 ---
if __name__ == "__main__":
    # 1. 填入你的链接
    target_url = "https://gemini.google.com/share/64424a661d7a" 
    
    # 2. 填入你想要的文件名（不带后缀）
    base_filename = "Gemini_雅思写作_Day12"

    # 3. 运行
    archiver = GeminiArchiver()
    archiver.run(target_url, base_filename)
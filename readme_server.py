import http.server
import socketserver
from socketserver import ThreadingMixIn
import webbrowser
import threading
import time
import os
import re

PORT = 8080

# 简单的Markdown解析器函数
def markdown_to_html(markdown):
    # 首先处理HTML标签，将它们暂时替换为占位符，避免后续正则替换影响
    html_placeholders = {}
    import re
    html_pattern = re.compile(r'<[^>]+>')
    
    def save_html(match):
        placeholder = f"__HTML_PLACEHOLDER_{len(html_placeholders)}__"
        html_placeholders[placeholder] = match.group(0)
        return placeholder
    
    # 保存所有HTML标签
    markdown = html_pattern.sub(save_html, markdown)
    
    # 标题处理
    markdown = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', markdown, flags=re.MULTILINE)
    markdown = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', markdown, flags=re.MULTILINE)
    markdown = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', markdown, flags=re.MULTILINE)
    
    # 粗体和斜体
    markdown = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', markdown)
    markdown = re.sub(r'\*(.*?)\*', r'<em>\1</em>', markdown)
    
    # 链接
    markdown = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', markdown)
    
    # 图片
    markdown = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1" />', markdown)
    
    # 恢复所有HTML标签
    for placeholder, html in html_placeholders.items():
        markdown = markdown.replace(placeholder, html)
    
    # 列表项
    markdown = re.sub(r'^- (.*?)$', r'<li>\1</li>', markdown, flags=re.MULTILINE)
    markdown = re.sub(r'^\d\. (.*?)$', r'<li>\1</li>', markdown, flags=re.MULTILINE)
    
    # 将连续的列表项包装在<ul>或<ol>中
    # 这里使用简化处理，实际可能需要更复杂的逻辑
    markdown = re.sub(r'(<li>.*?</li>\s*)+', lambda m: f'<ul>{m.group(0)}</ul>', markdown)
    
    # 引用块
    markdown = re.sub(r'^> (.*?)$', r'<blockquote>\1</blockquote>', markdown, flags=re.MULTILINE)
    
    # 代码块
    markdown = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', markdown, flags=re.DOTALL)
    
    # 行内代码
    markdown = re.sub(r'`(.*?)`', r'<code>\1</code>', markdown)
    
    # 段落处理（简单处理，实际可能需要更复杂的逻辑）
    lines = markdown.split('\n')
    html_lines = []
    in_pre = False
    
    for line in lines:
        if '<pre>' in line:
            in_pre = True
        if in_pre:
            html_lines.append(line)
        else:
            # 如果行不为空且不是标题、列表项、引用块等
            if line.strip() and not line.strip().startswith(('<h', '<ul', '<ol', '<li', '<blockquote')):
                html_lines.append(f'<p>{line}</p>')
            else:
                html_lines.append(line)
        if '</pre>' in line:
            in_pre = False
    
    return '\n'.join(html_lines)

# 设置自定义的处理器，添加GitHub风格的CSS样式
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 如果请求的是README.md或根路径
        if self.path == '/README.md' or self.path == '/':
            # 设置响应头
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # 读取README.md文件内容
            try:
                with open('README.md', 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 将Markdown转换为HTML
                html_content = markdown_to_html(content)
                
                # 创建GitHub风格的HTML响应
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>README.md - GitHub风格预览</title>
                    <style>
                        /* GitHub风格CSS */
                        :root {
                            --color-bg-primary: #ffffff;
                            --color-bg-secondary: #f6f8fa;
                            --color-text-primary: #24292e;
                            --color-text-secondary: #586069;
                            --color-border: #e1e4e8;
                            --color-link: #0366d6;
                            --color-link-hover: #0353a4;
                            --color-code-bg: #f6f8fa;
                            --color-quote-border: #e1e4e8;
                        }
                        
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
                            line-height: 1.6;
                            color: var(--color-text-primary);
                            background-color: var(--color-bg-secondary);
                            margin: 0;
                            padding: 0;
                        }
                        
                        .container {
                            max-width: 980px;
                            margin: 20px auto;
                            padding: 30px;
                            background-color: var(--color-bg-primary);
                            border-radius: 3px;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                        }
                        
                        h1, h2, h3, h4, h5, h6 {
                            margin-top: 24px;
                            margin-bottom: 16px;
                            font-weight: 600;
                            line-height: 1.25;
                            color: var(--color-text-primary);
                        }
                        
                        h1 {
                            font-size: 2em;
                            border-bottom: 1px solid var(--color-border);
                            padding-bottom: 0.3em;
                        }
                        
                        h2 {
                            font-size: 1.5em;
                            border-bottom: 1px solid var(--color-border);
                            padding-bottom: 0.3em;
                        }
                        
                        h3 {
                            font-size: 1.25em;
                        }
                        
                        p {
                            margin-top: 0;
                            margin-bottom: 16px;
                        }
                        
                        a {
                            color: var(--color-link);
                            text-decoration: none;
                        }
                        
                        a:hover {
                            text-decoration: underline;
                            color: var(--color-link-hover);
                        }
                        
                        ul, ol {
                            padding-left: 2em;
                            margin-top: 0;
                            margin-bottom: 16px;
                        }
                        
                        li {
                            margin-bottom: 8px;
                        }
                        
                        li > ul, li > ol {
                            margin-top: 8px;
                        }
                        
                        blockquote {
                            margin: 0;
                            padding: 0 1em;
                            color: var(--color-text-secondary);
                            border-left: 0.25em solid var(--color-quote-border);
                        }
                        
                        pre {
                            padding: 16px;
                            overflow: auto;
                            font-size: 85%;
                            line-height: 1.45;
                            background-color: var(--color-code-bg);
                            border-radius: 3px;
                            margin-top: 0;
                            margin-bottom: 16px;
                        }
                        
                        code {
                            padding: 0.2em 0.4em;
                            margin: 0;
                            font-size: 85%;
                            background-color: var(--color-code-bg);
                            border-radius: 3px;
                            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
                        }
                        
                        pre > code {
                            padding: 0;
                            margin: 0;
                            font-size: 100%;
                            word-break: normal;
                            white-space: pre;
                            background: transparent;
                            border: 0;
                        }
                        
                        img {
                            max-width: 100%;
                            box-sizing: content-box;
                            background-color: var(--color-bg-primary);
                        }
                        
                        /* 响应式设计 */
                        @media (max-width: 768px) {
                            .container {
                                padding: 20px;
                                margin: 10px;
                                width: auto;
                            }
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                """ + html_content + """
                    </div>
                </body>
                </html>
                """
                
                # 发送HTML响应
                self.wfile.write(html.encode('utf-8'))
                
            except FileNotFoundError:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                error_html = '<h1>404 Not Found</h1><p>README.md 文件不存在</p>'
                self.wfile.write(error_html.encode('utf-8'))
        else:
            # 对于其他文件，使用默认处理
            super().do_GET()

# 启动服务器的函数
# 创建支持多线程的TCP服务器类
class ThreadingTCPServer(ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True

def start_server():
    with ThreadingTCPServer(("0.0.0.0", PORT), CustomHandler) as httpd:
        print(f"服务器启动在 http://localhost:{PORT}")
        print(f"请在浏览器中访问 http://localhost:{PORT} 查看README.md")
        print("按 Ctrl+C 停止服务器")
        httpd.serve_forever()

if __name__ == "__main__":
    # 在新线程中启动服务器
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(1)
    
    # 自动打开浏览器
    url = f"http://localhost:{PORT}"
    print(f"正在打开浏览器: {url}")
    webbrowser.open(url)
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n服务器已停止")
import ctypes
import ctypes.wintypes
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
from datetime import datetime
import sys

# 获取前台窗口信息的函数
def get_active_window():
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        
        # 获取前台窗口句柄
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "无活动窗口", ""
        
        # 获取窗口标题
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            title = "无标题窗口"
        else:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
        
        # 获取进程名
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process_name = ""
        
        try:
            h_process = kernel32.OpenProcess(0x0410, False, pid)
            if h_process:
                exe_name = ctypes.create_unicode_buffer(256)
                psapi.GetModuleBaseNameW(h_process, None, exe_name, 256)
                process_name = exe_name.value
                kernel32.CloseHandle(h_process)
        except:
            process_name = ""
        
        return title, process_name
    except:
        return "无法获取窗口信息", ""

# 简单的HTTP处理器
class WindowHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 设置响应头 - 强制使用UTF-8编码
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 获取当前窗口信息
        window_title, process_name = get_active_window()
        
        # 构建JSON响应
        response = json.dumps({
            "window_title": window_title,
            "process_name": process_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "ok"
        }, ensure_ascii=False)  # ensure_ascii=False 确保中文不被转义
        
        # 发送响应
        self.wfile.write(response.encode('utf-8'))

# 启动服务器
def run_server():
    server_address = ('', 56566)
    httpd = HTTPServer(server_address, WindowHandler)
    
    # 获取本机IP
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    
    print(f"窗口信息服务已在端口56001启动")
    print(f"返回格式: JSON with UTF-8 encoding")
    print("按 Ctrl+C 停止")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        httpd.server_close()

if __name__ == '__main__':
    if sys.platform != "win32":
        print("错误：此程序仅支持Windows系统！")
        sys.exit(1)
    
    run_server()
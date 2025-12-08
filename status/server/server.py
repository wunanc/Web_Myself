import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
from datetime import datetime
import sys
import yaml
import urllib.request
import urllib.error

# 存储手机端app信息
mobile_app_info = {
    "app": "none",
    "timestamp": ""
}

# si变量
si = False

# 从远程PC服务获取窗口信息
def get_pc_window_info(config):
    try:
        if not config or not config.get('enable_windowsPC_service', True):
            return None
        
        pc_ip = config.get('windowsPC_service_ip', '127.0.0.1')
        pc_port = config.get('windowsPC_service_port', 5201)
        
        url = f"http://{pc_ip}:{pc_port}/"
        
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.URLError as e:
        print(f"无法连接到PC服务 ({pc_ip}:{pc_port}): {e}")
        return None
    except Exception as e:
        print(f"获取PC窗口信息出错: {e}")
        return None

# 加载配置文件
def load_config():
    try:
        # 获取脚本所在目录
        script_dir = __file__
        if script_dir == '<stdin>':
            # 如果直接运行，使用当前目录
            config_path = 'config.yml'
        else:
            # 使用脚本同目录的config.yml
            script_dir = __file__.replace('\\', '/')
            config_dir = '/'.join(script_dir.split('/')[:-1])
            config_path = f"{config_dir}/config.yml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"配置文件已加载: {config_path}")
        return config
    except Exception as e:
        print(f"无法加载配置文件: {e}")
        return None

# 手机端请求处理器（5202端口）
class MobileHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global mobile_app_info
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            # 存储手机app信息
            mobile_app_info["app"] = data.get("app", "")
            mobile_app_info["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 设置响应头
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # 返回成功响应
            response = json.dumps({
                "status": "ok",
                "message": f"已接收 {data.get('app', '')} 信息"
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
            
            print(f"[手机端] 接收到应用信息: {data.get('app', '')}")
        
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = json.dumps({
                "status": "error",
                "message": str(e)
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        # 抑制默认日志输出
        pass

# 主服务器请求处理器（5203端口）
class MainHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global si
        
        # 获取配置（从类属性中获取）
        config = getattr(self.server, 'config', None)
        
        # 设置响应头 - 强制使用UTF-8编码
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 获取PC窗口信息（从远程PC服务）
        pc_info = get_pc_window_info(config)
        
        if pc_info:
            pc_window = pc_info.get('window_title', '无法获取')
            pc_process = pc_info.get('process_name', '')
        else:
            pc_window = '无法连接到PC服务'
            pc_process = ''
        
        # 判断是否都无法获取信息
        # 手机无法获取：app为"none"；PC无法获取：pc_info为None
        if mobile_app_info["app"] == "none" and pc_info is None:
            si = True
        else:
            si = False
        
        # 构建JSON响应
        response = json.dumps({
            "pc": pc_window,
            "mobile": mobile_app_info["app"],
            "pc_process": pc_process,
            "si": si,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "ok"
        }, ensure_ascii=False)
        
        # 发送响应
        self.wfile.write(response.encode('utf-8'))
        print(f"[主服务] 返回PC窗口: {pc_window} | 手机应用: {mobile_app_info['app']} | si: {si}")
    
    def log_message(self, format, *args):
        # 抑制默认日志输出
        pass

# 启动服务器线程
def run_mobile_server(port):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MobileHandler)
    print(f"手机端监听服务已在端口 {port} 启动（接收手机app信息）")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

def run_main_server(port, config):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MainHandler)
    # 将配置保存到服务器实例中
    httpd.config = config
    print(f"主服务已在端口 {port} 启动（返回pc和mobile信息）")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

# 主函数
if __name__ == '__main__':
    # 加载配置
    config = load_config()
    
    if not config:
        print("使用默认配置...")
        mobile_port = 5202
        main_port = 5203
    else:
        mobile_port = config.get('mobile_listen_port', 5202)
        main_port = config.get('server_external_port', 5203)
    
    print("=" * 50)
    print("PC与手机信息同步服务器")
    print("=" * 50)
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    
    # 启动手机端监听服务（5202）
    if config is None or config.get('enable_mobile_listen_service', True):
        mobile_thread = threading.Thread(target=run_mobile_server, args=(mobile_port,), daemon=True)
        mobile_thread.start()
    
    # 启动主服务（5203）
    try:
        run_main_server(main_port, config)
    except KeyboardInterrupt:
        print("\n\n正在停止服务...")
        print("服务已停止")
        sys.exit(0)

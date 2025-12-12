import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime
import sys
import yaml
import urllib.request
import urllib.error
import ssl
import os

# 日志输出函数，带时间戳
def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

# 存储手机端app信息
mobile_app_info = {
    "app": "未知",
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
        log(f"无法连接到PC服务 ({pc_ip}:{pc_port}): {e}")
        return None
    except Exception as e:
        log(f"获取PC窗口信息出错: {e}")
        return None

# 加载配置文件
def load_config():
    config_path = "./config.yml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        log(f"配置文件已加载: {config_path}")
        return config
    except FileNotFoundError:
        log(f"配置文件未找到: {config_path}，将创建默认配置并保存。")
        default_content = (
            "# *号为必填项\n"
            "#是否开启电脑端读取窗口信息服务 *\n"
            "enable_windowsPC_service: true\n"
            "#电脑端ip地址 *\n"
            "windowsPC_service_ip: 127.0.0.1\n"
            "#电脑端端口号 *\n"
            "windowsPC_service_port: 5201\n\n"
            "#是否开启手机端监听服务 *\n"
            "enable_mobile_listen_service: true\n"
            "#手机端监听端口号 *\n"
            "mobile_listen_port: 5202\n"
            "#手机监听token(留空则不验证)\n"
            "mobile_listen_token: 1234\n\n"
            "#服务器外部访问端口 *\n"
            "server_external_port: 5203\n"
            "#是否启用HTTPS *\n"
            "enable_https: false\n"
            "#SSL证书文件路径（同一目录下的cert.pem文件）\n"
            "ssl_certfile: ./cert.pem\n"
            "#SSL私钥文件路径（同一目录下的key.pem文件）\n"
            "ssl_keyfile: ./key.pem\n"
        )
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(default_content)
            config = yaml.safe_load(default_content) or {}
            log(f"已生成默认配置文件: {config_path}")
            return config
        except Exception as e:
            log(f"无法创建默认配置文件: {e}")
            return None
    except Exception as e:
        log(f"无法加载配置文件: {e}")
        return None

# 手机端请求处理器（5202端口）
class MobileHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global mobile_app_info
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            # 获取配置
            config = getattr(self.server, 'config', None)
            
            # 验证token
            if config and config.get('mobile_listen_token'):
                expected_token = config.get('mobile_listen_token', '')
                provided_token = data.get('token', '')
                
                if provided_token != expected_token:
                    self.send_response(401)  # 未授权
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    response = json.dumps({
                        "status": "error",
                        "message": "Invalid token"
                    }, ensure_ascii=False)
                    self.wfile.write(response.encode('utf-8'))
                    log(f"[手机端] Token验证失败: 期望='{expected_token}', 收到='{provided_token}'")
                    return
            
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
            
            log(f"[手机端] 接收到应用信息: {data.get('app', '')}")
        
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = json.dumps({
                "status": "error",
                "message": str(e)
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
    
    def do_OPTIONS(self):
        # 处理 CORS 预检请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()
    
    def log_message(self, format, *args):
        # 抑制默认日志输出
        pass

# 主服务器请求处理器（5203端口）
class MainHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # 处理 CORS 预检请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()
    
    def do_GET(self):
        global si
        
        # 获取配置（从类属性中获取）
        config = getattr(self.server, 'config', None)
        
        # 设置响应头 - 强制使用UTF-8编码
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # 获取PC窗口信息（从远程PC服务）
        pc_info = get_pc_window_info(config)
        
        if pc_info:
            pc_window = pc_info.get('window_title', '无法获取')
            pc_process = pc_info.get('process_name', '')
        else:
            pc_window = '未知'
            pc_process = ''
        
        # 判断是否都无法获取信息
        # 手机无法获取：app为"none"；PC无法获取：pc_info为None
        if mobile_app_info["app"] == "未知" and pc_info is None:
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
        log(f"[主服务] 返回PC窗口: {pc_window} | 手机应用: {mobile_app_info['app']} | si: {si}")
    
    def log_message(self, format, *args):
        # 抑制默认日志输出
        pass

# 启动服务器线程
def run_mobile_server(port, config):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MobileHandler)
    # 将配置保存到服务器实例中
    httpd.config = config
    log(f"手机端监听服务已在端口 {port} 启动（接收手机app信息）")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

def run_main_server(port, config):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MainHandler)
    # 将配置保存到服务器实例中
    httpd.config = config
    
    # 检查是否启用HTTPS
    if config and config.get('enable_https', False):
        certfile = config.get('ssl_certfile', './cert.pem')
        keyfile = config.get('ssl_keyfile', './key.pem')
        
        # 检查证书文件是否存在
        if os.path.exists(certfile) and os.path.exists(keyfile):
            try:
                # 创建SSL上下文
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(certfile=certfile, keyfile=keyfile)
                
                # 包装socket
                httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
                log(f"主服务已在端口 {port} 启动HTTPS（返回pc和mobile信息）")
            except Exception as e:
                log(f"启用HTTPS失败: {e}，将使用HTTP")
                log(f"主服务已在端口 {port} 启动HTTP（返回pc和mobile信息）")
        else:
            log(f"证书文件不存在: certfile={certfile}, keyfile={keyfile}")
            log(f"主服务将在端口 {port} 启动HTTP（返回pc和mobile信息）")
    else:
        log(f"主服务已在端口 {port} 启动HTTP（返回pc和mobile信息）")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

# 主函数
if __name__ == '__main__':
    # 加载配置
    config = load_config()
    
    if not config:
        log("使用默认配置...")
        mobile_port = 5202
        main_port = 5203
        enable_https = False
    else:
        mobile_port = config.get('mobile_listen_port', 5202)
        main_port = config.get('server_external_port', 5203)
        enable_https = config.get('enable_https', False)
    
    log("=" * 50)
    log("PC与手机信息同步服务器")
    if enable_https:
        log("HTTPS模式已启用")
        log(f"证书文件: {config.get('ssl_certfile', './cert.pem')}")
        log(f"私钥文件: {config.get('ssl_keyfile', './key.pem')}")
    else:
        log("HTTP模式（未加密）")
    log("=" * 50)
    log("按 Ctrl+C 停止服务")
    log("=" * 50)
    
    # 启动手机端监听服务（5202）
    if config is None or config.get('enable_mobile_listen_service', True):
        mobile_thread = threading.Thread(target=run_mobile_server, args=(mobile_port, config), daemon=True)
        mobile_thread.start()
    
    # 启动主服务（5203）
    try:
        run_main_server(main_port, config)
    except KeyboardInterrupt:
        log("\n\n正在停止服务...")
        log("服务已停止")
        sys.exit(0)
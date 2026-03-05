import requests
import json
import os
import time

# --- 配置区 ---
GH_USER = "wunanc"
BILI_UID = "3461562578766467"
# --------------

def get_github_languages():
    print("正在抓取 GitHub 语言数据...")
    url = f"https://api.github.com/users/{GH_USER}/repos?per_page=100"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    # 尝试从环境变量获取 Token (本地运行可以手动填入字符串测试)
    token = os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    
    response = requests.get(url, headers=headers)
    
    # 检查请求是否成功
    if response.status_code != 200:
        print(f"❌ GitHub API 请求失败! 状态码: {response.status_code}")
        print(f"原因: {response.text}")
        return {"languages": {}, "total_repos": 0}

    repos = response.json()
    
    # 确保返回的是列表
    if not isinstance(repos, list):
        print("❌ 收到非预期的数据格式，可能是 API 限制消息。")
        return {"languages": {}, "total_repos": 0}
    
    lang_stats = {}
    for repo in repos:
        if not repo.get('fork') and repo.get('language'):
            lang = repo['language']
            lang_stats[lang] = lang_stats.get(lang, 0) + 1
            
    sorted_langs = dict(sorted(lang_stats.items(), key=lambda item: item[1], reverse=True))
    return {
        "languages": sorted_langs,
        "total_repos": len(repos)
    }

def get_bilibili_fans():
    print("正在抓取 Bilibili 粉丝数...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/"
    }
    url = f"https://api.bilibili.com/x/relation/stat?vmid={BILI_UID}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        res_json = response.json()
        if res_json['code'] == 0:
            return res_json['data']['follower']
        else:
            print(f"❌ B站返回异常: {res_json['message']}")
    except Exception as e:
        print(f"❌ B站抓取异常: {e}")
    return 0

def main():
    github_data = get_github_languages()
    bili_fans = get_bilibili_fans()
    
    # 强制使用北京时间 (Action 环境通常是 UTC)
    # 本地运行如果已经是北京时间，这行也没影响
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    result = {
        "github": github_data,
        "bilibili": {
            "follower": bili_fans
        },
        "updated_at": current_time
    }
    
    # 获取脚本所在目录，确保 data.json 存放在正确位置
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, "data.json")
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print(f"✅ 数据更新成功，已写入 {json_path}")

if __name__ == "__main__":
    main()
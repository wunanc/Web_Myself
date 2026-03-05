import requests
import json
import os
import time

# --- 配置区 ---
GH_USER = "wunanc"        # 你的 GitHub 用户名
BILI_UID = "3493282208008436" # 替换为你真实的 B 站 UID (在空间 URL 中可以看到)
# --------------

def get_github_languages():
    print("正在抓取 GitHub 语言数据...")
    url = f"https://api.github.com/users/{GH_USER}/repos?per_page=100"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    # 如果 Action 中配置了 GITHUB_TOKEN，可以避免触发速率限制
    token = os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    
    response = requests.get(url, headers=headers)
    repos = response.json()
    
    lang_stats = {}
    for repo in repos:
        # 排除 fork 的仓库，统计自己写的项目
        if not repo.get('fork') and repo.get('language'):
            lang = repo['language']
            lang_stats[lang] = lang_stats.get(lang, 0) + 1
            
    # 按使用频率排序
    sorted_langs = dict(sorted(lang_stats.items(), key=lambda item: item[1], reverse=True))
    return {
        "languages": sorted_langs,
        "total_repos": len(repos)
    }

def get_bilibili_fans():
    print("正在抓取 Bilibili 粉丝数...")
    # B站 API 需要 User-Agent 伪装，否则会返回 403
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://api.bilibili.com/x/relation/stat?vmid={BILI_UID}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        res_json = response.json()
        if res_json['code'] == 0:
            return res_json['data']['follower']
    except Exception as e:
        print(f"B站抓取失败: {e}")
    return 0

def main():
    github_data = get_github_languages()
    bili_fans = get_bilibili_fans()
    
    # 构造输出数据
    result = {
        "github": github_data,
        "bilibili": {
            "follower": bili_fans
        },
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 8*3600)) # 强制北京时间
    }
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print("数据更新成功，已写入 data.json")

if __name__ == "__main__":
    main()
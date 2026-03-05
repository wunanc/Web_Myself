import requests
import json
import os
import time

# --- 配置区 ---
GH_USER = "wunanc"
BILI_UID = "3461562578766467"
# --------------

def get_github_languages():
    print("正在抓取 GitHub 详细语言字节数据...")
    # 1. 先获取所有公共仓库列表
    repos_url = f"https://api.github.com/users/{GH_USER}/repos?per_page=100"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    token = os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    else:
        print("⚠️ 警告: 未检测到 GH_TOKEN，详细统计极易触发频率限制！")

    try:
        repos_res = requests.get(repos_url, headers=headers)
        if repos_res.status_code != 200:
            print(f"❌ 仓库列表请求失败: {repos_res.status_code}")
            return {"languages": {}, "total_repos": 0}
        
        repos = repos_res.json()
        total_lang_stats = {}
        valid_repo_count = 0

        for repo in repos:
            # 排除 fork 的仓库，只统计自己的原创代码
            if repo.get('fork'):
                continue
            
            valid_repo_count += 1
            repo_name = repo['name']
            # 2. 对每个仓库请求其详细语言分布 (获取字节数)
            lang_url = repo['languages_url']
            lang_res = requests.get(lang_url, headers=headers)
            
            if lang_res.status_code == 200:
                repo_langs = lang_res.json() # 格式如: {"Java": 1234, "HTML": 567}
                for lang, bytes_count in repo_langs.items():
                    total_lang_stats[lang] = total_lang_stats.get(lang, 0) + bytes_count
                print(f"  √ 已处理仓库: {repo_name}")
            else:
                print(f"  × 无法获取仓库语言: {repo_name}")
            
            # 稍微停顿，防止被反爬虫识别（Action 环境通常不需要，但本地建议留着）
            # time.sleep(0.1)

        # 按字节数从大到小排序
        sorted_langs = dict(sorted(total_lang_stats.items(), key=lambda item: item[1], reverse=True))
        
        return {
            "languages": sorted_langs,
            "total_repos": valid_repo_count
        }

    except Exception as e:
        print(f"❌ GitHub 数据抓取异常: {e}")
        return {"languages": {}, "total_repos": 0}

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
    except:
        pass
    return 0

def main():
    github_data = get_github_languages()
    bili_fans = get_bilibili_fans()
    
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    result = {
        "github": github_data,
        "bilibili": {
            "follower": bili_fans
        },
        "updated_at": current_time
    }
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, "data.json")
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print(f"✅ 深度数据更新成功，已写入 {json_path}")

if __name__ == "__main__":
    main()
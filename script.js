document.addEventListener('DOMContentLoaded', () => {
    // 指向你 GitHub 仓库中的 data.json 原始文件地址
    // 格式：https://raw.githubusercontent.com/用户名/仓库名/分支名/文件路径
    const DATA_URL = 'https://raw.githubusercontent.com/wunanc/Web_Myself/main/data.json';

    fetch(DATA_URL)
        .then(response => {
            if (!response.ok) throw new Error('网络请求失败');
            return response.json();
        })
        .then(data => {
            // 更新 B 站粉丝
            document.getElementById('bili-fans').innerText = data.bilibili.follower.toLocaleString();
            
            // 更新 GitHub 统计描述
            document.getElementById('repo-summary').innerHTML = `
                GitHub 共有 <strong>${data.github.total_repos}</strong> 个公共项目<br>
                数据最后同步: ${data.updated_at} (北京时间)
            `;

            // 渲染语言占比饼图
            const langEntries = Object.entries(data.github.languages).slice(0, 6);
            renderLanguageChart(langEntries);
        })
        .catch(err => {
            console.error('数据加载错误:', err);
            document.getElementById('bili-fans').innerText = "数据获取中...";
        });
});

function renderLanguageChart(langData) {
    const ctx = document.getElementById('languageChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: langData.map(i => i[0]),
            datasets: [{
                data: langData.map(i => i[1]),
                backgroundColor: ['#0071e3', '#34c759', '#ff9f0a', '#af52de', '#ff3b30', '#5ac8fa'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '70%',
            plugins: {
                legend: { position: 'right', labels: { usePointStyle: true, padding: 15 } }
            }
        }
    });
}
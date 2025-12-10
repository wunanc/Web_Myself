// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('Project Sleepy 状态面板已加载');
    
    // API 配置
    const API_URL = 'http://127.0.0.1:5203';
    
    // 获取状态数据
    function fetchStatusData() {
        fetch(API_URL)
            .then(response => response.json())
            .then(data => {
                updateUI(data);
            })
            .catch(error => {
                console.error('获取API数据失败:', error);
            });
    }
    
    // 更新UI
    function updateUI(data) {
        // 更新PC状态（37行）
        const pcStatus = document.querySelector('.pc-status');
        if (pcStatus) {
            pcStatus.textContent = data.pc;
            pcStatus.style.color = '#4ef34eff';
            console.log('PC状态已更新');
        }
        
        // 更新iPhone状态（41行）
        const iphoneStatus = document.querySelector('.iphone-status');
        if (iphoneStatus) {
            iphoneStatus.textContent = data.mobile;
            iphoneStatus.style.color = '#4ef34eff';
            console.log('iPhone状态已更新');
        }
        
        // 获取状态指示灯
        const statusDot = document.querySelector('.status-dot');
        
        // 根据si判断是否显示"似了"
        const statusText = document.querySelector('.status-text');
        if (data.si === true) {
            // si为True时显示"似了"，变成红色
            statusText.textContent = '似了';
            statusText.style.color = '#e74c3c';
            
            // 将绿点变成红色
            if (statusDot) {
                statusDot.style.backgroundColor = '#e74c3c';
                statusDot.style.boxShadow = '0 0 10px rgba(231, 76, 60, 0.7)';
            }
        } else {
            // si为False时显示"活着"，保持白色，绿点保持绿色
            statusText.textContent = '活着';
            statusText.style.color = '#78ff67d0';
            
            // 绿点恢复绿色
            if (statusDot) {
                statusDot.style.backgroundColor = '#2ecc71';
                statusDot.style.boxShadow = '0 0 10px rgba(46, 204, 113, 0.7)';
            }
        }
    }
    
    // 页面加载时立即获取一次数据
    fetchStatusData();
    
    // 每3秒更新一次数据
    //setInterval(fetchStatusData, 3000);
    
    // 添加简单的交互效果
    const infoBoxes = document.querySelectorAll('.info-box');
    
    // 为每个信息框添加点击效果（除了信息框4，因为它已经有自己的点击事件）
    infoBoxes.forEach(box => {
        if (box.id !== 'box4') {
            box.addEventListener('click', function() {
                this.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 200);
            });
        }
    });
    
    // 为信息框4添加点击跳转功能
    const box4 = document.getElementById('box4');
    if (box4) {
        // 添加可点击样式类
        box4.classList.add('clickable');
        
        // 添加点击事件
        box4.addEventListener('click', function() {
            // 跳转到GitHub仓库
            window.open('https://github.com/wunanc/Web_Myself', '_blank');
            
            // 添加点击反馈效果
            this.style.transform = 'scale(0.98)';
            this.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
            
            setTimeout(() => {
                this.style.transform = '';
                this.style.backgroundColor = '';
            }, 200);
        });
        
        // 添加键盘访问支持
        box4.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.click();
            }
        });
        
        // 添加可访问性属性
        box4.setAttribute('tabindex', '0');
        box4.setAttribute('role', 'button');
        box4.setAttribute('aria-label', '跳转到GitHub仓库页面');
    }
    
    // 状态指示灯闪烁效果（可选）
    const statusDot = document.querySelector('.status-dot');
    let blinkInterval;
    
    // 模拟状态指示灯呼吸效果
    function startStatusBlink() {
        let isBright = true;
        
        blinkInterval = setInterval(() => {
            if (isBright) {
                statusDot.style.boxShadow = '0 0 5px rgba(46, 204, 113, 0.5)';
                isBright = false;
            } else {
                statusDot.style.boxShadow = '0 0 10px rgba(46, 204, 113, 0.7)';
                isBright = true;
            }
        }, 2000);
    }
    
    // 启动状态指示灯效果
    if (statusDot) {
        startStatusBlink();
    }
    
    // 添加简单的键盘快捷键
    document.addEventListener('keydown', function(event) {
        // 按ESC键停止指示灯闪烁
        if (event.key === 'Escape') {
            if (blinkInterval) {
                clearInterval(blinkInterval);
                if (statusDot) {
                    statusDot.style.boxShadow = '0 0 10px rgba(46, 204, 113, 0.7)';
                }
                console.log('状态指示灯闪烁已停止');
            } else if (statusDot) {
                startStatusBlink();
                console.log('状态指示灯闪烁已启动');
            }
        }
    });
});
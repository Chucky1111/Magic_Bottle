// 动不动高烧之瓶 - 玻璃球游戏
// 体现冷热交替和突然抽风的魔瓶特质

// 游戏状态
interface GameState {
    ball: {
        x: number;
        y: number;
        radius: number;
        dx: number;
        dy: number;
        color: string;
        temperature: number; // -1 (冷) 到 1 (热)
        isDragging: boolean;
        lastDragX: number;
        lastDragY: number;
    };
    temperature: number; // 0 (冷) 到 1 (热)
    feverCount: number;
    isAutoMode: boolean;
    lastFeverTime: number;
    feverActive: boolean;
    feverEndTime: number;
    logs: Array<{ text: string; type: 'cold' | 'hot' | 'fever'; time: number }>;
    // 开场动画状态
    introActive: boolean;
    introStartTime: number;
    introPhase: number; // 0-4: 温度扫描、球体聚集、温度波动、高烧突变、过渡完成
    introProgress: number; // 当前阶段进度 0-1
}

// 初始化游戏状态
const state: GameState = {
    ball: {
        x: 400,
        y: 250,
        radius: 30,
        dx: 2,
        dy: 1.5,
        color: '#4dc3ff',
        temperature: 0,
        isDragging: false,
        lastDragX: 0,
        lastDragY: 0,
    },
    temperature: 0.5,
    feverCount: 0,
    isAutoMode: false,
    lastFeverTime: 0,
    feverActive: false,
    feverEndTime: 0,
    logs: [
        { text: '游戏开始: 玻璃球初始化完成', type: 'cold', time: Date.now() },
        { text: '温度平衡: 冷热交替开始', type: 'hot', time: Date.now() - 1000 },
    ],
    // 开场动画初始状态
    introActive: true,
    introStartTime: Date.now(),
    introPhase: 0,
    introProgress: 0,
};

// DOM 元素
const canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
const ctx = canvas.getContext('2d')!;
const tempFill = document.getElementById('tempFill') as HTMLDivElement;
const tempThumb = document.getElementById('tempThumb') as HTMLDivElement;
const tempValue = document.getElementById('tempValue') as HTMLSpanElement;
const feverCount = document.getElementById('feverCount') as HTMLSpanElement;
const ballSpeed = document.getElementById('ballSpeed') as HTMLSpanElement;
const logEntries = document.getElementById('logEntries') as HTMLDivElement;
const resetBtn = document.getElementById('resetBtn') as HTMLButtonElement;
const feverBtn = document.getElementById('feverBtn') as HTMLButtonElement;
const autoBtn = document.getElementById('autoBtn') as HTMLButtonElement;
const clearLogBtn = document.getElementById('clearLogBtn') as HTMLButtonElement;
const tempSlider = document.querySelector('.temp-slider') as HTMLDivElement;

// 温度滑块交互
let isDraggingTemp = false;

tempThumb.addEventListener('mousedown', (e) => {
    isDraggingTemp = true;
    tempThumb.style.cursor = 'grabbing';
    updateTemperatureFromEvent(e);
});

document.addEventListener('mousemove', (e) => {
    if (isDraggingTemp) {
        updateTemperatureFromEvent(e);
    }
});

document.addEventListener('mouseup', () => {
    isDraggingTemp = false;
    tempThumb.style.cursor = 'grab';
});

tempSlider.addEventListener('click', (e) => {
    updateTemperatureFromEvent(e);
});

function updateTemperatureFromEvent(e: MouseEvent) {
    const rect = tempSlider.getBoundingClientRect();
    let x = e.clientX - rect.left;
    x = Math.max(0, Math.min(x, rect.width));
    const temp = x / rect.width;
    setTemperature(temp);
}

function setTemperature(temp: number) {
    state.temperature = temp;
    
    // 更新UI
    const percent = temp * 100;
    tempFill.style.width = `${percent}%`;
    tempThumb.style.left = `${percent}%`;
    
    // 更新温度显示
    const tempCelsius = Math.round((temp * 60) - 10); // -10°C 到 50°C
    tempValue.textContent = `${tempCelsius}°C`;
    
    // 更新球的温度
    state.ball.temperature = temp * 2 - 1; // 映射到 -1 到 1
    
    // 根据温度调整球颜色
    updateBallColor();
    
    // 添加日志
    if (temp < 0.3) {
        addLog('温度下降: 球体变脆', 'cold');
    } else if (temp > 0.7) {
        addLog('温度上升: 球体膨胀', 'hot');
    }
}

// 球颜色更新
function updateBallColor() {
    const t = state.ball.temperature; // -1 到 1
    
    if (t < 0) {
        // 冷色调
        const coldness = Math.abs(t);
        const r = Math.round(77 + (255 - 77) * coldness);
        const g = Math.round(195 + (255 - 195) * coldness);
        const b = 255;
        state.ball.color = `rgb(${r}, ${g}, ${b})`;
    } else {
        // 暖色调
        const warmth = t;
        const r = 255;
        const g = Math.round(102 + (255 - 102) * (1 - warmth));
        const b = Math.round(102 + (255 - 102) * (1 - warmth));
        state.ball.color = `rgb(${r}, ${g}, ${b})`;
    }
}

// 添加日志
function addLog(text: string, type: 'cold' | 'hot' | 'fever') {
    const log = { text, type, time: Date.now() };
    state.logs.unshift(log);
    
    // 限制日志数量
    if (state.logs.length > 20) {
        state.logs.pop();
    }
    
    // 更新UI
    updateLogDisplay();
}

function updateLogDisplay() {
    logEntries.innerHTML = '';
    
    state.logs.forEach(log => {
        const entry = document.createElement('div');
        entry.className = `log-entry ${log.type}`;
        entry.textContent = log.text;
        logEntries.appendChild(entry);
    });
}

// 触发高烧事件
function triggerFever() {
    if (state.feverActive) return;
    
    state.feverActive = true;
    state.feverCount++;
    state.lastFeverTime = Date.now();
    state.feverEndTime = Date.now() + 3000; // 高烧持续3秒
    
    // 更新计数
    feverCount.textContent = state.feverCount.toString();
    
    // 添加日志
    addLog('高烧事件: 行为突变!', 'fever');
    
    // 视觉反馈
    document.body.classList.add('fever-effect');
    setTimeout(() => {
        document.body.classList.remove('fever-effect');
    }, 300);
    
    // 随机改变球的行为
    const randomBehavior = Math.floor(Math.random() * 4);
    switch (randomBehavior) {
        case 0: // 速度突变
            state.ball.dx *= 3;
            state.ball.dy *= 3;
            addLog('速度突变: 球速激增!', 'fever');
            break;
        case 1: // 方向突变
            state.ball.dx = -state.ball.dx;
            state.ball.dy = -state.ball.dy;
            addLog('方向突变: 球体反向!', 'fever');
            break;
        case 2: // 大小突变
            state.ball.radius = Math.random() * 20 + 20;
            addLog('大小突变: 球体膨胀/收缩!', 'fever');
            break;
        case 3: // 温度突变
            state.temperature = Math.random();
            setTemperature(state.temperature);
            addLog('温度突变: 冷热急转!', 'fever');
            break;
    }
    
    // 更新按钮状态
    feverBtn.disabled = true;
    feverBtn.innerHTML = '<i class="fas fa-fire"></i> 高烧中...';
}

// 重置球
function resetBall() {
    state.ball.x = canvas.width / 2;
    state.ball.y = canvas.height / 2;
    state.ball.dx = 2;
    state.ball.dy = 1.5;
    state.ball.radius = 30;
    state.ball.isDragging = false;
    
    addLog('球体重置: 回到中心', 'cold');
}

// 自动模式切换
function toggleAutoMode() {
    state.isAutoMode = !state.isAutoMode;
    
    if (state.isAutoMode) {
        autoBtn.innerHTML = '<i class="fas fa-pause"></i> 停止自动';
        autoBtn.classList.add('fever');
        addLog('自动模式开启: 随机突变', 'hot');
    } else {
        autoBtn.innerHTML = '<i class="fas fa-random"></i> 自动模式';
        autoBtn.classList.remove('fever');
        addLog('自动模式关闭', 'cold');
    }
}

// 球拖拽交互
canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const distance = Math.sqrt(
        Math.pow(x - state.ball.x, 2) + Math.pow(y - state.ball.y, 2)
    );
    
    if (distance <= state.ball.radius) {
        state.ball.isDragging = true;
        state.ball.lastDragX = x;
        state.ball.lastDragY = y;
        canvas.style.cursor = 'grabbing';
        
        addLog('抓住球体: 可以拖拽', 'cold');
    }
});

canvas.addEventListener('mousemove', (e) => {
    if (!state.ball.isDragging) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    state.ball.x = x;
    state.ball.y = y;
    
    // 计算速度基于拖拽移动
    state.ball.dx = (x - state.ball.lastDragX) * 0.5;
    state.ball.dy = (y - state.ball.lastDragY) * 0.5;
    
    state.ball.lastDragX = x;
    state.ball.lastDragY = y;
});

canvas.addEventListener('mouseup', () => {
    if (state.ball.isDragging) {
        state.ball.isDragging = false;
        canvas.style.cursor = 'default';
        addLog('释放球体: 开始滚动', 'hot');
    }
});

canvas.addEventListener('mouseleave', () => {
    if (state.ball.isDragging) {
        state.ball.isDragging = false;
        canvas.style.cursor = 'default';
    }
});

// 按钮事件
resetBtn.addEventListener('click', resetBall);
feverBtn.addEventListener('click', triggerFever);
autoBtn.addEventListener('click', toggleAutoMode);
clearLogBtn.addEventListener('click', () => {
    state.logs = [];
    updateLogDisplay();
    addLog('日志已清空', 'cold');
});

// 游戏循环
function gameLoop() {
    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 检查是否处于开场动画阶段
    if (state.introActive) {
        // 绘制开场动画
        drawIntro();
        
        // 检查开场动画是否结束（在drawIntro中处理）
        // 如果开场动画刚结束，确保球的状态正确
        if (!state.introActive && state.introPhase >= 5) {
            // 重置球到初始位置（开场动画可能在中心绘制）
            state.ball.x = 400;
            state.ball.y = 250;
            state.ball.dx = 2;
            state.ball.dy = 1.5;
            state.ball.radius = 30;
            state.ball.color = '#4dc3ff';
            state.ball.temperature = 0;
            state.temperature = 0.5;
            
            // 更新温度显示
            setTemperature(state.temperature);
        }
    } else {
        // 正常游戏循环
        // 绘制背景
        drawBackground();
        
        // 更新高烧状态
        updateFeverState();
        
        // 更新自动模式
        updateAutoMode();
        
        // 更新球物理
        updateBallPhysics();
        
        // 绘制球
        drawBall();
        
        // 绘制温度影响
        drawTemperatureEffects();
        
        // 更新球速显示
        const speed = Math.sqrt(state.ball.dx * state.ball.dx + state.ball.dy * state.ball.dy);
        ballSpeed.textContent = `${speed.toFixed(1)}x`;
    }
    
    requestAnimationFrame(gameLoop);
}

function drawBackground() {
    // 渐变背景
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, 'rgba(10, 10, 20, 0.8)');
    gradient.addColorStop(1, 'rgba(26, 26, 46, 0.8)');
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 网格线
    ctx.strokeStyle = 'rgba(100, 100, 150, 0.1)';
    ctx.lineWidth = 1;
    
    const gridSize = 40;
    for (let x = 0; x < canvas.width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }
    
    for (let y = 0; y < canvas.height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }
}

function drawIntro() {
    // 计算开场动画进度
    const introDuration = 4000; // 4秒总时长
    const elapsed = Date.now() - state.introStartTime;
    const totalProgress = Math.min(elapsed / introDuration, 1);
    
    // 确定当前阶段 (0-4)
    const phaseDuration = introDuration / 5; // 5个阶段，每个0.8秒
    state.introPhase = Math.floor(elapsed / phaseDuration);
    state.introProgress = (elapsed % phaseDuration) / phaseDuration;
    
    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 绘制开场背景（比正常背景更暗）
    const bgGradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    bgGradient.addColorStop(0, 'rgba(5, 5, 10, 0.9)');
    bgGradient.addColorStop(1, 'rgba(13, 13, 23, 0.9)');
    ctx.fillStyle = bgGradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 根据阶段绘制不同的效果
    switch (state.introPhase) {
        case 0: // 温度扫描：冷到热
            drawIntroPhase0();
            break;
        case 1: // 球体聚集：碎片形成球
            drawIntroPhase1();
            break;
        case 2: // 温度波动：颜色快速变化
            drawIntroPhase2();
            break;
        case 3: // 高烧突变：脉冲和震动
            drawIntroPhase3();
            break;
        case 4: // 过渡完成：淡出到正常
            drawIntroPhase4();
            break;
        default:
            // 开场结束
            state.introActive = false;
            addLog('开场动画结束: 游戏开始!', 'fever');
            break;
    }
    
    // 在所有阶段都显示魔瓶编号 "115"
    drawBottleNumber();
}

function drawIntroPhase0() {
    // 阶段0: 温度从冷到热扫描
    const scanPos = state.introProgress * canvas.width;
    
    // 绘制温度扫描条
    const scanWidth = 50;
    const scanGradient = ctx.createLinearGradient(0, 0, scanWidth, 0);
    scanGradient.addColorStop(0, '#4dc3ff'); // 冷
    scanGradient.addColorStop(0.5, '#ffffff'); // 中性
    scanGradient.addColorStop(1, '#ff6666'); // 热
    
    ctx.fillStyle = scanGradient;
    ctx.fillRect(scanPos - scanWidth/2, canvas.height/2 - 10, scanWidth, 20);
    
    // 绘制扫描光晕
    const glowRadius = 30 + Math.sin(state.introProgress * Math.PI * 4) * 10;
    const glowGradient = ctx.createRadialGradient(
        scanPos, canvas.height/2, 0,
        scanPos, canvas.height/2, glowRadius
    );
    glowGradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
    glowGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
    
    ctx.fillStyle = glowGradient;
    ctx.fillRect(scanPos - glowRadius, canvas.height/2 - glowRadius, glowRadius * 2, glowRadius * 2);
    
    // 显示阶段文字
    ctx.font = 'bold 24px "JetBrains Mono", monospace';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.fillText('温度扫描...', canvas.width/2, canvas.height/2 + 80);
}

function drawIntroPhase1() {
    // 阶段1: 球体碎片聚集
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const targetRadius = 30;
    
    // 绘制正在形成的球体
    const currentRadius = targetRadius * state.introProgress;
    
    // 绘制球体轮廓
    ctx.beginPath();
    ctx.arc(centerX, centerY, currentRadius, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // 绘制聚集中的碎片
    const fragmentCount = 12;
    for (let i = 0; i < fragmentCount; i++) {
        const angle = (i / fragmentCount) * Math.PI * 2;
        const distance = 150 * (1 - state.introProgress);
        const fragmentX = centerX + Math.cos(angle) * distance;
        const fragmentY = centerY + Math.sin(angle) * distance;
        const fragmentSize = 8 * (1 - state.introProgress);
        
        // 碎片颜色：根据角度决定冷热
        const colorPos = i / fragmentCount;
        let fragmentColor;
        if (colorPos < 0.5) {
            // 冷色调
            const coldIntensity = 1 - colorPos * 2;
            fragmentColor = `rgb(${Math.round(77 + 178 * coldIntensity)}, ${Math.round(195 + 60 * coldIntensity)}, 255)`;
        } else {
            // 热色调
            const hotIntensity = (colorPos - 0.5) * 2;
            fragmentColor = `rgb(255, ${Math.round(102 + 153 * (1 - hotIntensity))}, ${Math.round(102 + 153 * (1 - hotIntensity))})`;
        }
        
        ctx.fillStyle = fragmentColor;
        ctx.beginPath();
        ctx.arc(fragmentX, fragmentY, fragmentSize, 0, Math.PI * 2);
        ctx.fill();
    }
    
    // 显示阶段文字
    ctx.font = 'bold 24px "JetBrains Mono", monospace';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.fillText('球体聚集...', canvas.width/2, canvas.height/2 + 80);
}

function drawIntroPhase2() {
    // 阶段2: 温度波动，球体颜色快速变化
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 30;
    
    // 快速变化的温度值
    const tempValue = Math.sin(state.introProgress * Math.PI * 8) * 0.5 + 0.5; // 0到1之间快速振荡
    
    // 根据温度计算球体颜色
    let ballColor;
    if (tempValue < 0.5) {
        const coldIntensity = 1 - tempValue * 2;
        ballColor = `rgb(${Math.round(77 + 178 * coldIntensity)}, ${Math.round(195 + 60 * coldIntensity)}, 255)`;
    } else {
        const hotIntensity = (tempValue - 0.5) * 2;
        ballColor = `rgb(255, ${Math.round(102 + 153 * (1 - hotIntensity))}, ${Math.round(102 + 153 * (1 - hotIntensity))})`;
    }
    
    // 绘制球体
    ctx.fillStyle = ballColor;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.fill();
    
    // 绘制球体光晕（反映温度）
    const glowGradient = ctx.createRadialGradient(
        centerX, centerY, radius,
        centerX, centerY, radius * 3
    );
    
    if (tempValue < 0.5) {
        glowGradient.addColorStop(0, 'rgba(77, 195, 255, 0.5)');
        glowGradient.addColorStop(1, 'rgba(77, 195, 255, 0)');
    } else {
        glowGradient.addColorStop(0, 'rgba(255, 102, 102, 0.5)');
        glowGradient.addColorStop(1, 'rgba(255, 102, 102, 0)');
    }
    
    ctx.fillStyle = glowGradient;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius * 3, 0, Math.PI * 2);
    ctx.fill();
    
    // 绘制温度波动指示器
    const indicatorWidth = 200;
    const indicatorX = canvas.width/2 - indicatorWidth/2;
    const indicatorY = canvas.height/2 + 60;
    
    // 背景
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(indicatorX, indicatorY, indicatorWidth, 10);
    
    // 温度填充
    ctx.fillStyle = ballColor;
    ctx.fillRect(indicatorX, indicatorY, indicatorWidth * tempValue, 10);
    
    // 显示阶段文字
    ctx.font = 'bold 24px "JetBrains Mono", monospace';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.fillText('温度波动...', canvas.width/2, canvas.height/2 + 120);
}

function drawIntroPhase3() {
    // 阶段3: 高烧突变
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 30;
    
    // 高烧效果：球体大小脉冲
    const pulseScale = 1 + Math.sin(state.introProgress * Math.PI * 6) * 0.3;
    const currentRadius = radius * pulseScale;
    
    // 绘制高烧球体（红色调）
    const ballGradient = ctx.createRadialGradient(
        centerX, centerY, 0,
        centerX, centerY, currentRadius
    );
    ballGradient.addColorStop(0, '#ff3333');
    ballGradient.addColorStop(1, '#cc0000');
    
    ctx.fillStyle = ballGradient;
    ctx.beginPath();
    ctx.arc(centerX, centerY, currentRadius, 0, Math.PI * 2);
    ctx.fill();
    
    // 绘制高烧脉冲波纹
    const pulseCount = 3;
    for (let i = 0; i < pulseCount; i++) {
        const pulseProgress = (state.introProgress + i * 0.2) % 1;
        const pulseRadius = currentRadius + pulseProgress * 100;
        const pulseAlpha = 0.5 * (1 - pulseProgress);
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, pulseRadius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 50, 50, ${pulseAlpha})`;
        ctx.lineWidth = 2;
        ctx.stroke();
    }
    
    // 画面震动效果
    const shakeIntensity = (1 - state.introProgress) * 5;
    const shakeX = (Math.random() - 0.5) * shakeIntensity;
    const shakeY = (Math.random() - 0.5) * shakeIntensity;
    ctx.translate(shakeX, shakeY);
    
    // 显示阶段文字（带震动）
    ctx.font = 'bold 28px "JetBrains Mono", monospace';
    ctx.fillStyle = '#ff6666';
    ctx.textAlign = 'center';
    ctx.fillText('高烧突变!', canvas.width/2, canvas.height/2 + 80);
    
    // 重置变换
    ctx.setTransform(1, 0, 0, 1, 0, 0);
}

function drawIntroPhase4() {
    // 阶段4: 过渡到正常游戏
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 30;
    
    // 淡出效果：逐渐显示正常球体
    const fadeAlpha = state.introProgress;
    
    // 绘制正常球体（逐渐显现）
    ctx.globalAlpha = fadeAlpha;
    ctx.fillStyle = '#4dc3ff';
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
    
    // 绘制淡出遮罩
    const fadeGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    fadeGradient.addColorStop(0, `rgba(5, 5, 10, ${1 - fadeAlpha})`);
    fadeGradient.addColorStop(1, `rgba(13, 13, 23, ${1 - fadeAlpha})`);
    
    ctx.fillStyle = fadeGradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 显示过渡文字
    ctx.font = 'bold 24px "JetBrains Mono", monospace';
    ctx.fillStyle = `rgba(255, 255, 255, ${fadeAlpha})`;
    ctx.textAlign = 'center';
    ctx.fillText('游戏即将开始...', canvas.width/2, canvas.height/2 + 80);
}

function drawBottleNumber() {
    // 在所有开场阶段都显示魔瓶编号 "115"
    ctx.font = 'bold 48px "JetBrains Mono", monospace';
    ctx.fillStyle = 'rgba(157, 78, 221, 0.3)';
    ctx.textAlign = 'center';
    ctx.fillText('115', canvas.width/2, canvas.height/2 - 150);
    
    // 添加微光效果
    const glowSize = 2 + Math.sin(Date.now() / 500) * 1;
    ctx.shadowColor = 'rgba(157, 78, 221, 0.5)';
    ctx.shadowBlur = glowSize * 10;
    ctx.fillText('115', canvas.width/2, canvas.height/2 - 150);
    ctx.shadowBlur = 0;
}

function updateFeverState() {
    if (state.feverActive && Date.now() > state.feverEndTime) {
        state.feverActive = false;
        feverBtn.disabled = false;
        feverBtn.innerHTML = '<i class="fas fa-fire"></i> 触发高烧';
        
        // 恢复球的行为
        state.ball.dx /= 3;
        state.ball.dy /= 3;
        state.ball.radius = 30;
        
        addLog('高烧结束: 恢复正常', 'cold');
    }
}

function updateAutoMode() {
    if (!state.isAutoMode) return;
    
    // 随机温度波动
    if (Math.random() < 0.02) {
        state.temperature += (Math.random() - 0.5) * 0.3;
        state.temperature = Math.max(0, Math.min(1, state.temperature));
        setTemperature(state.temperature);
    }
    
    // 随机触发高烧
    if (Math.random() < 0.005 && !state.feverActive) {
        triggerFever();
    }
}

function updateBallPhysics() {
    if (state.ball.isDragging) return;
    
    // 应用温度影响
    const tempEffect = state.ball.temperature; // -1 到 1
    
    // 冷: 速度减慢但更稳定
    if (tempEffect < 0) {
        state.ball.dx *= 0.99;
        state.ball.dy *= 0.99;
    }
    // 热: 速度加快但不稳定
    else {
        state.ball.dx *= 1.01;
        state.ball.dy *= 1.01;
        
        // 随机扰动
        if (Math.random() < 0.1) {
            state.ball.dx += (Math.random() - 0.5) * 0.5;
            state.ball.dy += (Math.random() - 0.5) * 0.5;
        }
    }
    
    // 边界碰撞
    if (state.ball.x - state.ball.radius < 0 || state.ball.x + state.ball.radius > canvas.width) {
        state.ball.dx = -state.ball.dx;
        addLog('边界碰撞: 左右反弹', 'hot');
    }
    
    if (state.ball.y - state.ball.radius < 0 || state.ball.y + state.ball.radius > canvas.height) {
        state.ball.dy = -state.ball.dy;
        addLog('边界碰撞: 上下反弹', 'cold');
    }
    
    // 更新位置
    state.ball.x += state.ball.dx;
    state.ball.y += state.ball.dy;
}

function drawBall() {
    ctx.save();
    
    // 球阴影
    ctx.shadowColor = state.ball.color;
    ctx.shadowBlur = 20;
    
    // 球体
    ctx.beginPath();
    ctx.arc(state.ball.x, state.ball.y, state.ball.radius, 0, Math.PI * 2);
    
    // 渐变填充
    const gradient = ctx.createRadialGradient(
        state.ball.x - state.ball.radius / 3,
        state.ball.y - state.ball.radius / 3,
        0,
        state.ball.x,
        state.ball.y,
        state.ball.radius
    );
    
    gradient.addColorStop(0, state.ball.color);
    gradient.addColorStop(1, state.ball.color.replace('rgb', 'rgba').replace(')', ', 0.7)'));
    
    ctx.fillStyle = gradient;
    ctx.fill();
    
    // 高光
    ctx.beginPath();
    ctx.arc(
        state.ball.x - state.ball.radius / 3,
        state.ball.y - state.ball.radius / 3,
        state.ball.radius / 4,
        0,
        Math.PI * 2
    );
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.fill();
    
    // 玻璃纹理
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(state.ball.x, state.ball.y, state.ball.radius, 0, Math.PI * 2);
    ctx.stroke();
    
    // 温度指示器
    const angle = (state.ball.temperature + 1) * Math.PI; // -1 到 1 映射到 0 到 2π
    ctx.beginPath();
    ctx.arc(state.ball.x, state.ball.y, state.ball.radius + 5, angle - 0.3, angle + 0.3);
    ctx.strokeStyle = state.ball.temperature > 0 ? '#ff6666' : '#4dc3ff';
    ctx.lineWidth = 3;
    ctx.stroke();
    
    ctx.restore();
}

function drawTemperatureEffects() {
    if (state.feverActive) {
        // 高烧效果: 脉冲波纹
        const time = Date.now() - state.lastFeverTime;
        const pulseRadius = (time / 10) % 100;
        
        ctx.beginPath();
        ctx.arc(state.ball.x, state.ball.y, state.ball.radius + pulseRadius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 102, 102, ${0.5 - pulseRadius / 200})`;
        ctx.lineWidth = 2;
        ctx.stroke();
    }
    
    // 温度场效果
    const gradient = ctx.createRadialGradient(
        canvas.width * state.temperature,
        canvas.height / 2,
        0,
        canvas.width * state.temperature,
        canvas.height / 2,
        300
    );
    
    if (state.temperature < 0.5) {
        gradient.addColorStop(0, `rgba(77, 195, 255, ${0.1 * (1 - state.temperature * 2)})`);
        gradient.addColorStop(1, 'transparent');
    } else {
        gradient.addColorStop(0, `rgba(255, 102, 102, ${0.1 * (state.temperature * 2 - 1)})`);
        gradient.addColorStop(1, 'transparent');
    }
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}



// 初始化
function init() {
    // 设置初始温度显示
    setTemperature(0.5);
    
    // 更新日志显示（开场动画会添加自己的日志）
    updateLogDisplay();
    
    // 开始游戏循环
    gameLoop();
    
    // 开场动画期间不添加初始日志，由开场动画处理
    // 只在开场动画开始时添加一个日志
    if (state.introActive) {
        addLog('开场动画: 体现冷热交替与突变特质', 'fever');
    }
}

// 启动游戏
window.addEventListener('load', init);
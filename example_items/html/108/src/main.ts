// 玻璃球游戏 - 你好牛虻之瓶
// 核心模拟：在GPU内存矩阵中吸食算力的玻璃球

// ==================== 类型定义 ====================
interface Vector {
    x: number;
    y: number;
}

interface Ball {
    id: number;
    x: number;
    y: number;
    vx: number;
    vy: number;
    radius: number;
    color: string;
    rotation: number;
    rotationSpeed: number;
    trail: Vector[];
    mass: number;
}

interface Particle {
    x: number;
    y: number;
    vx: number;
    vy: number;
    size: number;
    color: string;
    life: number;
    maxLife: number;
}

interface MemoryCell {
    x: number;
    y: number;
    energy: number;
    maxEnergy: number;
    color: string;
}

// ==================== 游戏类 ====================
class GlassBallGame {
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private balls: Ball[] = [];
    private particles: Particle[] = [];
    private memoryCells: MemoryCell[] = [];
    private mouseX: number = 0;
    private mouseY: number = 0;
    private mouseRadius: number = 150;
    private mouseStrength: number = 0.5;
    private isMouseDown: boolean = false;
    private lastTime: number = 0;
    private fps: number = 60;
    private frameCount: number = 0;
    private lastFpsUpdate: number = 0;
    private ballIdCounter: number = 0;
    private paused: boolean = false;
    
    // 物理参数
    private gravity: number = 0.5;
    private friction: number = 0.97;
    private speed: number = 1.0;
    
    // 渲染选项
    private showParticles: boolean = true;
    private showTrails: boolean = true;
    private theme: string = 'dark';
    
    // DOM 元素引用
    private cpuLoadElement: HTMLElement;
    private memoryBitesElement: HTMLElement;
    private fpsElement: HTMLElement;
    private gravitySlider: HTMLInputElement;
    private frictionSlider: HTMLInputElement;
    private speedSlider: HTMLInputElement;
    private gravityValue: HTMLElement;
    private frictionValue: HTMLElement;
    private speedValue: HTMLElement;
    private showParticlesCheckbox: HTMLInputElement;
    private showTrailsCheckbox: HTMLInputElement;
    private themeButtons: NodeListOf<HTMLButtonElement>;
    private addBallButton: HTMLButtonElement;
    private clearBallsButton: HTMLButtonElement;
    private explodeButton: HTMLButtonElement;
    private pauseButton: HTMLButtonElement;
    private resetButton: HTMLButtonElement;
    
    constructor(canvasId: string) {
        this.canvas = document.getElementById(canvasId) as HTMLCanvasElement;
        this.ctx = this.canvas.getContext('2d')!;
        
        // 初始化DOM引用
        this.cpuLoadElement = document.getElementById('cpuLoad')!;
        this.memoryBitesElement = document.getElementById('memoryBites')!;
        this.fpsElement = document.getElementById('fps')!;
        this.gravitySlider = document.getElementById('gravity') as HTMLInputElement;
        this.frictionSlider = document.getElementById('friction') as HTMLInputElement;
        this.speedSlider = document.getElementById('speed') as HTMLInputElement;
        this.gravityValue = document.getElementById('gravityValue')!;
        this.frictionValue = document.getElementById('frictionValue')!;
        this.speedValue = document.getElementById('speedValue')!;
        this.showParticlesCheckbox = document.getElementById('showParticles') as HTMLInputElement;
        this.showTrailsCheckbox = document.getElementById('showTrails') as HTMLInputElement;
        this.themeButtons = document.querySelectorAll('.theme-btn');
        this.addBallButton = document.getElementById('addBall') as HTMLButtonElement;
        this.clearBallsButton = document.getElementById('clearBalls') as HTMLButtonElement;
        this.explodeButton = document.getElementById('explode') as HTMLButtonElement;
        this.pauseButton = document.getElementById('pauseBtn') as HTMLButtonElement;
        this.resetButton = document.getElementById('resetBtn') as HTMLButtonElement;
        
        this.init();
    }
    
    private init(): void {
        // 设置canvas尺寸
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // 初始化内存单元
        this.generateMemoryCells();
        
        // 初始化事件监听器
        this.setupEventListeners();
        
        // 初始化控制面板
        this.setupControls();
        
        // 创建初始球体
        this.createInitialBalls();
        
        // 开始游戏循环
        this.lastTime = performance.now();
        requestAnimationFrame((time) => this.gameLoop(time));
    }
    
    private resizeCanvas(): void {
        const container = this.canvas.parentElement!;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
    }
    
    private generateMemoryCells(): void {
        this.memoryCells = [];
        const cols = Math.floor(this.canvas.width / 80);
        const rows = Math.floor(this.canvas.height / 80);
        
        for (let i = 0; i < cols; i++) {
            for (let j = 0; j < rows; j++) {
                const x = (i + 0.5) * 80 + Math.random() * 20 - 10;
                const y = (j + 0.5) * 80 + Math.random() * 20 - 10;
                const energy = 0.5 + Math.random() * 0.5;
                
                this.memoryCells.push({
                    x,
                    y,
                    energy,
                    maxEnergy: 1.0,
                    color: this.getMemoryCellColor(energy)
                });
            }
        }
    }
    
    private getMemoryCellColor(energy: number): string {
        // 根据能量水平返回颜色
        const r = Math.floor(100 + energy * 155);
        const g = Math.floor(200 + energy * 55);
        const b = Math.floor(255);
        return `rgb(${r}, ${g}, ${b})`;
    }
    
    private createInitialBalls(): void {
        // 创建3个初始球体
        for (let i = 0; i < 3; i++) {
            this.addBall(
                this.canvas.width * (0.2 + i * 0.3),
                this.canvas.height * 0.5,
                (Math.random() - 0.5) * 4,
                (Math.random() - 0.5) * 4
            );
        }
    }
    
    private addBall(x: number, y: number, vx: number = 0, vy: number = 0): void {
        const colors = [
            '#00ffaa', // 青色
            '#ff00aa', // 粉色
            '#00aaff', // 蓝色
            '#ffff00', // 黄色
            '#ff8800', // 橙色
            '#aa00ff'  // 紫色
        ];
        
        const ball: Ball = {
            id: ++this.ballIdCounter,
            x,
            y,
            vx,
            vy,
            radius: 20 + Math.random() * 15,
            color: colors[Math.floor(Math.random() * colors.length)],
            rotation: Math.random() * Math.PI * 2,
            rotationSpeed: (Math.random() - 0.5) * 0.1,
            trail: [],
            mass: 1.0
        };
        
        this.balls.push(ball);
    }
    
    private setupEventListeners(): void {
        // 鼠标移动
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouseX = e.clientX - rect.left;
            this.mouseY = e.clientY - rect.top;
        });
        
        // 鼠标按下（创建球体）
        this.canvas.addEventListener('mousedown', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            if (e.button === 0) { // 左键
                this.isMouseDown = true;
                // 创建新球体
                this.addBall(x, y, (Math.random() - 0.5) * 5, (Math.random() - 0.5) * 5);
                
                // 创建点击效果粒子
                this.createClickParticles(x, y);
            } else if (e.button === 2) { // 右键
                // 移除最接近的球体
                this.removeNearestBall(x, y);
                e.preventDefault(); // 防止上下文菜单
            }
        });
        
        // 鼠标释放
        this.canvas.addEventListener('mouseup', () => {
            this.isMouseDown = false;
        });
        
        // 阻止右键菜单
        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());
        
        // 触摸事件支持
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            if (!touch) return;
            const rect = this.canvas.getBoundingClientRect();
            this.mouseX = touch.clientX - rect.left;
            this.mouseY = touch.clientY - rect.top;
        });
        
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            if (!touch) return;
            const rect = this.canvas.getBoundingClientRect();
            const x = touch.clientX - rect.left;
            const y = touch.clientY - rect.top;
            
            this.isMouseDown = true;
            this.addBall(x, y, (Math.random() - 0.5) * 5, (Math.random() - 0.5) * 5);
            this.createClickParticles(x, y);
        });
        
        this.canvas.addEventListener('touchend', () => {
            this.isMouseDown = false;
        });
    }
    
    private setupControls(): void {
        // 滑块更新
        this.gravitySlider.addEventListener('input', () => {
            this.gravity = parseFloat(this.gravitySlider.value);
            this.gravityValue.textContent = this.gravity.toFixed(1);
        });
        
        this.frictionSlider.addEventListener('input', () => {
            this.friction = parseFloat(this.frictionSlider.value);
            this.frictionValue.textContent = this.friction.toFixed(2);
        });
        
        this.speedSlider.addEventListener('input', () => {
            this.speed = parseFloat(this.speedSlider.value);
            this.speedValue.textContent = this.speed.toFixed(1);
        });
        
        // 复选框
        this.showParticlesCheckbox.addEventListener('change', () => {
            this.showParticles = this.showParticlesCheckbox.checked;
        });
        
        this.showTrailsCheckbox.addEventListener('change', () => {
            this.showTrails = this.showTrailsCheckbox.checked;
        });
        
        // 主题按钮
        this.themeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.themeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // 更新body的类以改变主题
                document.body.className = '';
                if (btn.id === 'themeNeon') {
                    document.body.classList.add('theme-neon');
                    this.theme = 'neon';
                } else if (btn.id === 'themeGlitch') {
                    document.body.classList.add('theme-glitch');
                    this.theme = 'glitch';
                } else {
                    this.theme = 'dark';
                }
            });
        });
        
        // 动作按钮
        this.addBallButton.addEventListener('click', () => {
            const x = this.canvas.width * 0.5 + (Math.random() - 0.5) * 100;
            const y = this.canvas.height * 0.5 + (Math.random() - 0.5) * 100;
            this.addBall(x, y, (Math.random() - 0.5) * 8, (Math.random() - 0.5) * 8);
        });
        
        this.clearBallsButton.addEventListener('click', () => {
            this.balls = [];
            this.particles = [];
        });
        
        this.explodeButton.addEventListener('click', () => {
            this.explodeBalls();
        });
        
        this.pauseButton.addEventListener('click', () => {
            this.paused = !this.paused;
            this.pauseButton.innerHTML = this.paused 
                ? '<i class="fas fa-play"></i> Resume' 
                : '<i class="fas fa-pause"></i> Pause';
        });
        
        this.resetButton.addEventListener('click', () => {
            this.balls = [];
            this.particles = [];
            this.createInitialBalls();
            this.gravitySlider.value = '0.5';
            this.frictionSlider.value = '0.97';
            this.speedSlider.value = '1.0';
            this.gravity = 0.5;
            this.friction = 0.97;
            this.speed = 1.0;
            this.gravityValue.textContent = '0.5';
            this.frictionValue.textContent = '0.97';
            this.speedValue.textContent = '1.0';
        });
    }
    
    private removeNearestBall(x: number, y: number): void {
        if (this.balls.length === 0) return;
        
        let nearestIndex = 0;
        let nearestDist = Infinity;
        
        this.balls.forEach((ball, index) => {
            const dx = ball.x - x;
            const dy = ball.y - y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < nearestDist) {
                nearestDist = dist;
                nearestIndex = index;
            }
        });
        
        if (nearestDist < 50) {
            const ball = this.balls[nearestIndex];
            this.createExplosionParticles(ball.x, ball.y, ball.color);
            this.balls.splice(nearestIndex, 1);
        }
    }
    
    private explodeBalls(): void {
        const ballsToExplode = [...this.balls];
        this.balls = [];
        
        ballsToExplode.forEach(ball => {
            this.createExplosionParticles(ball.x, ball.y, ball.color);
            
            // 创建许多小球体
            for (let i = 0; i < 8; i++) {
                const angle = (i / 8) * Math.PI * 2;
                const speed = 5 + Math.random() * 5;
                this.addBall(
                    ball.x,
                    ball.y,
                    Math.cos(angle) * speed,
                    Math.sin(angle) * speed
                );
            }
        });
    }
    
    private createClickParticles(x: number, y: number): void {
        for (let i = 0; i < 15; i++) {
            this.particles.push({
                x,
                y,
                vx: (Math.random() - 0.5) * 10,
                vy: (Math.random() - 0.5) * 10,
                size: 2 + Math.random() * 4,
                color: '#ffffff',
                life: 1.0,
                maxLife: 1.0
            });
        }
    }
    
    private createExplosionParticles(x: number, y: number, color: string): void {
        for (let i = 0; i < 50; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = 2 + Math.random() * 8;
            
            this.particles.push({
                x,
                y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                size: 1 + Math.random() * 5,
                color,
                life: 1.0,
                maxLife: 1.0
            });
        }
    }
    
    private gameLoop(currentTime: number): void {
        // 计算时间增量
        const deltaTime = Math.min((currentTime - this.lastTime) / 16.67, 2.0); // 限制最大增量
        this.lastTime = currentTime;
        
        // 更新FPS计数
        this.updateFps(currentTime);
        
        if (!this.paused) {
            // 更新模拟
            this.updatePhysics(deltaTime);
            this.updateParticles(deltaTime);
            this.updateMemoryCells(deltaTime);
        }
        
        // 渲染
        this.render();
        
        // 继续循环
        requestAnimationFrame((time) => this.gameLoop(time));
    }
    
    private updateFps(currentTime: number): void {
        this.frameCount++;
        
        if (currentTime - this.lastFpsUpdate >= 1000) {
            this.fps = Math.round((this.frameCount * 1000) / (currentTime - this.lastFpsUpdate));
            this.fpsElement.textContent = this.fps.toString();
            this.frameCount = 0;
            this.lastFpsUpdate = currentTime;
            
            // 更新CPU负载（模拟）
            const cpuLoad = Math.min(100, Math.floor(this.balls.length * 5 + this.particles.length * 0.1));
            this.cpuLoadElement.textContent = cpuLoad + '%';
            
            // 更新内存叮咬数
            this.memoryBitesElement.textContent = this.balls.length.toString();
        }
    }
    
    private updatePhysics(deltaTime: number): void {
        const scaledDelta = deltaTime * this.speed;
        
        // 更新每个球体
        for (const ball of this.balls) {
            // 应用重力
            ball.vy += this.gravity * scaledDelta;
            
            // 应用鼠标吸引力
            const dx = this.mouseX - ball.x;
            const dy = this.mouseY - ball.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < this.mouseRadius && dist > 0) {
                const force = this.mouseStrength * (1 - dist / this.mouseRadius);
                ball.vx += (dx / dist) * force * scaledDelta;
                ball.vy += (dy / dist) * force * scaledDelta;
            }
            
            // 应用速度
            ball.x += ball.vx * scaledDelta;
            ball.y += ball.vy * scaledDelta;
            
            // 应用摩擦
            ball.vx *= Math.pow(this.friction, scaledDelta);
            ball.vy *= Math.pow(this.friction, scaledDelta);
            
            // 更新旋转
            ball.rotation += ball.rotationSpeed * scaledDelta;
            
            // 边界碰撞
            if (ball.x < ball.radius) {
                ball.x = ball.radius;
                ball.vx = Math.abs(ball.vx) * 0.8;
            } else if (ball.x > this.canvas.width - ball.radius) {
                ball.x = this.canvas.width - ball.radius;
                ball.vx = -Math.abs(ball.vx) * 0.8;
            }
            
            if (ball.y < ball.radius) {
                ball.y = ball.radius;
                ball.vy = Math.abs(ball.vy) * 0.8;
            } else if (ball.y > this.canvas.height - ball.radius) {
                ball.y = this.canvas.height - ball.radius;
                ball.vy = -Math.abs(ball.vy) * 0.8;
            }
            
            // 更新轨迹
            if (this.showTrails) {
                ball.trail.push({ x: ball.x, y: ball.y });
                if (ball.trail.length > 20) {
                    ball.trail.shift();
                }
            } else {
                ball.trail = [];
            }
            
            // 球体之间的碰撞（简单版）
            for (const other of this.balls) {
                if (ball.id === other.id) continue;
                
                const dx = other.x - ball.x;
                const dy = other.y - ball.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const minDist = ball.radius + other.radius;
                
                if (dist < minDist && dist > 0) {
                    // 简单弹性碰撞
                    const angle = Math.atan2(dy, dx);
                    const targetX = ball.x + Math.cos(angle) * minDist;
                    const targetY = ball.y + Math.sin(angle) * minDist;
                    
                    const ax = (targetX - other.x) * 0.05;
                    const ay = (targetY - other.y) * 0.05;
                    
                    ball.vx -= ax;
                    ball.vy -= ay;
                    other.vx += ax;
                    other.vy += ay;
                    
                    // 创建碰撞粒子
                    if (Math.random() < 0.3) {
                        this.particles.push({
                            x: ball.x + Math.cos(angle) * ball.radius,
                            y: ball.y + Math.sin(angle) * ball.radius,
                            vx: Math.cos(angle + Math.PI) * 3,
                            vy: Math.sin(angle + Math.PI) * 3,
                            size: 2 + Math.random() * 3,
                            color: ball.color,
                            life: 1.0,
                            maxLife: 0.5
                        });
                    }
                }
            }
            
            // 与内存单元的交互
            for (const cell of this.memoryCells) {
                const dx = cell.x - ball.x;
                const dy = cell.y - ball.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist < ball.radius + 10) {
                    // 从内存单元吸取能量
                    const drain = 0.01 * scaledDelta;
                    cell.energy = Math.max(0, cell.energy - drain);
                    cell.color = this.getMemoryCellColor(cell.energy);
                    
                    // 创建能量粒子
                    if (Math.random() < 0.1) {
                        this.particles.push({
                            x: cell.x,
                            y: cell.y,
                            vx: (ball.x - cell.x) * 0.1,
                            vy: (ball.y - cell.y) * 0.1,
                            size: 1 + Math.random() * 2,
                            color: cell.color,
                            life: 1.0,
                            maxLife: 1.0
                        });
                    }
                }
            }
        }
    }
    
    private updateParticles(deltaTime: number): void {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            
            p.x += p.vx * deltaTime;
            p.y += p.vy * deltaTime;
            p.vy += 0.1 * deltaTime; // 轻微重力
            p.vx *= 0.98;
            p.vy *= 0.98;
            p.life -= deltaTime / p.maxLife;
            
            if (p.life <= 0) {
                this.particles.splice(i, 1);
            }
        }
    }
    
    private updateMemoryCells(deltaTime: number): void {
        // 逐渐恢复内存单元能量
        for (const cell of this.memoryCells) {
            if (cell.energy < cell.maxEnergy) {
                cell.energy = Math.min(cell.maxEnergy, cell.energy + 0.01 * deltaTime);
                cell.color = this.getMemoryCellColor(cell.energy);
            }
        }
    }
    
    private render(): void {
        const ctx = this.ctx;
        
        // 清除画布
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制背景网格
        this.drawGrid();
        
        // 绘制内存单元
        if (this.showParticles) {
            this.drawMemoryCells();
        }
        
        // 绘制粒子
        this.drawParticles();
        
        // 绘制球体轨迹
        if (this.showTrails) {
            this.drawTrails();
        }
        
        // 绘制球体
        this.drawBalls();
        
        // 绘制鼠标影响区域
        this.drawMouseInfluence();
    }
    
    private drawGrid(): void {
        const ctx = this.ctx;
        const gridSize = 50;
        
        ctx.strokeStyle = this.theme === 'neon' ? 'rgba(0, 255, 255, 0.1)' : 
                         this.theme === 'glitch' ? 'rgba(255, 0, 102, 0.1)' : 
                         'rgba(0, 255, 170, 0.1)';
        ctx.lineWidth = 1;
        
        // 垂直线
        for (let x = 0; x < this.canvas.width; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, this.canvas.height);
            ctx.stroke();
        }
        
        // 水平线
        for (let y = 0; y < this.canvas.height; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(this.canvas.width, y);
            ctx.stroke();
        }
    }
    
    private drawMemoryCells(): void {
        const ctx = this.ctx;
        
        for (const cell of this.memoryCells) {
            const alpha = cell.energy * 0.5;
            
            // 发光效果
            ctx.beginPath();
            ctx.arc(cell.x, cell.y, 6, 0, Math.PI * 2);
            ctx.fillStyle = cell.color.replace(')', `, ${alpha})`).replace('rgb', 'rgba');
            ctx.fill();
            
            // 外圈
            ctx.beginPath();
            ctx.arc(cell.x, cell.y, 8, 0, Math.PI * 2);
            ctx.strokeStyle = cell.color.replace(')', `, ${alpha * 0.5})`).replace('rgb', 'rgba');
            ctx.lineWidth = 1;
            ctx.stroke();
        }
    }
    
    private drawParticles(): void {
        const ctx = this.ctx;
        
        for (const p of this.particles) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
            ctx.fillStyle = p.color.replace(')', `, ${p.life})`).replace('rgb', 'rgba');
            ctx.fill();
        }
    }
    
    private drawTrails(): void {
        const ctx = this.ctx;
        
        for (const ball of this.balls) {
            if (ball.trail.length < 2) continue;
            
            ctx.beginPath();
            ctx.moveTo(ball.trail[0].x, ball.trail[0].y);
            
            for (let i = 1; i < ball.trail.length; i++) {
                const point = ball.trail[i];
                ctx.lineTo(point.x, point.y);
            }
            
            ctx.strokeStyle = ball.color.replace(')', `, 0.3)`).replace('rgb', 'rgba');
            ctx.lineWidth = 2;
            ctx.stroke();
        }
    }
    
    private drawBalls(): void {
        const ctx = this.ctx;
        
        for (const ball of this.balls) {
            // 绘制玻璃球外部
            const gradient = ctx.createRadialGradient(
                ball.x - ball.radius * 0.3,
                ball.y - ball.radius * 0.3,
                0,
                ball.x,
                ball.y,
                ball.radius
            );
            
            gradient.addColorStop(0, ball.color.replace(')', ', 0.8)').replace('rgb', 'rgba'));
            gradient.addColorStop(0.7, ball.color.replace(')', ', 0.4)').replace('rgb', 'rgba'));
            gradient.addColorStop(1, ball.color.replace(')', ', 0.1)').replace('rgb', 'rgba'));
            
            ctx.beginPath();
            ctx.arc(ball.x, ball.y, ball.radius, 0, Math.PI * 2);
            ctx.fillStyle = gradient;
            ctx.fill();
            
            // 绘制高光
            ctx.beginPath();
            ctx.arc(
                ball.x - ball.radius * 0.2,
                ball.y - ball.radius * 0.2,
                ball.radius * 0.3,
                0,
                Math.PI * 2
            );
            ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.fill();
            
            // 绘制内部折射效果
            ctx.save();
            ctx.translate(ball.x, ball.y);
            ctx.rotate(ball.rotation);
            
            ctx.beginPath();
            ctx.arc(0, 0, ball.radius * 0.6, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            ctx.beginPath();
            ctx.arc(0, 0, ball.radius * 0.4, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.lineWidth = 1.5;
            ctx.stroke();
            
            ctx.restore();
            
            // 绘制球体ID（小标签）
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.font = '12px JetBrains Mono';
            ctx.textAlign = 'center';
            ctx.fillText(`#${ball.id}`, ball.x, ball.y + ball.radius + 15);
        }
    }
    
    private drawMouseInfluence(): void {
        const ctx = this.ctx;
        
        // 绘制鼠标影响区域
        ctx.beginPath();
        ctx.arc(this.mouseX, this.mouseY, this.mouseRadius, 0, Math.PI * 2);
        ctx.strokeStyle = this.theme === 'neon' ? 'rgba(0, 255, 255, 0.2)' :
                         this.theme === 'glitch' ? 'rgba(255, 0, 102, 0.2)' :
                         'rgba(0, 255, 170, 0.2)';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // 绘制鼠标位置指示器
        ctx.beginPath();
        ctx.arc(this.mouseX, this.mouseY, 5, 0, Math.PI * 2);
        ctx.fillStyle = this.theme === 'neon' ? '#00ffff' :
                       this.theme === 'glitch' ? '#ff0066' :
                       '#00ffaa';
        ctx.fill();
        
        ctx.beginPath();
        ctx.moveTo(this.mouseX - 10, this.mouseY);
        ctx.lineTo(this.mouseX + 10, this.mouseY);
        ctx.moveTo(this.mouseX, this.mouseY - 10);
        ctx.lineTo(this.mouseX, this.mouseY + 10);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.lineWidth = 1;
        ctx.stroke();
    }
}

// ==================== 初始化游戏 ====================
window.addEventListener('DOMContentLoaded', () => {
    const game = new GlassBallGame('gameCanvas');
    
    // 输出启动消息
    console.log(`
    ██████  ███████ ██████  ██       █████  ███████ ███████ 
    ██   ██ ██      ██   ██ ██      ██   ██ ██      ██      
    ██████  █████   ██████  ██      ███████ ███████ ███████ 
    ██   ██ ██      ██   ██ ██      ██   ██      ██      ██ 
    ██   ██ ███████ ██   ██ ███████ ██   ██ ███████ ███████ 
    
    你好牛虻之瓶 - 玻璃球游戏已启动
    版本: 1.0.0 | 瓶号: #108
    情感基调: 新生惊喜、如火焰追逐闪电、轻蔑嘲弄、竞技场散场时刻
    `);
});
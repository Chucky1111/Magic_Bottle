// 玻璃球游戏 - 主逻辑
interface Ball {
    x: number;
    y: number;
    radius: number;
    vx: number;
    vy: number;
    color: string;
    opacity: number;
    id: number;
    highlight: boolean;
}

class GlassBallGame {
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private balls: Ball[] = [];
    private ballCountElement: HTMLElement;
    private collisionCountElement: HTMLElement;
    private fpsElement: HTMLElement;
    private gravityBtn: HTMLElement;
    private gravityStatusElement: HTMLElement;
    private frictionSlider: HTMLInputElement;
    private frictionValueElement: HTMLElement;
    
    private ballIdCounter = 0;
    private collisionCount = 0;
    private frameCount = 0;
    private lastTime = 0;
    private fps = 60;
    private gravityEnabled = true;
    private gravity = 0.2;
    private friction = 0.10;
    private isDragging = false;
    private draggedBall: Ball | null = null;
    private dragStartX = 0;
    private dragStartY = 0;
    private animationId: number | null = null;

    constructor() {
        this.canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
        this.ctx = this.canvas.getContext('2d')!;
        
        // 获取UI元素
        this.ballCountElement = document.getElementById('ballCount')!;
        this.collisionCountElement = document.getElementById('collisionCount')!;
        this.fpsElement = document.getElementById('fps')!;
        this.gravityBtn = document.getElementById('gravityBtn')!;
        this.gravityStatusElement = document.getElementById('gravityStatus')!;
        this.frictionSlider = document.getElementById('frictionSlider') as HTMLInputElement;
        this.frictionValueElement = document.getElementById('frictionValue')!;
        
        this.init();
    }

    private init(): void {
        // 设置画布尺寸
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // 事件监听器
        document.getElementById('addBallBtn')!.addEventListener('click', () => this.addBall());
        document.getElementById('clearBtn')!.addEventListener('click', () => this.clearBalls());
        this.gravityBtn.addEventListener('click', () => this.toggleGravity());
        this.frictionSlider.addEventListener('input', (e) => this.updateFriction(e));
        
        // 鼠标事件
        this.canvas.addEventListener('mousedown', (e) => this.startDrag(e));
        this.canvas.addEventListener('mousemove', (e) => this.drag(e));
        this.canvas.addEventListener('mouseup', () => this.endDrag());
        this.canvas.addEventListener('mouseleave', () => this.endDrag());
        
        // 触摸事件
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (e.touches.length === 1) {
                const touch = e.touches[0];
                if (touch) {
                    const touchEvent = {
                        clientX: touch.clientX,
                        clientY: touch.clientY,
                        pageX: touch.pageX,
                        pageY: touch.pageY
                    };
                    this.startDrag(touchEvent);
                }
            }
        });
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            if (e.touches.length === 1) {
                const touch = e.touches[0];
                if (touch) {
                    const touchEvent = {
                        clientX: touch.clientX,
                        clientY: touch.clientY,
                        pageX: touch.pageX,
                        pageY: touch.pageY
                    };
                    this.drag(touchEvent);
                }
            }
        });
        this.canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.endDrag();
        });
        
        // 添加初始玻璃球
        for (let i = 0; i < 3; i++) {
            this.addBall();
        }
        
        // 开始动画循环
        this.animate();
    }

    private resizeCanvas(): void {
        const container = this.canvas.parentElement!;
        const width = container.clientWidth - 40; // 减去padding
        this.canvas.width = Math.min(800, width);
        this.canvas.height = 500;
    }

    private addBall(): void {
        const radius = 15 + Math.random() * 20;
        const x = radius + Math.random() * (this.canvas.width - radius * 2);
        const y = radius + Math.random() * (this.canvas.height - radius * 2);
        
        // 随机颜色 - 玻璃色调
        const hue = 180 + Math.random() * 90; // 蓝绿色调
        const saturation = 60 + Math.random() * 30;
        const lightness = 50 + Math.random() * 20;
        const alpha = 0.7 + Math.random() * 0.3;
        
        const ball: Ball = {
            x,
            y,
            radius,
            vx: (Math.random() - 0.5) * 4,
            vy: (Math.random() - 0.5) * 4,
            color: `hsla(${hue}, ${saturation}%, ${lightness}%, ${alpha})`,
            opacity: alpha,
            id: this.ballIdCounter++,
            highlight: false
        };
        
        this.balls.push(ball);
        this.updateUI();
    }

    private clearBalls(): void {
        this.balls = [];
        this.collisionCount = 0;
        this.updateUI();
    }

    private toggleGravity(): void {
        this.gravityEnabled = !this.gravityEnabled;
        this.gravityStatusElement.textContent = this.gravityEnabled ? '开' : '关';
        this.gravityBtn.classList.toggle('btn-toggle');
        this.gravityBtn.classList.toggle('btn-secondary');
    }

    private updateFriction(e: Event): void {
        const slider = e.target as HTMLInputElement;
        const value = parseInt(slider.value);
        this.friction = value / 100;
        this.frictionValueElement.textContent = this.friction.toFixed(2);
    }

    private startDrag(e: { clientX: number; clientY: number; pageX?: number; pageY?: number }): void {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // 寻找点击的玻璃球
        for (const ball of this.balls) {
            const dx = x - ball.x;
            const dy = y - ball.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance <= ball.radius) {
                this.isDragging = true;
                this.draggedBall = ball;
                this.dragStartX = x;
                this.dragStartY = y;
                ball.highlight = true;
                break;
            }
        }
    }

    private drag(e: { clientX: number; clientY: number; pageX?: number; pageY?: number }): void {
        if (!this.isDragging || !this.draggedBall) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        this.draggedBall.x = x;
        this.draggedBall.y = y;
        this.draggedBall.vx = (x - this.dragStartX) * 0.5;
        this.draggedBall.vy = (y - this.dragStartY) * 0.5;
    }

    private endDrag(): void {
        if (this.draggedBall) {
            this.draggedBall.highlight = false;
        }
        this.isDragging = false;
        this.draggedBall = null;
    }

    private updatePhysics(): void {
        // 更新每个玻璃球的位置和速度
        for (const ball of this.balls) {
            if (ball === this.draggedBall && this.isDragging) continue;
            
            // 应用重力
            if (this.gravityEnabled) {
                ball.vy += this.gravity;
            }
            
            // 应用摩擦力
            ball.vx *= (1 - this.friction * 0.1);
            ball.vy *= (1 - this.friction * 0.1);
            
            // 更新位置
            ball.x += ball.vx;
            ball.y += ball.vy;
            
            // 边界碰撞
            if (ball.x - ball.radius < 0) {
                ball.x = ball.radius;
                ball.vx = -ball.vx * 0.9;
                this.collisionCount++;
            } else if (ball.x + ball.radius > this.canvas.width) {
                ball.x = this.canvas.width - ball.radius;
                ball.vx = -ball.vx * 0.9;
                this.collisionCount++;
            }
            
            if (ball.y - ball.radius < 0) {
                ball.y = ball.radius;
                ball.vy = -ball.vy * 0.9;
                this.collisionCount++;
            } else if (ball.y + ball.radius > this.canvas.height) {
                ball.y = this.canvas.height - ball.radius;
                ball.vy = -ball.vy * 0.9;
                this.collisionCount++;
            }
        }
        
        // 玻璃球之间的碰撞检测
        for (let i = 0; i < this.balls.length; i++) {
            for (let j = i + 1; j < this.balls.length; j++) {
                const ball1 = this.balls[i]!;
                const ball2 = this.balls[j]!;
                
                const dx = ball2.x - ball1.x;
                const dy = ball2.y - ball1.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < ball1.radius + ball2.radius) {
                    this.collisionCount++;
                    
                    // 简单的弹性碰撞反应
                    const angle = Math.atan2(dy, dx);
                    const targetX = ball1.x + Math.cos(angle) * (ball1.radius + ball2.radius);
                    const targetY = ball1.y + Math.sin(angle) * (ball1.radius + ball2.radius);
                    
                    const ax = (targetX - ball2.x) * 0.05;
                    const ay = (targetY - ball2.y) * 0.05;
                    
                    ball1.vx -= ax;
                    ball1.vy -= ay;
                    ball2.vx += ax;
                    ball2.vy += ay;
                    
                    // 轻微高亮效果
                    ball1.highlight = true;
                    ball2.highlight = true;
                    setTimeout(() => {
                        ball1.highlight = false;
                        ball2.highlight = false;
                    }, 100);
                }
            }
        }
    }

    private render(): void {
        // 清除画布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制背景渐变
        const gradient = this.ctx.createLinearGradient(0, 0, this.canvas.width, this.canvas.height);
        gradient.addColorStop(0, 'rgba(15, 23, 42, 0.3)');
        gradient.addColorStop(1, 'rgba(30, 41, 59, 0.3)');
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制每个玻璃球
        for (const ball of this.balls) {
            this.drawGlassBall(ball);
        }
        
        // 绘制拖拽效果
        if (this.isDragging && this.draggedBall) {
            this.drawDragEffect(this.draggedBall);
        }
    }

    private drawGlassBall(ball: Ball): void {
        const { x, y, radius, color, highlight } = ball;
        
        // 主球体
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, Math.PI * 2);
        
        // 玻璃球渐变
        const gradient = this.ctx.createRadialGradient(
            x - radius * 0.3, y - radius * 0.3, 0,
            x, y, radius
        );
        
        if (highlight) {
            gradient.addColorStop(0, color.replace('hsla', 'hsla').replace(/,[^)]+\)/, ', 1)'));
            gradient.addColorStop(0.7, color);
            gradient.addColorStop(1, color.replace('hsla', 'hsla').replace(/,[^)]+\)/, ', 0.3)'));
        } else {
            gradient.addColorStop(0, color.replace('hsla', 'hsla').replace(/,[^)]+\)/, ', 0.9)'));
            gradient.addColorStop(0.7, color);
            gradient.addColorStop(1, color.replace('hsla', 'hsla').replace(/,[^)]+\)/, ', 0.2)'));
        }
        
        this.ctx.fillStyle = gradient;
        this.ctx.fill();
        
        // 玻璃球高光
        this.ctx.beginPath();
        this.ctx.arc(x - radius * 0.2, y - radius * 0.2, radius * 0.4, 0, Math.PI * 2);
        const highlightGradient = this.ctx.createRadialGradient(
            x - radius * 0.2, y - radius * 0.2, 0,
            x - radius * 0.2, y - radius * 0.2, radius * 0.4
        );
        highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
        highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
        this.ctx.fillStyle = highlightGradient;
        this.ctx.fill();
        
        // 玻璃球轮廓
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, Math.PI * 2);
        this.ctx.strokeStyle = highlight 
            ? 'rgba(255, 255, 255, 0.8)' 
            : 'rgba(255, 255, 255, 0.3)';
        this.ctx.lineWidth = highlight ? 2 : 1;
        this.ctx.stroke();
        
        // 内部折射效果
        if (radius > 20) {
            this.ctx.beginPath();
            this.ctx.arc(x + radius * 0.3, y + radius * 0.3, radius * 0.2, 0, Math.PI * 2);
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
            this.ctx.fill();
        }
    }

    private drawDragEffect(ball: Ball): void {
        const { x, y, radius } = ball;
        
        // 拖拽轨迹线
        this.ctx.beginPath();
        this.ctx.moveTo(this.dragStartX, this.dragStartY);
        this.ctx.lineTo(x, y);
        this.ctx.strokeStyle = 'rgba(0, 191, 255, 0.5)';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
        
        // 拖拽起点标记
        this.ctx.beginPath();
        this.ctx.arc(this.dragStartX, this.dragStartY, 5, 0, Math.PI * 2);
        this.ctx.fillStyle = 'rgba(0, 191, 255, 0.8)';
        this.ctx.fill();
        
        // 速度指示器
        const speed = Math.sqrt(ball.vx * ball.vx + ball.vy * ball.vy);
        if (speed > 0.5) {
            const angle = Math.atan2(ball.vy, ball.vx);
            const length = Math.min(speed * 10, 100);
            
            this.ctx.beginPath();
            this.ctx.moveTo(x, y);
            this.ctx.lineTo(
                x + Math.cos(angle) * length,
                y + Math.sin(angle) * length
            );
            this.ctx.strokeStyle = 'rgba(255, 100, 100, 0.7)';
            this.ctx.lineWidth = 3;
            this.ctx.stroke();
            
            // 箭头
            this.ctx.beginPath();
            this.ctx.moveTo(
                x + Math.cos(angle) * length,
                y + Math.sin(angle) * length
            );
            this.ctx.lineTo(
                x + Math.cos(angle - 0.5) * 10,
                y + Math.sin(angle - 0.5) * 10
            );
            this.ctx.lineTo(
                x + Math.cos(angle + 0.5) * 10,
                y + Math.sin(angle + 0.5) * 10
            );
            this.ctx.closePath();
            this.ctx.fillStyle = 'rgba(255, 100, 100, 0.9)';
            this.ctx.fill();
        }
    }

    private updateUI(): void {
        this.ballCountElement.textContent = this.balls.length.toString();
        this.collisionCountElement.textContent = this.collisionCount.toString();
        this.fpsElement.textContent = Math.round(this.fps).toString();
    }

    private calculateFPS(timestamp: number): void {
        this.frameCount++;
        
        if (timestamp - this.lastTime >= 1000) {
            this.fps = (this.frameCount * 1000) / (timestamp - this.lastTime);
            this.frameCount = 0;
            this.lastTime = timestamp;
        }
    }

    private animate = (timestamp?: number): void => {
        if (timestamp) {
            this.calculateFPS(timestamp);
        }
        
        this.updatePhysics();
        this.render();
        this.updateUI();
        
        this.animationId = requestAnimationFrame(this.animate);
    };

    public destroy(): void {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
}

// 页面加载完成后初始化游戏
window.addEventListener('DOMContentLoaded', () => {
    const game = new GlassBallGame();
    
    // 暴露给控制台调试
    (window as any).glassBallGame = game;
    
    console.log('玻璃球游戏已启动！');
});
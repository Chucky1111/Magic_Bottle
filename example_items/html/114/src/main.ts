// 万分寻常之瓶 - 玻璃球游戏
// 没什么特别的，就是几个球撞来撞去

interface Ball {
  x: number;
  y: number;
  radius: number;
  color: string;
  dx: number;
  dy: number;
  emotion: string;
  id: number;
}

class GlassBallGame {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private balls: Ball[] = [];
  private nextBallId = 0;
  private isDragging = false;
  private dragBall: Ball | null = null;
  private dragOffsetX = 0;
  private dragOffsetY = 0;
  private currentEmotion = '寻常';
  private emotionDisplay: HTMLElement;
  private emotionTimeout: number | null = null;
  
  // 情绪颜色映射
  private emotionColors: Record<string, string> = {
    surprise: '#ffeb3b',
    chase: '#ff9800',
    mock: '#9c27b0',
    ending: '#795548',
    normal: '#42a5f5'
  };
  
  // 情绪名称映射
  private emotionNames: Record<string, string> = {
    surprise: '初生的惊喜',
    chase: '如火焰一般追逐闪电',
    mock: '轻蔑的嘲弄',
    ending: '竞技场的散场时刻',
    normal: '寻常'
  };

  constructor() {
    this.canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
    this.ctx = this.canvas.getContext('2d')!;
    this.emotionDisplay = document.getElementById('currentEmotion')!;
    
    this.init();
    this.setupEventListeners();
    this.createInitialBalls();
    this.animate();
  }

  private init() {
    // 设置画布尺寸
    this.canvas.width = 800;
    this.canvas.height = 500;
  }

  private setupEventListeners() {
    // 鼠标事件
    this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
    this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
    this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
    
    // 触摸事件
    this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this));
    this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this));
    this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this));
    
    // 按钮事件
    document.getElementById('addBallBtn')!.addEventListener('click', () => this.addRandomBall());
    document.getElementById('clearBtn')!.addEventListener('click', () => this.clearBalls());
    
    // 情绪药水点击
    document.querySelectorAll('.potion').forEach(potion => {
      potion.addEventListener('click', (e) => {
        const emotion = (e.currentTarget as HTMLElement).dataset.emotion!;
        this.applyEmotionEffect(emotion);
      });
    });
  }

  private createInitialBalls() {
    // 创建几个初始球，没什么特别的
    this.addBall(200, 150, 30, this.emotionColors.normal, 'normal');
    this.addBall(400, 250, 35, this.emotionColors.normal, 'normal');
    this.addBall(600, 200, 25, this.emotionColors.normal, 'normal');
  }

  private addBall(x: number, y: number, radius: number, color: string, emotion: string) {
    this.balls.push({
      x,
      y,
      radius,
      color,
      dx: (Math.random() - 0.5) * 2,
      dy: (Math.random() - 0.5) * 2,
      emotion,
      id: this.nextBallId++
    });
  }

  private addRandomBall() {
    const radius = 20 + Math.random() * 25;
    const x = radius + Math.random() * (this.canvas.width - 2 * radius);
    const y = radius + Math.random() * (this.canvas.height - 2 * radius);
    const color = this.getRandomColor();
    
    this.addBall(x, y, radius, color, 'normal');
    
    // 轻微的情绪变化
    this.setEmotion('寻常', 1000);
  }

  private clearBalls() {
    this.balls = [];
    this.setEmotion('空无', 2000);
  }

  private getRandomColor(): string {
    const colors = [
      '#42a5f5', '#66bb6a', '#ffa726', '#ab47bc', 
      '#26c6da', '#78909c', '#8d6e63', '#bdbdbd'
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  }

  private handleMouseDown(e: MouseEvent) {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    this.startDrag(x, y);
  }

  private handleMouseMove(e: MouseEvent) {
    if (!this.isDragging) return;
    
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    this.dragBall!.x = x - this.dragOffsetX;
    this.dragBall!.y = y - this.dragOffsetY;
  }

  private handleMouseUp() {
    this.isDragging = false;
    this.dragBall = null;
  }

  private handleTouchStart(e: TouchEvent) {
    e.preventDefault();
    const rect = this.canvas.getBoundingClientRect();
    const touch = e.touches[0];
    const x = touch.clientX - rect.left;
    const y = touch.clientY - rect.top;
    
    this.startDrag(x, y);
  }

  private handleTouchMove(e: TouchEvent) {
    if (!this.isDragging) return;
    e.preventDefault();
    
    const rect = this.canvas.getBoundingClientRect();
    const touch = e.touches[0];
    const x = touch.clientX - rect.left;
    const y = touch.clientY - rect.top;
    
    this.dragBall!.x = x - this.dragOffsetX;
    this.dragBall!.y = y - this.dragOffsetY;
  }

  private handleTouchEnd() {
    this.isDragging = false;
    this.dragBall = null;
  }

  private startDrag(x: number, y: number) {
    for (let i = this.balls.length - 1; i >= 0; i--) {
      const ball = this.balls[i];
      const distance = Math.sqrt((x - ball.x) ** 2 + (y - ball.y) ** 2);
      
      if (distance <= ball.radius) {
        this.isDragging = true;
        this.dragBall = ball;
        this.dragOffsetX = x - ball.x;
        this.dragOffsetY = y - ball.y;
        
        // 拖动时改变颜色，但也就那样
        ball.color = '#ff7043';
        this.setEmotion('拖动中', 500);
        break;
      }
    }
  }

  private update() {
    // 更新球的位置
    for (const ball of this.balls) {
      if (this.isDragging && ball === this.dragBall) {
        continue; // 被拖动的球不受物理影响
      }
      
      // 边界碰撞
      if (ball.x - ball.radius < 0 || ball.x + ball.radius > this.canvas.width) {
        ball.dx *= -0.95; // 有点能量损失
        ball.x = Math.max(ball.radius, Math.min(this.canvas.width - ball.radius, ball.x));
      }
      
      if (ball.y - ball.radius < 0 || ball.y + ball.radius > this.canvas.height) {
        ball.dy *= -0.95;
        ball.y = Math.max(ball.radius, Math.min(this.canvas.height - ball.radius, ball.y));
      }
      
      // 移动
      ball.x += ball.dx;
      ball.y += ball.dy;
      
      // 轻微减速
      ball.dx *= 0.995;
      ball.dy *= 0.995;
    }
    
    // 球之间碰撞
    this.handleCollisions();
  }

  private handleCollisions() {
    for (let i = 0; i < this.balls.length; i++) {
      for (let j = i + 1; j < this.balls.length; j++) {
        const ball1 = this.balls[i];
        const ball2 = this.balls[j];
        
        const dx = ball2.x - ball1.x;
        const dy = ball2.y - ball1.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance < ball1.radius + ball2.radius) {
          // 碰撞发生
          this.resolveCollision(ball1, ball2);
          
          // 随机触发情绪效果
          if (Math.random() < 0.3) {
            const emotions = ['surprise', 'chase', 'mock', 'ending'];
            const emotion = emotions[Math.floor(Math.random() * emotions.length)];
            this.applyEmotionEffect(emotion, 1500);
          }
        }
      }
    }
  }

  private resolveCollision(ball1: Ball, ball2: Ball) {
    // 简单的弹性碰撞
    const dx = ball2.x - ball1.x;
    const dy = ball2.y - ball1.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    if (distance === 0) return;
    
    const nx = dx / distance;
    const ny = dy / distance;
    
    const dvx = ball2.dx - ball1.dx;
    const dvy = ball2.dy - ball1.dy;
    const speed = dvx * nx + dvy * ny;
    
    if (speed > 0) return; // 已经在分离
    
    const impulse = 2 * speed / (1 + 1); // 假设质量相同
    ball1.dx += impulse * nx;
    ball1.dy += impulse * ny;
    ball2.dx -= impulse * nx;
    ball2.dy -= impulse * ny;
    
    // 分开它们防止重叠
    const overlap = ball1.radius + ball2.radius - distance;
    const separateX = overlap * nx * 0.5;
    const separateY = overlap * ny * 0.5;
    
    ball1.x -= separateX;
    ball1.y -= separateY;
    ball2.x += separateX;
    ball2.y += separateY;
  }

  private applyEmotionEffect(emotion: string, duration = 2000) {
    this.setEmotion(this.emotionNames[emotion], duration);
    
    // 改变球的颜色
    const emotionColor = this.emotionColors[emotion];
    for (const ball of this.balls) {
      const originalColor = ball.color;
      ball.color = emotionColor;
      
      setTimeout(() => {
        if (ball.color === emotionColor) {
          ball.color = this.emotionColors.normal;
        }
      }, duration);
    }
    
    // 添加CSS类到body
    document.body.classList.remove('emotion-surprise', 'emotion-chase', 'emotion-mock', 'emotion-ending');
    document.body.classList.add(`emotion-${emotion}`);
    
    setTimeout(() => {
      document.body.classList.remove(`emotion-${emotion}`);
    }, duration);
  }

  private setEmotion(emotion: string, duration = 3000) {
    this.currentEmotion = emotion;
    this.emotionDisplay.textContent = emotion;
    
    if (this.emotionTimeout) {
      clearTimeout(this.emotionTimeout);
    }
    
    this.emotionTimeout = setTimeout(() => {
      this.currentEmotion = '寻常';
      this.emotionDisplay.textContent = '寻常';
    }, duration) as unknown as number;
  }

  private draw() {
    // 清空画布
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    // 绘制网格背景
    this.drawGrid();
    
    // 绘制球
    for (const ball of this.balls) {
      this.drawBall(ball);
    }
  }

  private drawGrid() {
    this.ctx.strokeStyle = '#e0e0e0';
    this.ctx.lineWidth = 0.5;
    
    const gridSize = 40;
    
    // 垂直线
    for (let x = 0; x <= this.canvas.width; x += gridSize) {
      this.ctx.beginPath();
      this.ctx.moveTo(x, 0);
      this.ctx.lineTo(x, this.canvas.height);
      this.ctx.stroke();
    }
    
    // 水平线
    for (let y = 0; y <= this.canvas.height; y += gridSize) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(this.canvas.width, y);
      this.ctx.stroke();
    }
  }

  private drawBall(ball: Ball) {
    // 球体
    this.ctx.beginPath();
    this.ctx.arc(ball.x, ball.y, ball.radius, 0, Math.PI * 2);
    this.ctx.fillStyle = ball.color;
    this.ctx.fill();
    
    // 高光
    this.ctx.beginPath();
    this.ctx.arc(ball.x - ball.radius * 0.3, ball.y - ball.radius * 0.3, ball.radius * 0.4, 0, Math.PI * 2);
    this.ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    this.ctx.fill();
    
    // 边框
    this.ctx.beginPath();
    this.ctx.arc(ball.x, ball.y, ball.radius, 0, Math.PI * 2);
    this.ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
    this.ctx.lineWidth = 2;
    this.ctx.stroke();
    
    // 情绪标记
    if (ball.emotion !== 'normal') {
      this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
      this.ctx.font = '12px Noto Sans SC';
      this.ctx.textAlign = 'center';
      this.ctx.fillText(ball.emotion.charAt(0).toUpperCase(), ball.x, ball.y + 4);
    }
  }

  private animate = () => {
    this.update();
    this.draw();
    requestAnimationFrame(this.animate);
  }
}

// 启动游戏
new GlassBallGame();
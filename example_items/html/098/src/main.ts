import { GlassBall } from './glassball.ts';
import { FluidSimulator } from './fluid.ts';

// 哲学语句库
const PHILOSOPHIES = [
    "光滑的表面之下，永恒涌动着无法净化的混沌。这便是存在的本质。",
    "我们竭力维持的秩序，其下永远是涌动的不洁与混沌。",
    "接受混沌，不是放弃，而是对真实更深层的拥抱。",
    "万物内核皆不可洗涤，唯有在裂痕中，真实得以窥见。",
    "纯洁是表象，污浊是本质。表象易碎，本质永恒。",
    "在表面的透明中，我们迷失；在内里的浑浊中，我们找到自己。",
    "裂纹不是缺陷，而是通向真实的门户。",
    "流动的混沌中，蕴藏着维持一切运转的原始动力。",
    "试图净化内在，不过是在光滑表面上徒劳地雕刻。",
    "最深处的污浊，恰是最深处的真实。"
];

class Game {
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private glassBall: GlassBall;
    private fluidSimulator: FluidSimulator;
    private lastTime: number = 0;
    private isRunning: boolean = true;
    
    // UI元素
    private viscositySlider: HTMLInputElement;
    private chaosSlider: HTMLInputElement;
    private resetButton: HTMLButtonElement;
    private crackButton: HTMLButtonElement;
    private pressureElement: HTMLElement;
    private crackCountElement: HTMLElement;
    private contaminationElement: HTMLElement;
    private philosophyText: HTMLElement;
    private nextPhilosophyButton: HTMLButtonElement;
    
    private crackCount: number = 0;
    private contamination: number = 0;
    
    constructor() {
        this.canvas = document.getElementById('game-canvas') as HTMLCanvasElement;
        this.ctx = this.canvas.getContext('2d')!;
        
        // 初始化玻璃球和流体模拟
        this.glassBall = new GlassBall(this.canvas.width / 2, this.canvas.height / 2, 200);
        this.fluidSimulator = new FluidSimulator(100, 100);
        
        // 获取UI元素
        this.viscositySlider = document.getElementById('viscosity') as HTMLInputElement;
        this.chaosSlider = document.getElementById('chaos') as HTMLInputElement;
        this.resetButton = document.getElementById('reset-btn') as HTMLButtonElement;
        this.crackButton = document.getElementById('crack-btn') as HTMLButtonElement;
        this.pressureElement = document.getElementById('pressure')!;
        this.crackCountElement = document.getElementById('crack-count')!;
        this.contaminationElement = document.getElementById('contamination')!;
        this.philosophyText = document.getElementById('philosophy-text')!;
        this.nextPhilosophyButton = document.getElementById('next-philosophy') as HTMLButtonElement;
        
        this.setupEventListeners();
        this.updateUIValues();
        this.setRandomPhilosophy();
        
        // 启动游戏循环
        requestAnimationFrame(this.gameLoop.bind(this));
    }
    
    private setupEventListeners(): void {
        // 滑块事件
        this.viscositySlider.addEventListener('input', () => {
            const value = parseFloat(this.viscositySlider.value);
            this.fluidSimulator.setViscosity(value);
            document.getElementById('viscosity-value')!.textContent = value.toFixed(1);
        });
        
        this.chaosSlider.addEventListener('input', () => {
            const value = parseFloat(this.chaosSlider.value);
            this.fluidSimulator.setChaos(value);
            document.getElementById('chaos-value')!.textContent = value.toFixed(1);
        });
        
        // 按钮事件
        this.resetButton.addEventListener('click', () => {
            this.glassBall.reset();
            this.crackCount = 0;
            this.contamination = 0;
            this.updateStats();
        });
        
        this.crackButton.addEventListener('click', () => {
            this.glassBall.addCrack();
            this.crackCount++;
            this.updateStats();
        });
        
        // 哲学语句切换
        this.nextPhilosophyButton.addEventListener('click', () => {
            this.setRandomPhilosophy();
        });
        
        // 画布交互
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', () => this.handleMouseUp());
        
        // 触摸屏支持
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (e.touches && e.touches.length > 0) {
                const touch = e.touches[0];
                if (touch) {
                    this.handleMouseDown(touch);
                }
            }
        });
        
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            if (e.touches && e.touches.length > 0) {
                const touch = e.touches[0];
                if (touch) {
                    this.handleMouseMove(touch);
                }
            }
        });
        
        this.canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.handleMouseUp();
        });
    }
    
    private handleMouseDown(event: MouseEvent | Touch): void {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        this.glassBall.startInteraction(x, y);
    }
    
    private handleMouseMove(event: MouseEvent | Touch): void {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        this.glassBall.updateInteraction(x, y);
    }
    
    private handleMouseUp(): void {
        this.glassBall.endInteraction();
    }
    
    private updateUIValues(): void {
        document.getElementById('viscosity-value')!.textContent = this.viscositySlider.value;
        document.getElementById('chaos-value')!.textContent = this.chaosSlider.value;
    }
    
    private updateStats(): void {
        // 模拟内部压力（基于流体活动）
        const pressure = this.fluidSimulator.getPressure();
        this.pressureElement.textContent = pressure.toFixed(2);
        
        this.crackCountElement.textContent = this.crackCount.toString();
        
        // 污染程度随裂纹增加
        this.contamination = Math.min(100, this.crackCount * 5 + pressure * 10);
        this.contaminationElement.textContent = `${Math.round(this.contamination)}%`;
    }
    
    private setRandomPhilosophy(): void {
        const randomIndex = Math.floor(Math.random() * PHILOSOPHIES.length);
        const text = PHILOSOPHIES[randomIndex];
        if (text) {
            this.philosophyText.textContent = text;
        }
    }
    
    private gameLoop(currentTime: number): void {
        if (!this.isRunning) return;
        
        const deltaTime = this.lastTime ? (currentTime - this.lastTime) / 1000 : 0.016;
        this.lastTime = currentTime;
        
        // 更新流体模拟
        this.fluidSimulator.update(deltaTime);
        
        // 更新玻璃球状态
        this.glassBall.update(deltaTime, this.fluidSimulator.getFlowField());
        
        // 渲染
        this.render();
        
        // 更新统计数据
        this.updateStats();
        
        // 继续循环
        requestAnimationFrame(this.gameLoop.bind(this));
    }
    
    private render(): void {
        // 清除画布
        this.ctx.fillStyle = '#1a1a1a';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制流体背景效果
        this.drawFluidBackground();
        
        // 绘制玻璃球
        this.glassBall.draw(this.ctx);
        
        // 绘制裂纹
        this.glassBall.drawCracks(this.ctx);
        
        // 绘制流体内部
        this.drawFluidInsideBall();
    }
    
    private drawFluidBackground(): void {
        const flowField = this.fluidSimulator.getFlowField();
        if (!flowField || flowField.length === 0 || !flowField[0] || flowField[0].length === 0) return;
        
        const cellWidth = this.canvas.width / flowField.length;
        const cellHeight = this.canvas.height / flowField[0].length;
        
        this.ctx.globalAlpha = 0.1;
        for (let i = 0; i < flowField.length; i++) {
            const column = flowField[i];
            if (!column) continue;
            
            for (let j = 0; j < column.length; j++) {
                const flow = column[j];
                if (!flow) continue;
                
                const intensity = Math.sqrt(flow.x * flow.x + flow.y * flow.y);
                
                this.ctx.fillStyle = `rgba(90, 40, 40, ${intensity * 0.5})`;
                this.ctx.fillRect(i * cellWidth, j * cellHeight, cellWidth, cellHeight);
            }
        }
        this.ctx.globalAlpha = 1.0;
    }
    
    private drawFluidInsideBall(): void {
        const ballX = this.glassBall.x;
        const ballY = this.glassBall.y;
        const radius = this.glassBall.radius;
        
        // 创建剪裁区域，只绘制球内部分
        this.ctx.save();
        this.ctx.beginPath();
        this.ctx.arc(ballX, ballY, radius, 0, Math.PI * 2);
        this.ctx.clip();
        
        const flowField = this.fluidSimulator.getFlowField();
        if (!flowField || flowField.length === 0 || !flowField[0] || flowField[0].length === 0) {
            this.ctx.restore();
            return;
        }
        
        const cellWidth = this.canvas.width / flowField.length;
        const cellHeight = this.canvas.height / flowField[0].length;
        
        for (let i = 0; i < flowField.length; i++) {
            const column = flowField[i];
            if (!column) continue;
            
            for (let j = 0; j < column.length; j++) {
                const flow = column[j];
                if (!flow) continue;
                
                const intensity = Math.sqrt(flow.x * flow.x + flow.y * flow.y);
                
                // 计算颜色基于流动强度
                const red = 90 + intensity * 50;
                const green = 40 + intensity * 20;
                const blue = 40 + intensity * 10;
                
                this.ctx.fillStyle = `rgba(${red}, ${green}, ${blue}, ${0.3 + intensity * 0.7})`;
                this.ctx.fillRect(i * cellWidth, j * cellHeight, cellWidth, cellHeight);
                
                // 绘制流动方向线
                if (intensity > 0.3 && Math.random() < 0.1) {
                    const centerX = i * cellWidth + cellWidth / 2;
                    const centerY = j * cellHeight + cellHeight / 2;
                    
                    this.ctx.strokeStyle = `rgba(140, 70, 70, ${intensity})`;
                    this.ctx.lineWidth = 1;
                    this.ctx.beginPath();
                    this.ctx.moveTo(centerX, centerY);
                    this.ctx.lineTo(centerX + flow.x * 10, centerY + flow.y * 10);
                    this.ctx.stroke();
                }
            }
        }
        
        this.ctx.restore();
    }
}

// 页面加载完成后初始化游戏
window.addEventListener('DOMContentLoaded', () => {
    new Game();
});

// 导出类型
export { Game };
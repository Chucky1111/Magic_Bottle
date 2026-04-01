export interface Crack {
    x: number;
    y: number;
    length: number;
    angle: number;
    width: number;
}

export interface FlowField {
    x: number;
    y: number;
}

export class GlassBall {
    public x: number;
    public y: number;
    public radius: number;
    
    private cracks: Crack[] = [];
    private rotation: number = 0;
    private rotationSpeed: number = 0;
    private interactionStart: { x: number, y: number } | null = null;
    private interactionAngle: number = 0;
    private isInteracting: boolean = false;
    
    constructor(x: number, y: number, radius: number) {
        this.x = x;
        this.y = y;
        this.radius = radius;
        
        // 初始添加一些微裂纹
        for (let i = 0; i < 3; i++) {
            this.addMicroCrack();
        }
    }
    
    reset(): void {
        this.cracks = [];
        this.rotation = 0;
        this.rotationSpeed = 0;
        
        // 重新添加微裂纹
        for (let i = 0; i < 3; i++) {
            this.addMicroCrack();
        }
    }
    
    addCrack(): void {
        // 随机位置（在球体内）
        const angle = Math.random() * Math.PI * 2;
        const distance = Math.random() * this.radius * 0.7;
        const x = this.x + Math.cos(angle) * distance;
        const y = this.y + Math.sin(angle) * distance;
        
        // 随机长度和角度
        const length = 20 + Math.random() * 60;
        const crackAngle = angle + (Math.random() - 0.5) * Math.PI * 0.5;
        const width = 1 + Math.random() * 3;
        
        this.cracks.push({ x, y, length, angle: crackAngle, width });
    }
    
    private addMicroCrack(): void {
        const angle = Math.random() * Math.PI * 2;
        const distance = Math.random() * this.radius * 0.8;
        const x = this.x + Math.cos(angle) * distance;
        const y = this.y + Math.sin(angle) * distance;
        
        const length = 5 + Math.random() * 15;
        const crackAngle = angle + (Math.random() - 0.5) * Math.PI * 0.3;
        const width = 0.5 + Math.random() * 1;
        
        this.cracks.push({ x, y, length, angle: crackAngle, width });
    }
    
    startInteraction(x: number, y: number): void {
        const distance = Math.sqrt((x - this.x) ** 2 + (y - this.y) ** 2);
        if (distance <= this.radius) {
            this.interactionStart = { x, y };
            this.isInteracting = true;
            this.interactionAngle = Math.atan2(y - this.y, x - this.x);
        }
    }
    
    updateInteraction(x: number, y: number): void {
        if (!this.isInteracting || !this.interactionStart) return;
        
        const currentAngle = Math.atan2(y - this.y, x - this.x);
        const angleDiff = currentAngle - this.interactionAngle;
        
        // 根据拖动调整旋转速度
        this.rotationSpeed = angleDiff * 5;
        this.interactionAngle = currentAngle;
        
        // 更新交互起点
        this.interactionStart = { x, y };
    }
    
    endInteraction(): void {
        this.isInteracting = false;
        this.interactionStart = null;
    }
    
    update(deltaTime: number, flowField: FlowField[][]): void {
        // 更新旋转
        this.rotation += this.rotationSpeed * deltaTime;
        this.rotationSpeed *= 0.95; // 阻尼
        
        // 流动场对旋转的影响
        if (flowField && flowField.length > 0 && flowField[0] && flowField[0].length > 0) {
            const cellX = Math.floor(this.x / (800 / flowField.length));
            const cellY = Math.floor(this.y / (600 / flowField[0].length));
            
            if (cellX >= 0 && cellX < flowField.length) {
                const column = flowField[cellX];
                if (column && cellY >= 0 && cellY < column.length) {
                    const flow = column[cellY];
                    if (flow) {
                        // 流动影响旋转速度
                        this.rotationSpeed += (flow.x * 0.1) * deltaTime;
                    }
                }
            }
        }
        
        // 随机添加微裂纹的概率
        if (Math.random() < 0.001 * deltaTime * 60) {
            this.addMicroCrack();
        }
    }
    
    draw(ctx: CanvasRenderingContext2D): void {
        // 绘制玻璃球外轮廓
        ctx.save();
        
        // 球体渐变填充
        const gradient = ctx.createRadialGradient(
            this.x, this.y, 0,
            this.x, this.y, this.radius
        );
        gradient.addColorStop(0, 'rgba(255, 255, 255, 0.1)');
        gradient.addColorStop(0.3, 'rgba(200, 200, 200, 0.05)');
        gradient.addColorStop(1, 'rgba(150, 150, 150, 0.01)');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        
        // 球体边框
        ctx.strokeStyle = 'rgba(200, 200, 200, 0.3)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.stroke();
        
        // 高光效果
        const highlightGradient = ctx.createRadialGradient(
            this.x - this.radius * 0.3, this.y - this.radius * 0.3, 0,
            this.x - this.radius * 0.3, this.y - this.radius * 0.3, this.radius * 0.5
        );
        highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.3)');
        highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
        
        ctx.fillStyle = highlightGradient;
        ctx.beginPath();
        ctx.arc(this.x - this.radius * 0.2, this.y - this.radius * 0.2, this.radius * 0.4, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
    }
    
    drawCracks(ctx: CanvasRenderingContext2D): void {
        ctx.save();
        
        for (const crack of this.cracks) {
            // 裂纹颜色（从深红到褐黑）
            const age = crack.width / 3; // 模拟"老化"
            const red = 60 + age * 30;
            const green = 30 + age * 10;
            const blue = 30 + age * 5;
            
            ctx.strokeStyle = `rgba(${red}, ${green}, ${blue}, ${0.3 + age * 0.2})`;
            ctx.lineWidth = crack.width;
            ctx.lineCap = 'round';
            
            ctx.beginPath();
            ctx.moveTo(crack.x, crack.y);
            ctx.lineTo(
                crack.x + Math.cos(crack.angle) * crack.length,
                crack.y + Math.sin(crack.angle) * crack.length
            );
            ctx.stroke();
            
            // 裂纹末端的分支
            if (crack.length > 30 && Math.random() < 0.5) {
                const branchAngle = crack.angle + (Math.random() - 0.5) * Math.PI * 0.7;
                const branchLength = crack.length * (0.3 + Math.random() * 0.4);
                
                ctx.beginPath();
                ctx.moveTo(crack.x, crack.y);
                ctx.lineTo(
                    crack.x + Math.cos(branchAngle) * branchLength,
                    crack.y + Math.sin(branchAngle) * branchLength
                );
                ctx.stroke();
            }
        }
        
        ctx.restore();
    }
    
    getCrackCount(): number {
        return this.cracks.length;
    }
}
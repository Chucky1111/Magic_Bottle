export interface FlowVector {
    x: number;
    y: number;
}

export class FluidSimulator {
    private width: number;
    private height: number;
    private flowField: FlowVector[][];
    private viscosity: number = 1.5;
    private chaos: number = 3.0;
    private time: number = 0;
    
    constructor(width: number, height: number) {
        this.width = width;
        this.height = height;
        this.flowField = this.createFlowField();
        this.initializeField();
    }
    
    private createFlowField(): FlowVector[][] {
        const field: FlowVector[][] = [];
        for (let x = 0; x < this.width; x++) {
            const column: FlowVector[] = [];
            for (let y = 0; y < this.height; y++) {
                column.push({ x: 0, y: 0 });
            }
            field.push(column);
        }
        return field;
    }
    
    private initializeField(): void {
        // 创建初始涡流
        const vortexCount = 5;
        for (let i = 0; i < vortexCount; i++) {
            const vortexX = Math.random() * this.width;
            const vortexY = Math.random() * this.height;
            const strength = 2 + Math.random() * 3;
            const radius = 10 + Math.random() * 15;
            
            this.addVortex(vortexX, vortexY, strength, radius);
        }
        
        // 添加一些随机流动
        for (let x = 0; x < this.width; x++) {
            const column = this.flowField[x];
            if (!column) continue;
            
            for (let y = 0; y < this.height; y++) {
                const cell = column[y];
                if (!cell) continue;
                
                cell.x += (Math.random() - 0.5) * 0.5;
                cell.y += (Math.random() - 0.5) * 0.5;
            }
        }
    }
    
    private addVortex(centerX: number, centerY: number, strength: number, radius: number): void {
        for (let x = 0; x < this.width; x++) {
            const column = this.flowField[x];
            if (!column) continue;
            
            for (let y = 0; y < this.height; y++) {
                const cell = column[y];
                if (!cell) continue;
                
                const dx = x - centerX;
                const dy = y - centerY;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < radius && distance > 0) {
                    // 涡流速度与距离成反比
                    const force = strength * (1 - distance / radius);
                    // 垂直方向向量（产生旋转）
                    const vx = -dy / distance;
                    const vy = dx / distance;
                    
                    cell.x += vx * force;
                    cell.y += vy * force;
                }
            }
        }
    }
    
    setViscosity(value: number): void {
        this.viscosity = value;
    }
    
    setChaos(value: number): void {
        this.chaos = value;
    }
    
    update(deltaTime: number): void {
        this.time += deltaTime;
        
        // 创建新的流场作为下一步状态
        const newField = this.createFlowField();
        
        for (let x = 0; x < this.width; x++) {
            const column = this.flowField[x];
            const newColumn = newField[x];
            if (!column || !newColumn) continue;
            
            for (let y = 0; y < this.height; y++) {
                const cell = column[y];
                const newCell = newColumn[y];
                if (!cell || !newCell) continue;
                
                // 基础平流
                let newX = cell.x;
                let newY = cell.y;
                
                // 粘度效应（扩散）
                let sumX = 0;
                let sumY = 0;
                let count = 0;
                
                for (let dx = -1; dx <= 1; dx++) {
                    for (let dy = -1; dy <= 1; dy++) {
                        const nx = x + dx;
                        const ny = y + dy;
                        
                        if (nx >= 0 && nx < this.width && ny >= 0 && ny < this.height) {
                            const neighborColumn = this.flowField[nx];
                            if (neighborColumn && neighborColumn[ny]) {
                                sumX += neighborColumn[ny].x;
                                sumY += neighborColumn[ny].y;
                                count++;
                            }
                        }
                    }
                }
                
                if (count > 0) {
                    const avgX = sumX / count;
                    const avgY = sumY / count;
                    // 粘度越高，越趋向于平均
                    const viscosityFactor = 1 / (1 + this.viscosity);
                    newX = newX * viscosityFactor + avgX * (1 - viscosityFactor);
                    newY = newY * viscosityFactor + avgY * (1 - viscosityFactor);
                }
                
                // 混沌扰动
                if (this.chaos > 0) {
                    const noise = this.getPerlinNoise(x * 0.1, y * 0.1, this.time * 0.5);
                    const chaosStrength = this.chaos * 0.1;
                    newX += noise.x * chaosStrength * deltaTime;
                    newY += noise.y * chaosStrength * deltaTime;
                }
                
                // 能量衰减
                const decay = 0.99;
                newX *= decay;
                newY *= decay;
                
                // 限制最大速度
                const speed = Math.sqrt(newX * newX + newY * newY);
                const maxSpeed = 5.0;
                if (speed > maxSpeed) {
                    newX = (newX / speed) * maxSpeed;
                    newY = (newY / speed) * maxSpeed;
                }
                
                newCell.x = newX;
                newCell.y = newY;
            }
        }
        
        // 添加随机涡流
        if (Math.random() < 0.02 * deltaTime * 60) {
            const vortexX = Math.random() * this.width;
            const vortexY = Math.random() * this.height;
            const strength = 1 + Math.random() * 2;
            const radius = 5 + Math.random() * 10;
            this.addVortexToField(newField, vortexX, vortexY, strength, radius);
        }
        
        this.flowField = newField;
    }
    
    private addVortexToField(field: FlowVector[][], centerX: number, centerY: number, strength: number, radius: number): void {
        for (let x = 0; x < this.width; x++) {
            const column = field[x];
            if (!column) continue;
            
            for (let y = 0; y < this.height; y++) {
                const cell = column[y];
                if (!cell) continue;
                
                const dx = x - centerX;
                const dy = y - centerY;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < radius && distance > 0) {
                    const force = strength * (1 - distance / radius);
                    const vx = -dy / distance;
                    const vy = dx / distance;
                    
                    cell.x += vx * force;
                    cell.y += vy * force;
                }
            }
        }
    }
    
    private getPerlinNoise(x: number, y: number, t: number): FlowVector {
        // 简化版的Perlin噪声
        const angle = Math.sin(x * 0.1 + Math.cos(y * 0.07 + t) * 2) * Math.PI * 2;
        const strength = 0.5 + 0.5 * Math.sin(x * 0.05 + y * 0.03 + t * 0.7);
        
        return {
            x: Math.cos(angle) * strength,
            y: Math.sin(angle) * strength
        };
    }
    
    getFlowField(): FlowVector[][] {
        return this.flowField;
    }
    
    getPressure(): number {
        // 计算整个流场的平均动能作为"压力"
        let totalEnergy = 0;
        let count = 0;
        
        for (let x = 0; x < this.width; x++) {
            const column = this.flowField[x];
            if (!column) continue;
            
            for (let y = 0; y < this.height; y++) {
                const cell = column[y];
                if (!cell) continue;
                
                const vx = cell.x;
                const vy = cell.y;
                totalEnergy += vx * vx + vy * vy;
                count++;
            }
        }
        
        return count > 0 ? Math.sqrt(totalEnergy / count) : 0;
    }
}
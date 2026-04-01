// Glass Orb Game - Magic Bottle #107
// Super Workflow Bottle Simulation

// Types and Interfaces
interface Node {
    id: number;
    x: number;
    y: number;
    name: string;
    color: string;
    radius: number;
    connectedTo: number[]; // IDs of connected nodes
    active: boolean;
    visited: boolean;
}

interface Connection {
    from: number;
    to: number;
    progress: number; // 0 to 1 for animation
    active: boolean;
}

interface Orb {
    x: number;
    y: number;
    radius: number;
    color: string;
    targetNodeId: number | null;
    moving: boolean;
    speed: number;
    path: number[]; // Sequence of node IDs
    currentPathIndex: number;
    progress: number; // Progress along current connection (0 to 1)
}

// Game State
class GlassOrbGame {
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private nodes: Node[] = [];
    private connections: Connection[] = [];
    private orb: Orb;
    private animationId: number | null = null;
    private lastTime: number = 0;
    private isRunning: boolean = false;
    private showGrid: boolean = false;
    private animateConnections: boolean = true;
    private loopPath: boolean = true;
    private nextNodeId: number = 1;
    private selectedNode: Node | null = null;
    private draggingOrb: boolean = false;
    private mouseX: number = 0;
    private mouseY: number = 0;

    // UI Elements
    private startBtn: HTMLButtonElement;
    private resetBtn: HTMLButtonElement;
    private randomBtn: HTMLButtonElement;
    private speedSlider: HTMLInputElement;
    private stepsCount: HTMLElement;
    private progressPercent: HTMLElement;
    private nodeList: HTMLElement;
    private addNodeBtn: HTMLButtonElement;
    private clearNodesBtn: HTMLButtonElement;
    private loopPathCheckbox: HTMLInputElement;
    private showGridCheckbox: HTMLInputElement;
    private animateConnectionsCheckbox: HTMLInputElement;

    constructor(canvasId: string) {
        console.log('%c⚙️ Super Workflow Bottle #107 initializing...', 'color: #9d4edd; font-weight: bold; font-size: 14px;');
        console.log('%c🌀 "Infinite possibilities, fixed nodes. Let the human play."', 'color: #00bbf9; font-style: italic;');
        
        this.canvas = document.getElementById(canvasId) as HTMLCanvasElement;
        this.ctx = this.canvas.getContext('2d')!;
        
        // Initialize orb
        this.orb = {
            x: this.canvas.width / 2,
            y: this.canvas.height / 2,
            radius: 20,
            color: '#00bbf9',
            targetNodeId: null,
            moving: false,
            speed: 2,
            path: [],
            currentPathIndex: 0,
            progress: 0
        };

        // Initialize with some nodes
        this.initializeDefaultNodes();

        // Setup event listeners
        this.setupEventListeners();

        // Get UI elements
        this.startBtn = document.getElementById('startBtn') as HTMLButtonElement;
        this.resetBtn = document.getElementById('resetBtn') as HTMLButtonElement;
        this.randomBtn = document.getElementById('randomBtn') as HTMLButtonElement;
        this.speedSlider = document.getElementById('speedSlider') as HTMLInputElement;
        this.stepsCount = document.getElementById('stepsCount') as HTMLElement;
        this.progressPercent = document.getElementById('progressPercent') as HTMLElement;
        this.nodeList = document.getElementById('nodeList') as HTMLElement;
        this.addNodeBtn = document.getElementById('addNodeBtn') as HTMLButtonElement;
        this.clearNodesBtn = document.getElementById('clearNodesBtn') as HTMLButtonElement;
        this.loopPathCheckbox = document.getElementById('loopPath') as HTMLInputElement;
        this.showGridCheckbox = document.getElementById('showGrid') as HTMLInputElement;
        this.animateConnectionsCheckbox = document.getElementById('animateConnections') as HTMLInputElement;

        // Setup UI event listeners
        this.setupUIListeners();

        // Update UI
        this.updateNodeList();
        this.updateInfoDisplay();

        // Start animation loop
        this.animate();
    }

    private initializeDefaultNodes(): void {
        // Create initial nodes in a circular pattern
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const radius = Math.min(this.canvas.width, this.canvas.height) * 0.3;
        const nodeCount = 6;
        
        for (let i = 0; i < nodeCount; i++) {
            const angle = (i / nodeCount) * Math.PI * 2;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;
            
            const node: Node = {
                id: this.nextNodeId++,
                x,
                y,
                name: `Node ${i + 1}`,
                color: this.getNodeColor(i),
                radius: 25,
                connectedTo: [],
                active: false,
                visited: false
            };
            
            this.nodes.push(node);
        }
        
        // Connect nodes in a circular pattern
        for (let i = 0; i < this.nodes.length; i++) {
            const nextIndex = (i + 1) % this.nodes.length;
            this.nodes[i].connectedTo.push(this.nodes[nextIndex].id);
            this.connections.push({
                from: this.nodes[i].id,
                to: this.nodes[nextIndex].id,
                progress: 0,
                active: false
            });
        }
        
        // Add some cross connections for complexity
        if (this.nodes.length >= 4) {
            this.nodes[0].connectedTo.push(this.nodes[2].id);
            this.connections.push({
                from: this.nodes[0].id,
                to: this.nodes[2].id,
                progress: 0,
                active: false
            });
            
            this.nodes[1].connectedTo.push(this.nodes[4].id);
            this.connections.push({
                from: this.nodes[1].id,
                to: this.nodes[4].id,
                progress: 0,
                active: false
            });
        }
        
        // Place orb at first node
        if (this.nodes.length > 0) {
            this.orb.x = this.nodes[0].x;
            this.orb.y = this.nodes[0].y;
            this.nodes[0].active = true;
            this.nodes[0].visited = true;
        }
    }

    private getNodeColor(index: number): string {
        const colors = [
            '#9d4edd', // Purple
            '#00bbf9', // Blue
            '#f72585', // Pink
            '#4cc9f0', // Light Blue
            '#7209b7', // Dark Purple
            '#3a0ca3'  // Deep Blue
        ];
        return colors[index % colors.length];
    }

    private setupEventListeners(): void {
        // Canvas mouse events
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', () => this.handleMouseUp());
        
        // Canvas touch events for mobile
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            this.handleMouseDown(touch);
        });
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            this.handleMouseMove(touch);
        });
        this.canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.handleMouseUp();
        });
        
        // Window resize
        window.addEventListener('resize', () => this.handleResize());
    }

    private setupUIListeners(): void {
        // Start button
        this.startBtn.addEventListener('click', () => {
            if (!this.isRunning) {
                this.startWorkflow();
            } else {
                this.pauseWorkflow();
            }
        });
        
        // Reset button
        this.resetBtn.addEventListener('click', () => this.resetPath());
        
        // Random button
        this.randomBtn.addEventListener('click', () => this.randomizeNodes());
        
        // Speed slider
        this.speedSlider.addEventListener('input', () => {
            this.orb.speed = parseInt(this.speedSlider.value) / 2;
        });
        
        // Add node button
        this.addNodeBtn.addEventListener('click', () => this.addRandomNode());
        
        // Clear nodes button
        this.clearNodesBtn.addEventListener('click', () => this.clearAllNodes());
        
        // Checkboxes
        this.loopPathCheckbox.addEventListener('change', () => {
            this.loopPath = this.loopPathCheckbox.checked;
        });
        
        this.showGridCheckbox.addEventListener('change', () => {
            this.showGrid = this.showGridCheckbox.checked;
        });
        
        this.animateConnectionsCheckbox.addEventListener('change', () => {
            this.animateConnections = this.animateConnectionsCheckbox.checked;
        });
    }

    private handleMouseDown(e: MouseEvent | Touch): void {
        const rect = this.canvas.getBoundingClientRect();
        this.mouseX = e.clientX - rect.left;
        this.mouseY = e.clientY - rect.top;
        
        // Check if clicking on orb
        const distanceToOrb = Math.sqrt(
            Math.pow(this.mouseX - this.orb.x, 2) + 
            Math.pow(this.mouseY - this.orb.y, 2)
        );
        
        if (distanceToOrb <= this.orb.radius) {
            this.draggingOrb = true;
            return;
        }
        
        // Check if clicking on a node
        for (const node of this.nodes) {
            const distance = Math.sqrt(
                Math.pow(this.mouseX - node.x, 2) + 
                Math.pow(this.mouseY - node.y, 2)
            );
            
            if (distance <= node.radius) {
                this.selectedNode = node;
                
                // If orb is not moving, move it to this node
                if (!this.orb.moving) {
                    this.orb.x = node.x;
                    this.orb.y = node.y;
                    this.resetNodeStates();
                    node.active = true;
                    node.visited = true;
                    this.updateNodeList();
                }
                return;
            }
        }
        
        // If clicking on empty space, add a new node
        this.addNodeAt(this.mouseX, this.mouseY);
    }

    private handleMouseMove(e: MouseEvent | Touch): void {
        const rect = this.canvas.getBoundingClientRect();
        this.mouseX = e.clientX - rect.left;
        this.mouseY = e.clientY - rect.top;
        
        if (this.draggingOrb && !this.orb.moving) {
            this.orb.x = this.mouseX;
            this.orb.y = this.mouseY;
        }
    }

    private handleMouseUp(): void {
        this.draggingOrb = false;
        this.selectedNode = null;
    }

    private handleResize(): void {
        // Keep canvas size fixed for now, but could make responsive
        // this.canvas.width = this.canvas.clientWidth;
        // this.canvas.height = this.canvas.clientHeight;
    }

    // Game Logic
    private startWorkflow(): void {
        if (this.nodes.length === 0) return;
        
        this.isRunning = true;
        this.startBtn.innerHTML = '<i class="fas fa-pause"></i> Pause Workflow';
        this.startBtn.classList.remove('btn-primary');
        this.startBtn.classList.add('btn-accent');
        
        // Build path if not already built
        if (this.orb.path.length === 0) {
            this.buildPath();
        }
        
        // Start moving orb
        this.orb.moving = true;
        this.orb.currentPathIndex = 0;
        this.orb.progress = 0;
        
        // Find starting node
        const startNode = this.nodes.find(node => node.id === this.orb.path[0]);
        if (startNode) {
            this.orb.x = startNode.x;
            this.orb.y = startNode.y;
            this.resetNodeStates();
            startNode.active = true;
        }
    }

    private pauseWorkflow(): void {
        this.isRunning = false;
        this.orb.moving = false;
        this.startBtn.innerHTML = '<i class="fas fa-play"></i> Start Workflow';
        this.startBtn.classList.remove('btn-accent');
        this.startBtn.classList.add('btn-primary');
    }

    private resetPath(): void {
        this.pauseWorkflow();
        this.orb.path = [];
        this.orb.currentPathIndex = 0;
        this.orb.progress = 0;
        
        // Reset all nodes
        this.resetNodeStates();
        
        // Place orb at first node if exists
        if (this.nodes.length > 0) {
            this.orb.x = this.nodes[0].x;
            this.orb.y = this.nodes[0].y;
            this.nodes[0].active = true;
            this.nodes[0].visited = true;
        }
        
        this.updateInfoDisplay();
        this.updateNodeList();
    }

    private randomizeNodes(): void {
        // Clear existing nodes
        this.nodes = [];
        this.connections = [];
        this.nextNodeId = 1;
        
        // Create random nodes
        const nodeCount = Math.floor(Math.random() * 8) + 4; // 4 to 11 nodes
        for (let i = 0; i < nodeCount; i++) {
            const padding = 100;
            const x = padding + Math.random() * (this.canvas.width - padding * 2);
            const y = padding + Math.random() * (this.canvas.height - padding * 2);
            
            const node: Node = {
                id: this.nextNodeId++,
                x,
                y,
                name: `Node ${i + 1}`,
                color: this.getNodeColor(i),
                radius: 25,
                connectedTo: [],
                active: false,
                visited: false
            };
            
            this.nodes.push(node);
        }
        
        // Create random connections
        for (let i = 0; i < this.nodes.length; i++) {
            const connectionCount = Math.floor(Math.random() * 3) + 1; // 1 to 3 connections per node
            for (let j = 0; j < connectionCount; j++) {
                const targetIndex = Math.floor(Math.random() * this.nodes.length);
                if (targetIndex !== i && !this.nodes[i].connectedTo.includes(this.nodes[targetIndex].id)) {
                    this.nodes[i].connectedTo.push(this.nodes[targetIndex].id);
                    this.connections.push({
                        from: this.nodes[i].id,
                        to: this.nodes[targetIndex].id,
                        progress: 0,
                        active: false
                    });
                }
            }
        }
        
        // Reset orb
        this.resetPath();
    }

    private addRandomNode(): void {
        const padding = 100;
        const x = padding + Math.random() * (this.canvas.width - padding * 2);
        const y = padding + Math.random() * (this.canvas.height - padding * 2);
        
        this.addNodeAt(x, y);
    }

    private addNodeAt(x: number, y: number): void {
        const node: Node = {
            id: this.nextNodeId++,
            x,
            y,
            name: `Node ${this.nextNodeId - 1}`,
            color: this.getNodeColor(this.nodes.length),
            radius: 25,
            connectedTo: [],
            active: false,
            visited: false
        };
        
        this.nodes.push(node);
        
        // Connect to a few random existing nodes
        if (this.nodes.length > 1) {
            const connectionsToAdd = Math.min(3, this.nodes.length - 1);
            for (let i = 0; i < connectionsToAdd; i++) {
                const targetIndex = Math.floor(Math.random() * (this.nodes.length - 1));
                if (!node.connectedTo.includes(this.nodes[targetIndex].id)) {
                    node.connectedTo.push(this.nodes[targetIndex].id);
                    this.connections.push({
                        from: node.id,
                        to: this.nodes[targetIndex].id,
                        progress: 0,
                        active: false
                    });
                }
            }
        }
        
        this.updateNodeList();
    }

    private clearAllNodes(): void {
        if (confirm('Clear all nodes and connections?')) {
            this.nodes = [];
            this.connections = [];
            this.nextNodeId = 1;
            this.resetPath();
            this.updateNodeList();
        }
    }

    private buildPath(): void {
        // Simple path finding - just visit all nodes in order
        this.orb.path = this.nodes.map(node => node.id);
        
        // Shuffle path for randomness
        for (let i = this.orb.path.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [this.orb.path[i], this.orb.path[j]] = [this.orb.path[j], this.orb.path[i]];
        }
        
        // If loop is enabled, add return to start
        if (this.loopPath && this.orb.path.length > 1) {
            this.orb.path.push(this.orb.path[0]);
        }
    }

    private resetNodeStates(): void {
        for (const node of this.nodes) {
            node.active = false;
            node.visited = false;
        }
        
        for (const conn of this.connections) {
            conn.active = false;
            conn.progress = 0;
        }
    }

    private updateOrb(deltaTime: number): void {
        if (!this.orb.moving || this.orb.path.length === 0) return;
        
        const currentNodeId = this.orb.path[this.orb.currentPathIndex];
        const nextNodeId = this.orb.path[this.orb.currentPathIndex + 1];
        
        if (!nextNodeId) {
            // Reached end of path
            if (this.loopPath && this.orb.path.length > 1) {
                this.orb.currentPathIndex = 0;
                this.orb.progress = 0;
                this.resetNodeStates();
            } else {
                this.orb.moving = false;
                this.pauseWorkflow();
            }
            return;
        }
        
        const currentNode = this.nodes.find(n => n.id === currentNodeId);
        const nextNode = this.nodes.find(n => n.id === nextNodeId);
        
        if (!currentNode || !nextNode) return;
        
        // Update progress
        this.orb.progress += (this.orb.speed * deltaTime) / 100;
        if (this.orb.progress > 1) this.orb.progress = 1;
        
        // Calculate orb position
        this.orb.x = currentNode.x + (nextNode.x - currentNode.x) * this.orb.progress;
        this.orb.y = currentNode.y + (nextNode.y - currentNode.y) * this.orb.progress;
        
        // Update connection animation
        const connection = this.connections.find(
            conn => (conn.from === currentNodeId && conn.to === nextNodeId) ||
                   (conn.from === nextNodeId && conn.to === currentNodeId)
        );
        
        if (connection) {
            connection.active = true;
            connection.progress = this.orb.progress;
        }
        
        // When reaching next node
        if (this.orb.progress >= 1) {
            currentNode.active = false;
            nextNode.active = true;
            nextNode.visited = true;
            
            this.orb.currentPathIndex++;
            this.orb.progress = 0;
            
            // Update info display
            this.updateInfoDisplay();
            this.updateNodeList();
        }
    }

    // Rendering
    private drawGrid(): void {
        if (!this.showGrid) return;
        
        this.ctx.strokeStyle = 'rgba(157, 78, 221, 0.1)';
        this.ctx.lineWidth = 1;
        
        const gridSize = 50;
        
        // Vertical lines
        for (let x = 0; x < this.canvas.width; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.canvas.height);
            this.ctx.stroke();
        }
        
        // Horizontal lines
        for (let y = 0; y < this.canvas.height; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }
    }

    private drawConnections(): void {
        for (const connection of this.connections) {
            const fromNode = this.nodes.find(n => n.id === connection.from);
            const toNode = this.nodes.find(n => n.id === connection.to);
            
            if (!fromNode || !toNode) continue;
            
            // Draw connection line
            this.ctx.beginPath();
            this.ctx.moveTo(fromNode.x, fromNode.y);
            this.ctx.lineTo(toNode.x, toNode.y);
            
            if (connection.active) {
                this.ctx.strokeStyle = connection.active ? '#00bbf9' : 'rgba(157, 78, 221, 0.5)';
                this.ctx.lineWidth = 3;
                
                // Animated dash effect
                if (this.animateConnections) {
                    this.ctx.setLineDash([5, 5]);
                    this.ctx.lineDashOffset = -connection.progress * 20;
                }
            } else {
                this.ctx.strokeStyle = 'rgba(157, 78, 221, 0.3)';
                this.ctx.lineWidth = 2;
                this.ctx.setLineDash([]);
            }
            
            this.ctx.stroke();
            this.ctx.setLineDash([]);
            
            // Draw progress indicator if active
            if (connection.active && connection.progress > 0) {
                const progressX = fromNode.x + (toNode.x - fromNode.x) * connection.progress;
                const progressY = fromNode.y + (toNode.y - fromNode.y) * connection.progress;
                
                this.ctx.beginPath();
                this.ctx.arc(progressX, progressY, 6, 0, Math.PI * 2);
                this.ctx.fillStyle = '#f72585';
                this.ctx.fill();
                this.ctx.strokeStyle = 'white';
                this.ctx.lineWidth = 2;
                this.ctx.stroke();
            }
        }
    }

    private drawNodes(): void {
        for (const node of this.nodes) {
            // Draw node glow if active
            if (node.active) {
                this.ctx.beginPath();
                this.ctx.arc(node.x, node.y, node.radius + 10, 0, Math.PI * 2);
                const gradient = this.ctx.createRadialGradient(
                    node.x, node.y, node.radius,
                    node.x, node.y, node.radius + 10
                );
                gradient.addColorStop(0, node.color + '80');
                gradient.addColorStop(1, node.color + '00');
                this.ctx.fillStyle = gradient;
                this.ctx.fill();
            }
            
            // Draw node
            this.ctx.beginPath();
            this.ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
            
            // Node fill
            const nodeGradient = this.ctx.createRadialGradient(
                node.x - 5, node.y - 5, 5,
                node.x, node.y, node.radius
            );
            nodeGradient.addColorStop(0, node.color + 'FF');
            nodeGradient.addColorStop(1, node.color + '80');
            this.ctx.fillStyle = nodeGradient;
            this.ctx.fill();
            
            // Node border
            this.ctx.strokeStyle = node.active ? '#ffffff' : 'rgba(255, 255, 255, 0.7)';
            this.ctx.lineWidth = node.active ? 3 : 2;
            this.ctx.stroke();
            
            // Node label
            this.ctx.fillStyle = 'white';
            this.ctx.font = 'bold 14px "Exo 2", sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(node.name, node.x, node.y);
            
            // Visited indicator
            if (node.visited && !node.active) {
                this.ctx.beginPath();
                this.ctx.arc(node.x, node.y, 8, 0, Math.PI * 2);
                this.ctx.fillStyle = '#00bbf9';
                this.ctx.fill();
                this.ctx.strokeStyle = 'white';
                this.ctx.lineWidth = 2;
                this.ctx.stroke();
            }
        }
    }

    private drawOrb(): void {
        // Orb glow
        this.ctx.beginPath();
        this.ctx.arc(this.orb.x, this.orb.y, this.orb.radius + 15, 0, Math.PI * 2);
        const glowGradient = this.ctx.createRadialGradient(
            this.orb.x, this.orb.y, this.orb.radius,
            this.orb.x, this.orb.y, this.orb.radius + 15
        );
        glowGradient.addColorStop(0, this.orb.color + '80');
        glowGradient.addColorStop(1, this.orb.color + '00');
        this.ctx.fillStyle = glowGradient;
        this.ctx.fill();
        
        // Orb body
        this.ctx.beginPath();
        this.ctx.arc(this.orb.x, this.orb.y, this.orb.radius, 0, Math.PI * 2);
        
        // Glass effect gradient
        const orbGradient = this.ctx.createRadialGradient(
            this.orb.x - 10, this.orb.y - 10, 5,
            this.orb.x, this.orb.y, this.orb.radius
        );
        orbGradient.addColorStop(0, '#ffffff');
        orbGradient.addColorStop(0.3, this.orb.color);
        orbGradient.addColorStop(1, this.orb.color + '80');
        this.ctx.fillStyle = orbGradient;
        this.ctx.fill();
        
        // Orb highlight
        this.ctx.beginPath();
        this.ctx.arc(this.orb.x - 8, this.orb.y - 8, 8, 0, Math.PI * 2);
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        this.ctx.fill();
        
        // Orb border
        this.ctx.strokeStyle = 'white';
        this.ctx.lineWidth = 3;
        this.ctx.stroke();
        
        // Orb trail if moving
        if (this.orb.moving) {
            this.ctx.beginPath();
            this.ctx.moveTo(this.orb.x, this.orb.y);
            
            // Draw a short trail backwards
            const trailLength = 20;
            const angle = Math.atan2(
                this.orb.y - this.mouseY,
                this.orb.x - this.mouseX
            ) + Math.PI;
            
            const trailX = this.orb.x + Math.cos(angle) * trailLength;
            const trailY = this.orb.y + Math.sin(angle) * trailLength;
            
            this.ctx.lineTo(trailX, trailY);
            this.ctx.strokeStyle = this.orb.color + '80';
            this.ctx.lineWidth = 4;
            this.ctx.stroke();
        }
    }

    private draw(): void {
        // Clear canvas with slight transparency for trail effect
        this.ctx.fillStyle = 'rgba(10, 10, 20, 0.1)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw grid
        this.drawGrid();
        
        // Draw connections
        this.drawConnections();
        
        // Draw nodes
        this.drawNodes();
        
        // Draw orb
        this.drawOrb();
    }

    private animate = (timestamp: number = 0): void => {
        // Calculate delta time
        const deltaTime = this.lastTime ? timestamp - this.lastTime : 16;
        this.lastTime = timestamp;
        
        // Update game state
        this.updateOrb(deltaTime);
        
        // Draw everything
        this.draw();
        
        // Continue animation loop
        this.animationId = requestAnimationFrame(this.animate);
    }

    // UI Updates
    private updateInfoDisplay(): void {
        // Calculate steps (visited nodes)
        const visitedCount = this.nodes.filter(node => node.visited).length;
        const totalCount = this.nodes.length;
        
        this.stepsCount.textContent = visitedCount.toString();
        
        if (totalCount > 0) {
            const progress = Math.round((visitedCount / totalCount) * 100);
            this.progressPercent.textContent = `${progress}%`;
        } else {
            this.progressPercent.textContent = '0%';
        }
    }

    private updateNodeList(): void {
        this.nodeList.innerHTML = '';
        
        for (const node of this.nodes) {
            const nodeElement = document.createElement('div');
            nodeElement.className = `node-item ${node.active ? 'active' : ''}`;
            
            nodeElement.innerHTML = `
                <div class="node-info">
                    <div class="node-name">${node.name}</div>
                    <div class="node-id">ID: ${node.id}</div>
                </div>
                <div class="node-actions">
                    <button class="node-btn" data-action="visit" data-id="${node.id}">
                        <i class="fas fa-crosshairs"></i>
                    </button>
                    <button class="node-btn" data-action="delete" data-id="${node.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            // Add event listeners to buttons
            const visitBtn = nodeElement.querySelector('[data-action="visit"]');
            const deleteBtn = nodeElement.querySelector('[data-action="delete"]');
            
            if (visitBtn) {
                visitBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.moveOrbToNode(node.id);
                });
            }
            
            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deleteNode(node.id);
                });
            }
            
            this.nodeList.appendChild(nodeElement);
        }
    }

    private moveOrbToNode(nodeId: number): void {
        const node = this.nodes.find(n => n.id === nodeId);
        if (!node) return;
        
        if (!this.orb.moving) {
            this.orb.x = node.x;
            this.orb.y = node.y;
            this.resetNodeStates();
            node.active = true;
            node.visited = true;
            this.updateNodeList();
        }
    }

    private deleteNode(nodeId: number): void {
        // Remove node
        this.nodes = this.nodes.filter(node => node.id !== nodeId);
        
        // Remove connections involving this node
        this.connections = this.connections.filter(
            conn => conn.from !== nodeId && conn.to !== nodeId
        );
        
        // Update other nodes' connections
        for (const node of this.nodes) {
            node.connectedTo = node.connectedTo.filter(id => id !== nodeId);
        }
        
        // Update path if needed
        this.orb.path = this.orb.path.filter(id => id !== nodeId);
        
        // Reset if orb was on deleted node
        if (this.orb.path.length === 0 && this.nodes.length > 0) {
            this.orb.x = this.nodes[0].x;
            this.orb.y = this.nodes[0].y;
            this.nodes[0].active = true;
            this.nodes[0].visited = true;
        }
        
        this.updateNodeList();
        this.updateInfoDisplay();
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    const game = new GlassOrbGame('gameCanvas');
    
    // Expose game instance to console for debugging
    (window as any).glassOrbGame = game;
    
    console.log('Glass Orb Game initialized. Magic Bottle #107 is watching...');
});
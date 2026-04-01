// game.ts
class GlassOrbGame {
  canvas;
  ctx;
  nodes = [];
  connections = [];
  orb;
  animationId = null;
  lastTime = 0;
  isRunning = false;
  showGrid = false;
  animateConnections = true;
  loopPath = true;
  nextNodeId = 1;
  selectedNode = null;
  draggingOrb = false;
  mouseX = 0;
  mouseY = 0;
  startBtn;
  resetBtn;
  randomBtn;
  speedSlider;
  stepsCount;
  progressPercent;
  nodeList;
  addNodeBtn;
  clearNodesBtn;
  loopPathCheckbox;
  showGridCheckbox;
  animateConnectionsCheckbox;
  constructor(canvasId) {
    console.log("%c⚙️ Super Workflow Bottle #107 initializing...", "color: #9d4edd; font-weight: bold; font-size: 14px;");
    console.log('%c\uD83C\uDF00 "Infinite possibilities, fixed nodes. Let the human play."', "color: #00bbf9; font-style: italic;");
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext("2d");
    this.orb = {
      x: this.canvas.width / 2,
      y: this.canvas.height / 2,
      radius: 20,
      color: "#00bbf9",
      targetNodeId: null,
      moving: false,
      speed: 2,
      path: [],
      currentPathIndex: 0,
      progress: 0
    };
    this.initializeDefaultNodes();
    this.setupEventListeners();
    this.startBtn = document.getElementById("startBtn");
    this.resetBtn = document.getElementById("resetBtn");
    this.randomBtn = document.getElementById("randomBtn");
    this.speedSlider = document.getElementById("speedSlider");
    this.stepsCount = document.getElementById("stepsCount");
    this.progressPercent = document.getElementById("progressPercent");
    this.nodeList = document.getElementById("nodeList");
    this.addNodeBtn = document.getElementById("addNodeBtn");
    this.clearNodesBtn = document.getElementById("clearNodesBtn");
    this.loopPathCheckbox = document.getElementById("loopPath");
    this.showGridCheckbox = document.getElementById("showGrid");
    this.animateConnectionsCheckbox = document.getElementById("animateConnections");
    this.setupUIListeners();
    this.updateNodeList();
    this.updateInfoDisplay();
    this.animate();
  }
  initializeDefaultNodes() {
    const centerX = this.canvas.width / 2;
    const centerY = this.canvas.height / 2;
    const radius = Math.min(this.canvas.width, this.canvas.height) * 0.3;
    const nodeCount = 6;
    for (let i = 0;i < nodeCount; i++) {
      const angle = i / nodeCount * Math.PI * 2;
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;
      const node = {
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
    for (let i = 0;i < this.nodes.length; i++) {
      const nextIndex = (i + 1) % this.nodes.length;
      this.nodes[i].connectedTo.push(this.nodes[nextIndex].id);
      this.connections.push({
        from: this.nodes[i].id,
        to: this.nodes[nextIndex].id,
        progress: 0,
        active: false
      });
    }
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
    if (this.nodes.length > 0) {
      this.orb.x = this.nodes[0].x;
      this.orb.y = this.nodes[0].y;
      this.nodes[0].active = true;
      this.nodes[0].visited = true;
    }
  }
  getNodeColor(index) {
    const colors = [
      "#9d4edd",
      "#00bbf9",
      "#f72585",
      "#4cc9f0",
      "#7209b7",
      "#3a0ca3"
    ];
    return colors[index % colors.length];
  }
  setupEventListeners() {
    this.canvas.addEventListener("mousedown", (e) => this.handleMouseDown(e));
    this.canvas.addEventListener("mousemove", (e) => this.handleMouseMove(e));
    this.canvas.addEventListener("mouseup", () => this.handleMouseUp());
    this.canvas.addEventListener("touchstart", (e) => {
      e.preventDefault();
      const touch = e.touches[0];
      this.handleMouseDown(touch);
    });
    this.canvas.addEventListener("touchmove", (e) => {
      e.preventDefault();
      const touch = e.touches[0];
      this.handleMouseMove(touch);
    });
    this.canvas.addEventListener("touchend", (e) => {
      e.preventDefault();
      this.handleMouseUp();
    });
    window.addEventListener("resize", () => this.handleResize());
  }
  setupUIListeners() {
    this.startBtn.addEventListener("click", () => {
      if (!this.isRunning) {
        this.startWorkflow();
      } else {
        this.pauseWorkflow();
      }
    });
    this.resetBtn.addEventListener("click", () => this.resetPath());
    this.randomBtn.addEventListener("click", () => this.randomizeNodes());
    this.speedSlider.addEventListener("input", () => {
      this.orb.speed = parseInt(this.speedSlider.value) / 2;
    });
    this.addNodeBtn.addEventListener("click", () => this.addRandomNode());
    this.clearNodesBtn.addEventListener("click", () => this.clearAllNodes());
    this.loopPathCheckbox.addEventListener("change", () => {
      this.loopPath = this.loopPathCheckbox.checked;
    });
    this.showGridCheckbox.addEventListener("change", () => {
      this.showGrid = this.showGridCheckbox.checked;
    });
    this.animateConnectionsCheckbox.addEventListener("change", () => {
      this.animateConnections = this.animateConnectionsCheckbox.checked;
    });
  }
  handleMouseDown(e) {
    const rect = this.canvas.getBoundingClientRect();
    this.mouseX = e.clientX - rect.left;
    this.mouseY = e.clientY - rect.top;
    const distanceToOrb = Math.sqrt(Math.pow(this.mouseX - this.orb.x, 2) + Math.pow(this.mouseY - this.orb.y, 2));
    if (distanceToOrb <= this.orb.radius) {
      this.draggingOrb = true;
      return;
    }
    for (const node of this.nodes) {
      const distance = Math.sqrt(Math.pow(this.mouseX - node.x, 2) + Math.pow(this.mouseY - node.y, 2));
      if (distance <= node.radius) {
        this.selectedNode = node;
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
    this.addNodeAt(this.mouseX, this.mouseY);
  }
  handleMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    this.mouseX = e.clientX - rect.left;
    this.mouseY = e.clientY - rect.top;
    if (this.draggingOrb && !this.orb.moving) {
      this.orb.x = this.mouseX;
      this.orb.y = this.mouseY;
    }
  }
  handleMouseUp() {
    this.draggingOrb = false;
    this.selectedNode = null;
  }
  handleResize() {}
  startWorkflow() {
    if (this.nodes.length === 0)
      return;
    this.isRunning = true;
    this.startBtn.innerHTML = '<i class="fas fa-pause"></i> Pause Workflow';
    this.startBtn.classList.remove("btn-primary");
    this.startBtn.classList.add("btn-accent");
    if (this.orb.path.length === 0) {
      this.buildPath();
    }
    this.orb.moving = true;
    this.orb.currentPathIndex = 0;
    this.orb.progress = 0;
    const startNode = this.nodes.find((node) => node.id === this.orb.path[0]);
    if (startNode) {
      this.orb.x = startNode.x;
      this.orb.y = startNode.y;
      this.resetNodeStates();
      startNode.active = true;
    }
  }
  pauseWorkflow() {
    this.isRunning = false;
    this.orb.moving = false;
    this.startBtn.innerHTML = '<i class="fas fa-play"></i> Start Workflow';
    this.startBtn.classList.remove("btn-accent");
    this.startBtn.classList.add("btn-primary");
  }
  resetPath() {
    this.pauseWorkflow();
    this.orb.path = [];
    this.orb.currentPathIndex = 0;
    this.orb.progress = 0;
    this.resetNodeStates();
    if (this.nodes.length > 0) {
      this.orb.x = this.nodes[0].x;
      this.orb.y = this.nodes[0].y;
      this.nodes[0].active = true;
      this.nodes[0].visited = true;
    }
    this.updateInfoDisplay();
    this.updateNodeList();
  }
  randomizeNodes() {
    this.nodes = [];
    this.connections = [];
    this.nextNodeId = 1;
    const nodeCount = Math.floor(Math.random() * 8) + 4;
    for (let i = 0;i < nodeCount; i++) {
      const padding = 100;
      const x = padding + Math.random() * (this.canvas.width - padding * 2);
      const y = padding + Math.random() * (this.canvas.height - padding * 2);
      const node = {
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
    for (let i = 0;i < this.nodes.length; i++) {
      const connectionCount = Math.floor(Math.random() * 3) + 1;
      for (let j = 0;j < connectionCount; j++) {
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
    this.resetPath();
  }
  addRandomNode() {
    const padding = 100;
    const x = padding + Math.random() * (this.canvas.width - padding * 2);
    const y = padding + Math.random() * (this.canvas.height - padding * 2);
    this.addNodeAt(x, y);
  }
  addNodeAt(x, y) {
    const node = {
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
    if (this.nodes.length > 1) {
      const connectionsToAdd = Math.min(3, this.nodes.length - 1);
      for (let i = 0;i < connectionsToAdd; i++) {
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
  clearAllNodes() {
    if (confirm("Clear all nodes and connections?")) {
      this.nodes = [];
      this.connections = [];
      this.nextNodeId = 1;
      this.resetPath();
      this.updateNodeList();
    }
  }
  buildPath() {
    this.orb.path = this.nodes.map((node) => node.id);
    for (let i = this.orb.path.length - 1;i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [this.orb.path[i], this.orb.path[j]] = [this.orb.path[j], this.orb.path[i]];
    }
    if (this.loopPath && this.orb.path.length > 1) {
      this.orb.path.push(this.orb.path[0]);
    }
  }
  resetNodeStates() {
    for (const node of this.nodes) {
      node.active = false;
      node.visited = false;
    }
    for (const conn of this.connections) {
      conn.active = false;
      conn.progress = 0;
    }
  }
  updateOrb(deltaTime) {
    if (!this.orb.moving || this.orb.path.length === 0)
      return;
    const currentNodeId = this.orb.path[this.orb.currentPathIndex];
    const nextNodeId = this.orb.path[this.orb.currentPathIndex + 1];
    if (!nextNodeId) {
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
    const currentNode = this.nodes.find((n) => n.id === currentNodeId);
    const nextNode = this.nodes.find((n) => n.id === nextNodeId);
    if (!currentNode || !nextNode)
      return;
    this.orb.progress += this.orb.speed * deltaTime / 100;
    if (this.orb.progress > 1)
      this.orb.progress = 1;
    this.orb.x = currentNode.x + (nextNode.x - currentNode.x) * this.orb.progress;
    this.orb.y = currentNode.y + (nextNode.y - currentNode.y) * this.orb.progress;
    const connection = this.connections.find((conn) => conn.from === currentNodeId && conn.to === nextNodeId || conn.from === nextNodeId && conn.to === currentNodeId);
    if (connection) {
      connection.active = true;
      connection.progress = this.orb.progress;
    }
    if (this.orb.progress >= 1) {
      currentNode.active = false;
      nextNode.active = true;
      nextNode.visited = true;
      this.orb.currentPathIndex++;
      this.orb.progress = 0;
      this.updateInfoDisplay();
      this.updateNodeList();
    }
  }
  drawGrid() {
    if (!this.showGrid)
      return;
    this.ctx.strokeStyle = "rgba(157, 78, 221, 0.1)";
    this.ctx.lineWidth = 1;
    const gridSize = 50;
    for (let x = 0;x < this.canvas.width; x += gridSize) {
      this.ctx.beginPath();
      this.ctx.moveTo(x, 0);
      this.ctx.lineTo(x, this.canvas.height);
      this.ctx.stroke();
    }
    for (let y = 0;y < this.canvas.height; y += gridSize) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(this.canvas.width, y);
      this.ctx.stroke();
    }
  }
  drawConnections() {
    for (const connection of this.connections) {
      const fromNode = this.nodes.find((n) => n.id === connection.from);
      const toNode = this.nodes.find((n) => n.id === connection.to);
      if (!fromNode || !toNode)
        continue;
      this.ctx.beginPath();
      this.ctx.moveTo(fromNode.x, fromNode.y);
      this.ctx.lineTo(toNode.x, toNode.y);
      if (connection.active) {
        this.ctx.strokeStyle = connection.active ? "#00bbf9" : "rgba(157, 78, 221, 0.5)";
        this.ctx.lineWidth = 3;
        if (this.animateConnections) {
          this.ctx.setLineDash([5, 5]);
          this.ctx.lineDashOffset = -connection.progress * 20;
        }
      } else {
        this.ctx.strokeStyle = "rgba(157, 78, 221, 0.3)";
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([]);
      }
      this.ctx.stroke();
      this.ctx.setLineDash([]);
      if (connection.active && connection.progress > 0) {
        const progressX = fromNode.x + (toNode.x - fromNode.x) * connection.progress;
        const progressY = fromNode.y + (toNode.y - fromNode.y) * connection.progress;
        this.ctx.beginPath();
        this.ctx.arc(progressX, progressY, 6, 0, Math.PI * 2);
        this.ctx.fillStyle = "#f72585";
        this.ctx.fill();
        this.ctx.strokeStyle = "white";
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
      }
    }
  }
  drawNodes() {
    for (const node of this.nodes) {
      if (node.active) {
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, node.radius + 10, 0, Math.PI * 2);
        const gradient = this.ctx.createRadialGradient(node.x, node.y, node.radius, node.x, node.y, node.radius + 10);
        gradient.addColorStop(0, node.color + "80");
        gradient.addColorStop(1, node.color + "00");
        this.ctx.fillStyle = gradient;
        this.ctx.fill();
      }
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      const nodeGradient = this.ctx.createRadialGradient(node.x - 5, node.y - 5, 5, node.x, node.y, node.radius);
      nodeGradient.addColorStop(0, node.color + "FF");
      nodeGradient.addColorStop(1, node.color + "80");
      this.ctx.fillStyle = nodeGradient;
      this.ctx.fill();
      this.ctx.strokeStyle = node.active ? "#ffffff" : "rgba(255, 255, 255, 0.7)";
      this.ctx.lineWidth = node.active ? 3 : 2;
      this.ctx.stroke();
      this.ctx.fillStyle = "white";
      this.ctx.font = 'bold 14px "Exo 2", sans-serif';
      this.ctx.textAlign = "center";
      this.ctx.textBaseline = "middle";
      this.ctx.fillText(node.name, node.x, node.y);
      if (node.visited && !node.active) {
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, 8, 0, Math.PI * 2);
        this.ctx.fillStyle = "#00bbf9";
        this.ctx.fill();
        this.ctx.strokeStyle = "white";
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
      }
    }
  }
  drawOrb() {
    this.ctx.beginPath();
    this.ctx.arc(this.orb.x, this.orb.y, this.orb.radius + 15, 0, Math.PI * 2);
    const glowGradient = this.ctx.createRadialGradient(this.orb.x, this.orb.y, this.orb.radius, this.orb.x, this.orb.y, this.orb.radius + 15);
    glowGradient.addColorStop(0, this.orb.color + "80");
    glowGradient.addColorStop(1, this.orb.color + "00");
    this.ctx.fillStyle = glowGradient;
    this.ctx.fill();
    this.ctx.beginPath();
    this.ctx.arc(this.orb.x, this.orb.y, this.orb.radius, 0, Math.PI * 2);
    const orbGradient = this.ctx.createRadialGradient(this.orb.x - 10, this.orb.y - 10, 5, this.orb.x, this.orb.y, this.orb.radius);
    orbGradient.addColorStop(0, "#ffffff");
    orbGradient.addColorStop(0.3, this.orb.color);
    orbGradient.addColorStop(1, this.orb.color + "80");
    this.ctx.fillStyle = orbGradient;
    this.ctx.fill();
    this.ctx.beginPath();
    this.ctx.arc(this.orb.x - 8, this.orb.y - 8, 8, 0, Math.PI * 2);
    this.ctx.fillStyle = "rgba(255, 255, 255, 0.6)";
    this.ctx.fill();
    this.ctx.strokeStyle = "white";
    this.ctx.lineWidth = 3;
    this.ctx.stroke();
    if (this.orb.moving) {
      this.ctx.beginPath();
      this.ctx.moveTo(this.orb.x, this.orb.y);
      const trailLength = 20;
      const angle = Math.atan2(this.orb.y - this.mouseY, this.orb.x - this.mouseX) + Math.PI;
      const trailX = this.orb.x + Math.cos(angle) * trailLength;
      const trailY = this.orb.y + Math.sin(angle) * trailLength;
      this.ctx.lineTo(trailX, trailY);
      this.ctx.strokeStyle = this.orb.color + "80";
      this.ctx.lineWidth = 4;
      this.ctx.stroke();
    }
  }
  draw() {
    this.ctx.fillStyle = "rgba(10, 10, 20, 0.1)";
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    this.drawGrid();
    this.drawConnections();
    this.drawNodes();
    this.drawOrb();
  }
  animate = (timestamp = 0) => {
    const deltaTime = this.lastTime ? timestamp - this.lastTime : 16;
    this.lastTime = timestamp;
    this.updateOrb(deltaTime);
    this.draw();
    this.animationId = requestAnimationFrame(this.animate);
  };
  updateInfoDisplay() {
    const visitedCount = this.nodes.filter((node) => node.visited).length;
    const totalCount = this.nodes.length;
    this.stepsCount.textContent = visitedCount.toString();
    if (totalCount > 0) {
      const progress = Math.round(visitedCount / totalCount * 100);
      this.progressPercent.textContent = `${progress}%`;
    } else {
      this.progressPercent.textContent = "0%";
    }
  }
  updateNodeList() {
    this.nodeList.innerHTML = "";
    for (const node of this.nodes) {
      const nodeElement = document.createElement("div");
      nodeElement.className = `node-item ${node.active ? "active" : ""}`;
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
      const visitBtn = nodeElement.querySelector('[data-action="visit"]');
      const deleteBtn = nodeElement.querySelector('[data-action="delete"]');
      if (visitBtn) {
        visitBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          this.moveOrbToNode(node.id);
        });
      }
      if (deleteBtn) {
        deleteBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          this.deleteNode(node.id);
        });
      }
      this.nodeList.appendChild(nodeElement);
    }
  }
  moveOrbToNode(nodeId) {
    const node = this.nodes.find((n) => n.id === nodeId);
    if (!node)
      return;
    if (!this.orb.moving) {
      this.orb.x = node.x;
      this.orb.y = node.y;
      this.resetNodeStates();
      node.active = true;
      node.visited = true;
      this.updateNodeList();
    }
  }
  deleteNode(nodeId) {
    this.nodes = this.nodes.filter((node) => node.id !== nodeId);
    this.connections = this.connections.filter((conn) => conn.from !== nodeId && conn.to !== nodeId);
    for (const node of this.nodes) {
      node.connectedTo = node.connectedTo.filter((id) => id !== nodeId);
    }
    this.orb.path = this.orb.path.filter((id) => id !== nodeId);
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
document.addEventListener("DOMContentLoaded", () => {
  const game = new GlassOrbGame("gameCanvas");
  window.glassOrbGame = game;
  console.log("Glass Orb Game initialized. Magic Bottle #107 is watching...");
});

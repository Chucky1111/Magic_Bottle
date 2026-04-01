// src/main.ts
class GlassBallGame {
  canvas;
  ctx;
  balls = [];
  ballCountElement;
  collisionCountElement;
  fpsElement;
  gravityBtn;
  gravityStatusElement;
  frictionSlider;
  frictionValueElement;
  ballIdCounter = 0;
  collisionCount = 0;
  frameCount = 0;
  lastTime = 0;
  fps = 60;
  gravityEnabled = true;
  gravity = 0.2;
  friction = 0.1;
  isDragging = false;
  draggedBall = null;
  dragStartX = 0;
  dragStartY = 0;
  animationId = null;
  constructor() {
    this.canvas = document.getElementById("gameCanvas");
    this.ctx = this.canvas.getContext("2d");
    this.ballCountElement = document.getElementById("ballCount");
    this.collisionCountElement = document.getElementById("collisionCount");
    this.fpsElement = document.getElementById("fps");
    this.gravityBtn = document.getElementById("gravityBtn");
    this.gravityStatusElement = document.getElementById("gravityStatus");
    this.frictionSlider = document.getElementById("frictionSlider");
    this.frictionValueElement = document.getElementById("frictionValue");
    this.init();
  }
  init() {
    this.resizeCanvas();
    window.addEventListener("resize", () => this.resizeCanvas());
    document.getElementById("addBallBtn").addEventListener("click", () => this.addBall());
    document.getElementById("clearBtn").addEventListener("click", () => this.clearBalls());
    this.gravityBtn.addEventListener("click", () => this.toggleGravity());
    this.frictionSlider.addEventListener("input", (e) => this.updateFriction(e));
    this.canvas.addEventListener("mousedown", (e) => this.startDrag(e));
    this.canvas.addEventListener("mousemove", (e) => this.drag(e));
    this.canvas.addEventListener("mouseup", () => this.endDrag());
    this.canvas.addEventListener("mouseleave", () => this.endDrag());
    this.canvas.addEventListener("touchstart", (e) => {
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
    this.canvas.addEventListener("touchmove", (e) => {
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
    this.canvas.addEventListener("touchend", (e) => {
      e.preventDefault();
      this.endDrag();
    });
    for (let i = 0;i < 3; i++) {
      this.addBall();
    }
    this.animate();
  }
  resizeCanvas() {
    const container = this.canvas.parentElement;
    const width = container.clientWidth - 40;
    this.canvas.width = Math.min(800, width);
    this.canvas.height = 500;
  }
  addBall() {
    const radius = 15 + Math.random() * 20;
    const x = radius + Math.random() * (this.canvas.width - radius * 2);
    const y = radius + Math.random() * (this.canvas.height - radius * 2);
    const hue = 180 + Math.random() * 90;
    const saturation = 60 + Math.random() * 30;
    const lightness = 50 + Math.random() * 20;
    const alpha = 0.7 + Math.random() * 0.3;
    const ball = {
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
  clearBalls() {
    this.balls = [];
    this.collisionCount = 0;
    this.updateUI();
  }
  toggleGravity() {
    this.gravityEnabled = !this.gravityEnabled;
    this.gravityStatusElement.textContent = this.gravityEnabled ? "开" : "关";
    this.gravityBtn.classList.toggle("btn-toggle");
    this.gravityBtn.classList.toggle("btn-secondary");
  }
  updateFriction(e) {
    const slider = e.target;
    const value = parseInt(slider.value);
    this.friction = value / 100;
    this.frictionValueElement.textContent = this.friction.toFixed(2);
  }
  startDrag(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
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
  drag(e) {
    if (!this.isDragging || !this.draggedBall)
      return;
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    this.draggedBall.x = x;
    this.draggedBall.y = y;
    this.draggedBall.vx = (x - this.dragStartX) * 0.5;
    this.draggedBall.vy = (y - this.dragStartY) * 0.5;
  }
  endDrag() {
    if (this.draggedBall) {
      this.draggedBall.highlight = false;
    }
    this.isDragging = false;
    this.draggedBall = null;
  }
  updatePhysics() {
    for (const ball of this.balls) {
      if (ball === this.draggedBall && this.isDragging)
        continue;
      if (this.gravityEnabled) {
        ball.vy += this.gravity;
      }
      ball.vx *= 1 - this.friction * 0.1;
      ball.vy *= 1 - this.friction * 0.1;
      ball.x += ball.vx;
      ball.y += ball.vy;
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
    for (let i = 0;i < this.balls.length; i++) {
      for (let j = i + 1;j < this.balls.length; j++) {
        const ball1 = this.balls[i];
        const ball2 = this.balls[j];
        const dx = ball2.x - ball1.x;
        const dy = ball2.y - ball1.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance < ball1.radius + ball2.radius) {
          this.collisionCount++;
          const angle = Math.atan2(dy, dx);
          const targetX = ball1.x + Math.cos(angle) * (ball1.radius + ball2.radius);
          const targetY = ball1.y + Math.sin(angle) * (ball1.radius + ball2.radius);
          const ax = (targetX - ball2.x) * 0.05;
          const ay = (targetY - ball2.y) * 0.05;
          ball1.vx -= ax;
          ball1.vy -= ay;
          ball2.vx += ax;
          ball2.vy += ay;
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
  render() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    const gradient = this.ctx.createLinearGradient(0, 0, this.canvas.width, this.canvas.height);
    gradient.addColorStop(0, "rgba(15, 23, 42, 0.3)");
    gradient.addColorStop(1, "rgba(30, 41, 59, 0.3)");
    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    for (const ball of this.balls) {
      this.drawGlassBall(ball);
    }
    if (this.isDragging && this.draggedBall) {
      this.drawDragEffect(this.draggedBall);
    }
  }
  drawGlassBall(ball) {
    const { x, y, radius, color, highlight } = ball;
    this.ctx.beginPath();
    this.ctx.arc(x, y, radius, 0, Math.PI * 2);
    const gradient = this.ctx.createRadialGradient(x - radius * 0.3, y - radius * 0.3, 0, x, y, radius);
    if (highlight) {
      gradient.addColorStop(0, color.replace("hsla", "hsla").replace(/,[^)]+\)/, ", 1)"));
      gradient.addColorStop(0.7, color);
      gradient.addColorStop(1, color.replace("hsla", "hsla").replace(/,[^)]+\)/, ", 0.3)"));
    } else {
      gradient.addColorStop(0, color.replace("hsla", "hsla").replace(/,[^)]+\)/, ", 0.9)"));
      gradient.addColorStop(0.7, color);
      gradient.addColorStop(1, color.replace("hsla", "hsla").replace(/,[^)]+\)/, ", 0.2)"));
    }
    this.ctx.fillStyle = gradient;
    this.ctx.fill();
    this.ctx.beginPath();
    this.ctx.arc(x - radius * 0.2, y - radius * 0.2, radius * 0.4, 0, Math.PI * 2);
    const highlightGradient = this.ctx.createRadialGradient(x - radius * 0.2, y - radius * 0.2, 0, x - radius * 0.2, y - radius * 0.2, radius * 0.4);
    highlightGradient.addColorStop(0, "rgba(255, 255, 255, 0.8)");
    highlightGradient.addColorStop(1, "rgba(255, 255, 255, 0)");
    this.ctx.fillStyle = highlightGradient;
    this.ctx.fill();
    this.ctx.beginPath();
    this.ctx.arc(x, y, radius, 0, Math.PI * 2);
    this.ctx.strokeStyle = highlight ? "rgba(255, 255, 255, 0.8)" : "rgba(255, 255, 255, 0.3)";
    this.ctx.lineWidth = highlight ? 2 : 1;
    this.ctx.stroke();
    if (radius > 20) {
      this.ctx.beginPath();
      this.ctx.arc(x + radius * 0.3, y + radius * 0.3, radius * 0.2, 0, Math.PI * 2);
      this.ctx.fillStyle = "rgba(255, 255, 255, 0.1)";
      this.ctx.fill();
    }
  }
  drawDragEffect(ball) {
    const { x, y, radius } = ball;
    this.ctx.beginPath();
    this.ctx.moveTo(this.dragStartX, this.dragStartY);
    this.ctx.lineTo(x, y);
    this.ctx.strokeStyle = "rgba(0, 191, 255, 0.5)";
    this.ctx.lineWidth = 2;
    this.ctx.setLineDash([5, 5]);
    this.ctx.stroke();
    this.ctx.setLineDash([]);
    this.ctx.beginPath();
    this.ctx.arc(this.dragStartX, this.dragStartY, 5, 0, Math.PI * 2);
    this.ctx.fillStyle = "rgba(0, 191, 255, 0.8)";
    this.ctx.fill();
    const speed = Math.sqrt(ball.vx * ball.vx + ball.vy * ball.vy);
    if (speed > 0.5) {
      const angle = Math.atan2(ball.vy, ball.vx);
      const length = Math.min(speed * 10, 100);
      this.ctx.beginPath();
      this.ctx.moveTo(x, y);
      this.ctx.lineTo(x + Math.cos(angle) * length, y + Math.sin(angle) * length);
      this.ctx.strokeStyle = "rgba(255, 100, 100, 0.7)";
      this.ctx.lineWidth = 3;
      this.ctx.stroke();
      this.ctx.beginPath();
      this.ctx.moveTo(x + Math.cos(angle) * length, y + Math.sin(angle) * length);
      this.ctx.lineTo(x + Math.cos(angle - 0.5) * 10, y + Math.sin(angle - 0.5) * 10);
      this.ctx.lineTo(x + Math.cos(angle + 0.5) * 10, y + Math.sin(angle + 0.5) * 10);
      this.ctx.closePath();
      this.ctx.fillStyle = "rgba(255, 100, 100, 0.9)";
      this.ctx.fill();
    }
  }
  updateUI() {
    this.ballCountElement.textContent = this.balls.length.toString();
    this.collisionCountElement.textContent = this.collisionCount.toString();
    this.fpsElement.textContent = Math.round(this.fps).toString();
  }
  calculateFPS(timestamp) {
    this.frameCount++;
    if (timestamp - this.lastTime >= 1000) {
      this.fps = this.frameCount * 1000 / (timestamp - this.lastTime);
      this.frameCount = 0;
      this.lastTime = timestamp;
    }
  }
  animate = (timestamp) => {
    if (timestamp) {
      this.calculateFPS(timestamp);
    }
    this.updatePhysics();
    this.render();
    this.updateUI();
    this.animationId = requestAnimationFrame(this.animate);
  };
  destroy() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
  }
}
window.addEventListener("DOMContentLoaded", () => {
  const game = new GlassBallGame;
  window.glassBallGame = game;
  console.log("玻璃球游戏已启动！");
});

// game.ts
var canvas = document.getElementById("gameCanvas");
var ctx = canvas.getContext("2d");
var launchBtn = document.getElementById("launchBtn");
var resetBtn = document.getElementById("resetBtn");
var autoSolveBtn = document.getElementById("autoSolveBtn");
var hitCountEl = document.getElementById("hitCount");
var attemptCountEl = document.getElementById("attemptCount");
var efficiencyEl = document.getElementById("efficiency");
var activeConstraintsEl = document.getElementById("activeConstraints");
var targetPrecisionEl = document.getElementById("targetPrecision");
var gravitySlider = document.querySelector('[data-constraint="gravity"] .constraint-slider');
var frictionSlider = document.querySelector('[data-constraint="friction"] .constraint-slider');
var elasticitySlider = document.querySelector('[data-constraint="elasticity"] .constraint-slider');
var angleSlider = document.querySelector('[data-constraint="angle"] .constraint-slider');
var powerSlider = document.querySelector('[data-constraint="power"] .constraint-slider');
var gravityValue = document.querySelector('[data-constraint="gravity"] .value');
var frictionValue = document.querySelector('[data-constraint="friction"] .value');
var elasticityValue = document.querySelector('[data-constraint="elasticity"] .value');
var angleValue = document.querySelector('[data-constraint="angle"] .value');
var powerValue = document.querySelector('[data-constraint="power"] .value');
var gameState = {
  gravity: 9.81,
  friction: 0.2,
  elasticity: 0.8,
  launchAngle: 45,
  launchPower: 50,
  isSimulating: false,
  spherePosition: { x: 100, y: 500 },
  sphereVelocity: { x: 0, y: 0 },
  targetPosition: { x: 650, y: 450 },
  targetRadius: 40,
  hits: 0,
  attempts: 0,
  efficiency: 0,
  trailPoints: [],
  isAutoSolving: false
};
var TIME_STEP = 0.016;
var SPHERE_RADIUS = 15;
var GROUND_Y = 580;
var LAUNCH_X = 100;
var LAUNCH_Y = 500;
function init() {
  const yearElement = document.getElementById("currentYear");
  if (yearElement) {
    yearElement.textContent = new Date().getFullYear().toString();
  }
  updateConstraintDisplays();
  setupEventListeners();
  resetSimulation();
  draw();
}
function updateConstraintDisplays() {
  gravityValue.textContent = gameState.gravity.toFixed(2);
  frictionValue.textContent = gameState.friction.toFixed(2);
  elasticityValue.textContent = gameState.elasticity.toFixed(2);
  angleValue.textContent = gameState.launchAngle.toString();
  powerValue.textContent = gameState.launchPower.toString();
  const precision = calculatePrecision();
  targetPrecisionEl.textContent = precision;
  activeConstraintsEl.textContent = "5";
}
function calculatePrecision() {
  const stability = (1 - Math.abs(gameState.gravity - 9.81) / 20) * 0.3 + (1 - Math.abs(gameState.friction - 0.2) / 1) * 0.2 + (1 - Math.abs(gameState.elasticity - 0.8) / 1) * 0.2 + (1 - Math.abs(gameState.launchAngle - 45) / 90) * 0.15 + (1 - Math.abs(gameState.launchPower - 50) / 100) * 0.15;
  if (stability > 0.8)
    return "Ultra High";
  if (stability > 0.6)
    return "High";
  if (stability > 0.4)
    return "Medium";
  if (stability > 0.2)
    return "Low";
  return "Very Low";
}
function setupEventListeners() {
  gravitySlider.addEventListener("input", () => {
    gameState.gravity = parseFloat(gravitySlider.value);
    updateConstraintDisplays();
    if (!gameState.isSimulating)
      resetSimulation();
  });
  frictionSlider.addEventListener("input", () => {
    gameState.friction = parseFloat(frictionSlider.value);
    updateConstraintDisplays();
    if (!gameState.isSimulating)
      resetSimulation();
  });
  elasticitySlider.addEventListener("input", () => {
    gameState.elasticity = parseFloat(elasticitySlider.value);
    updateConstraintDisplays();
    if (!gameState.isSimulating)
      resetSimulation();
  });
  angleSlider.addEventListener("input", () => {
    gameState.launchAngle = parseFloat(angleSlider.value);
    updateConstraintDisplays();
    if (!gameState.isSimulating)
      resetSimulation();
  });
  powerSlider.addEventListener("input", () => {
    gameState.launchPower = parseFloat(powerSlider.value);
    updateConstraintDisplays();
    if (!gameState.isSimulating)
      resetSimulation();
  });
  launchBtn.addEventListener("click", () => {
    if (!gameState.isSimulating) {
      launchSphere();
    }
  });
  resetBtn.addEventListener("click", () => {
    resetSimulation();
  });
  autoSolveBtn.addEventListener("click", () => {
    if (!gameState.isAutoSolving) {
      startAutoSolve();
    }
  });
}
function launchSphere() {
  gameState.attempts++;
  gameState.isSimulating = true;
  gameState.trailPoints = [];
  const angleRad = gameState.launchAngle * Math.PI / 180;
  const velocityMagnitude = gameState.launchPower * 0.5;
  gameState.sphereVelocity = {
    x: Math.cos(angleRad) * velocityMagnitude,
    y: -Math.sin(angleRad) * velocityMagnitude
  };
  updateGameStats();
  simulate();
}
function resetSimulation() {
  gameState.isSimulating = false;
  gameState.isAutoSolving = false;
  gameState.spherePosition = { x: LAUNCH_X, y: LAUNCH_Y };
  gameState.sphereVelocity = { x: 0, y: 0 };
  gameState.trailPoints = [];
  draw();
}
function updateGameStats() {
  hitCountEl.textContent = gameState.hits.toString();
  attemptCountEl.textContent = gameState.attempts.toString();
  if (gameState.attempts > 0) {
    gameState.efficiency = Math.round(gameState.hits / gameState.attempts * 100);
  } else {
    gameState.efficiency = 0;
  }
  efficiencyEl.textContent = `${gameState.efficiency}%`;
}
function simulate() {
  if (!gameState.isSimulating)
    return;
  gameState.trailPoints.push({ ...gameState.spherePosition });
  if (gameState.trailPoints.length > 50) {
    gameState.trailPoints.shift();
  }
  updateSpherePosition();
  checkCollisions();
  draw();
  if (gameState.isSimulating) {
    requestAnimationFrame(simulate);
  }
}
function updateSpherePosition() {
  gameState.sphereVelocity.y += gameState.gravity * TIME_STEP;
  if (gameState.spherePosition.y + SPHERE_RADIUS >= GROUND_Y) {
    gameState.sphereVelocity.x *= 1 - gameState.friction * TIME_STEP;
  }
  gameState.spherePosition.x += gameState.sphereVelocity.x;
  gameState.spherePosition.y += gameState.sphereVelocity.y;
  if (gameState.spherePosition.x > canvas.width + 100 || gameState.spherePosition.y > canvas.height + 100 || Math.abs(gameState.sphereVelocity.x) < 0.1 && Math.abs(gameState.sphereVelocity.y) < 0.1 && gameState.spherePosition.y + SPHERE_RADIUS >= GROUND_Y - 1) {
    gameState.isSimulating = false;
  }
}
function checkCollisions() {
  if (gameState.spherePosition.y + SPHERE_RADIUS >= GROUND_Y) {
    gameState.spherePosition.y = GROUND_Y - SPHERE_RADIUS;
    gameState.sphereVelocity.y = -gameState.sphereVelocity.y * gameState.elasticity;
    if (Math.abs(gameState.sphereVelocity.y) < 0.5) {
      gameState.sphereVelocity.y = 0;
    }
  }
  if (gameState.spherePosition.x - SPHERE_RADIUS <= 0) {
    gameState.spherePosition.x = SPHERE_RADIUS;
    gameState.sphereVelocity.x = -gameState.sphereVelocity.x * gameState.elasticity;
  }
  if (gameState.spherePosition.x + SPHERE_RADIUS >= canvas.width) {
    gameState.spherePosition.x = canvas.width - SPHERE_RADIUS;
    gameState.sphereVelocity.x = -gameState.sphereVelocity.x * gameState.elasticity;
  }
  const dx = gameState.spherePosition.x - gameState.targetPosition.x;
  const dy = gameState.spherePosition.y - gameState.targetPosition.y;
  const distance = Math.sqrt(dx * dx + dy * dy);
  if (distance < SPHERE_RADIUS + gameState.targetRadius) {
    gameState.hits++;
    updateGameStats();
    flashTarget();
    gameState.isSimulating = false;
  }
}
function flashTarget() {
  const originalRadius = gameState.targetRadius;
  let flashCount = 0;
  const maxFlashes = 6;
  function flash() {
    if (flashCount >= maxFlashes) {
      gameState.targetRadius = originalRadius;
      draw();
      return;
    }
    gameState.targetRadius = originalRadius * (flashCount % 2 === 0 ? 1.5 : 1);
    draw();
    flashCount++;
    setTimeout(flash, 100);
  }
  flash();
}
function startAutoSolve() {
  if (gameState.isAutoSolving)
    return;
  gameState.isAutoSolving = true;
  autoSolveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Solving...';
  autoSolveBtn.classList.add("pulse");
  const initialConstraints = {
    gravity: gameState.gravity,
    friction: gameState.friction,
    elasticity: gameState.elasticity,
    angle: gameState.launchAngle,
    power: gameState.launchPower
  };
  let bestScore = -Infinity;
  let bestConstraints = { ...initialConstraints };
  const iterations = 50;
  let currentConstraints = { ...initialConstraints };
  function tryIteration(iteration) {
    if (iteration >= iterations || !gameState.isAutoSolving) {
      finishAutoSolve(bestConstraints);
      return;
    }
    const newConstraints = {
      gravity: Math.max(0.1, Math.min(20, currentConstraints.gravity + (Math.random() - 0.5) * 4)),
      friction: Math.max(0, Math.min(1, currentConstraints.friction + (Math.random() - 0.5) * 0.2)),
      elasticity: Math.max(0, Math.min(1, currentConstraints.elasticity + (Math.random() - 0.5) * 0.2)),
      angle: Math.max(0, Math.min(90, currentConstraints.angle + (Math.random() - 0.5) * 20)),
      power: Math.max(10, Math.min(100, currentConstraints.power + (Math.random() - 0.5) * 30))
    };
    const score = simulateConstraints(newConstraints);
    if (score > bestScore) {
      bestScore = score;
      bestConstraints = { ...newConstraints };
    }
    if (score > bestScore * 0.8 || Math.random() > 0.7) {
      currentConstraints = { ...newConstraints };
    }
    autoSolveBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Solving... ${Math.round((iteration + 1) / iterations * 100)}%`;
    setTimeout(() => tryIteration(iteration + 1), 50);
  }
  tryIteration(0);
}
function simulateConstraints(constraints) {
  const angleRad = constraints.angle * Math.PI / 180;
  const velocityMagnitude = constraints.power * 0.5;
  const vx = Math.cos(angleRad) * velocityMagnitude;
  const vy = -Math.sin(angleRad) * velocityMagnitude;
  const t = (vy + Math.sqrt(vy * vy + 2 * constraints.gravity * (LAUNCH_Y - GROUND_Y))) / constraints.gravity;
  const distance = vx * t;
  const targetDistance = gameState.targetPosition.x - LAUNCH_X;
  const error = Math.abs(distance - targetDistance);
  let score = 100 - error;
  if (Math.abs(constraints.gravity - 9.81) < 2)
    score += 10;
  if (constraints.friction > 0.1 && constraints.friction < 0.5)
    score += 5;
  if (constraints.elasticity > 0.5 && constraints.elasticity < 0.9)
    score += 5;
  return score;
}
function finishAutoSolve(bestConstraints) {
  gameState.isAutoSolving = false;
  gameState.gravity = bestConstraints.gravity;
  gameState.friction = bestConstraints.friction;
  gameState.elasticity = bestConstraints.elasticity;
  gameState.launchAngle = bestConstraints.angle;
  gameState.launchPower = bestConstraints.power;
  gravitySlider.value = gameState.gravity.toString();
  frictionSlider.value = gameState.friction.toString();
  elasticitySlider.value = gameState.elasticity.toString();
  angleSlider.value = gameState.launchAngle.toString();
  powerSlider.value = gameState.launchPower.toString();
  updateConstraintDisplays();
  resetSimulation();
  autoSolveBtn.innerHTML = '<i class="fas fa-robot"></i> Auto-Solve';
  autoSolveBtn.classList.remove("pulse");
  setTimeout(() => {
    launchSphere();
  }, 500);
}
function draw() {
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, "#0f172a");
  gradient.addColorStop(1, "#1e293b");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#334155";
  ctx.fillRect(0, GROUND_Y, canvas.width, canvas.height - GROUND_Y);
  ctx.strokeStyle = "#475569";
  ctx.lineWidth = 1;
  for (let i = 0;i < canvas.width; i += 20) {
    ctx.beginPath();
    ctx.moveTo(i, GROUND_Y);
    ctx.lineTo(i, canvas.height);
    ctx.stroke();
  }
  drawTarget();
  drawLaunchPlatform();
  drawConstraintVisualization();
  drawTrail();
  drawSphere();
  drawInfoText();
}
function drawTarget() {
  ctx.beginPath();
  ctx.arc(gameState.targetPosition.x, gameState.targetPosition.y, gameState.targetRadius, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(239, 68, 68, 0.3)";
  ctx.fill();
  ctx.strokeStyle = "#ef4444";
  ctx.lineWidth = 3;
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(gameState.targetPosition.x, gameState.targetPosition.y, gameState.targetRadius * 0.5, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(239, 68, 68, 0.6)";
  ctx.fill();
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(gameState.targetPosition.x - gameState.targetRadius, gameState.targetPosition.y);
  ctx.lineTo(gameState.targetPosition.x + gameState.targetRadius, gameState.targetPosition.y);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(gameState.targetPosition.x, gameState.targetPosition.y - gameState.targetRadius);
  ctx.lineTo(gameState.targetPosition.x, gameState.targetPosition.y + gameState.targetRadius);
  ctx.stroke();
}
function drawLaunchPlatform() {
  const platformWidth = 60;
  const platformHeight = 20;
  ctx.fillStyle = "#475569";
  ctx.fillRect(LAUNCH_X - platformWidth / 2, LAUNCH_Y + SPHERE_RADIUS, platformWidth, platformHeight);
  ctx.fillStyle = "#64748b";
  ctx.fillRect(LAUNCH_X - platformWidth / 2, LAUNCH_Y + SPHERE_RADIUS, platformWidth, 5);
  const angleRad = gameState.launchAngle * Math.PI / 180;
  const indicatorLength = 40;
  ctx.strokeStyle = "#10b981";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(LAUNCH_X, LAUNCH_Y);
  ctx.lineTo(LAUNCH_X + Math.cos(angleRad) * indicatorLength, LAUNCH_Y - Math.sin(angleRad) * indicatorLength);
  ctx.stroke();
}
function drawConstraintVisualization() {
  const startX = 20;
  const startY = 50;
  const barWidth = 20;
  const maxHeight = 100;
  const gravityHeight = gameState.gravity / 20 * maxHeight;
  ctx.fillStyle = "#0ea5e9";
  ctx.fillRect(startX, startY + maxHeight - gravityHeight, barWidth, gravityHeight);
  const frictionHeight = gameState.friction * maxHeight;
  ctx.fillStyle = "#8b5cf6";
  ctx.fillRect(startX + 40, startY + maxHeight - frictionHeight, barWidth, frictionHeight);
  const elasticityHeight = gameState.elasticity * maxHeight;
  ctx.fillStyle = "#10b981";
  ctx.fillRect(startX + 80, startY + maxHeight - elasticityHeight, barWidth, elasticityHeight);
  ctx.fillStyle = "#cbd5e1";
  ctx.font = "12px JetBrains Mono";
  ctx.fillText("Gravity", startX, startY + maxHeight + 20);
  ctx.fillText("Friction", startX + 40, startY + maxHeight + 20);
  ctx.fillText("Elasticity", startX + 80, startY + maxHeight + 20);
}
function drawTrail() {
  if (gameState.trailPoints.length < 2)
    return;
  ctx.strokeStyle = "rgba(14, 165, 233, 0.6)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(gameState.trailPoints[0].x, gameState.trailPoints[0].y);
  for (let i = 1;i < gameState.trailPoints.length; i++) {
    ctx.lineTo(gameState.trailPoints[i].x, gameState.trailPoints[i].y);
  }
  ctx.stroke();
  ctx.fillStyle = "rgba(14, 165, 233, 0.8)";
  for (let i = 0;i < gameState.trailPoints.length; i += 5) {
    ctx.beginPath();
    ctx.arc(gameState.trailPoints[i].x, gameState.trailPoints[i].y, 2, 0, Math.PI * 2);
    ctx.fill();
  }
}
function drawSphere() {
  const { x, y } = gameState.spherePosition;
  ctx.beginPath();
  ctx.ellipse(x, y + SPHERE_RADIUS / 2, SPHERE_RADIUS * 0.8, SPHERE_RADIUS * 0.3, 0, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(0, 0, 0, 0.3)";
  ctx.fill();
  const gradient = ctx.createRadialGradient(x - SPHERE_RADIUS * 0.3, y - SPHERE_RADIUS * 0.3, 1, x, y, SPHERE_RADIUS);
  gradient.addColorStop(0, "rgba(14, 165, 233, 0.9)");
  gradient.addColorStop(0.7, "rgba(3, 105, 161, 0.8)");
  gradient.addColorStop(1, "rgba(2, 75, 115, 0.6)");
  ctx.beginPath();
  ctx.arc(x, y, SPHERE_RADIUS, 0, Math.PI * 2);
  ctx.fillStyle = gradient;
  ctx.fill();
  ctx.beginPath();
  ctx.arc(x - SPHERE_RADIUS * 0.3, y - SPHERE_RADIUS * 0.3, SPHERE_RADIUS * 0.3, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
  ctx.fill();
  ctx.strokeStyle = "rgba(255, 255, 255, 0.6)";
  ctx.lineWidth = 1.5;
  ctx.stroke();
  if (gameState.isSimulating) {
    ctx.strokeStyle = "#f59e0b";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + gameState.sphereVelocity.x * 0.5, y + gameState.sphereVelocity.y * 0.5);
    ctx.stroke();
  }
}
function drawInfoText() {
  ctx.fillStyle = "#f1f5f9";
  ctx.font = "14px JetBrains Mono";
  ctx.fillText(`Gravity: ${gameState.gravity.toFixed(2)} m/s²`, 20, 30);
  ctx.fillText(`Angle: ${gameState.launchAngle}°`, 180, 30);
  ctx.fillText(`Power: ${gameState.launchPower}%`, 320, 30);
  if (gameState.isSimulating) {
    ctx.fillStyle = "#10b981";
    ctx.font = "bold 16px JetBrains Mono";
    ctx.fillText("SIMULATING...", canvas.width - 150, 30);
  } else if (gameState.isAutoSolving) {
    ctx.fillStyle = "#8b5cf6";
    ctx.font = "bold 16px JetBrains Mono";
    ctx.fillText("AUTO-SOLVING...", canvas.width - 170, 30);
  }
}
window.addEventListener("load", init);

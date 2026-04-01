// Glass Sphere Game - Bottle #030
// Core Philosophy: "Collect all constraints, find the optimal solution"

// Game State Interface
interface GameState {
    gravity: number;
    friction: number;
    elasticity: number;
    launchAngle: number;
    launchPower: number;
    isSimulating: boolean;
    spherePosition: { x: number; y: number };
    sphereVelocity: { x: number; y: number };
    targetPosition: { x: number; y: number };
    targetRadius: number;
    hits: number;
    attempts: number;
    efficiency: number;
    trailPoints: Array<{ x: number; y: number }>;
    isAutoSolving: boolean;
}

// DOM Elements
const canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
const ctx = canvas.getContext('2d')!;
const launchBtn = document.getElementById('launchBtn')!;
const resetBtn = document.getElementById('resetBtn')!;
const autoSolveBtn = document.getElementById('autoSolveBtn')!;
const hitCountEl = document.getElementById('hitCount')!;
const attemptCountEl = document.getElementById('attemptCount')!;
const efficiencyEl = document.getElementById('efficiency')!;
const activeConstraintsEl = document.getElementById('activeConstraints')!;
const targetPrecisionEl = document.getElementById('targetPrecision')!;

// Constraint Sliders
const gravitySlider = document.querySelector('[data-constraint="gravity"] .constraint-slider') as HTMLInputElement;
const frictionSlider = document.querySelector('[data-constraint="friction"] .constraint-slider') as HTMLInputElement;
const elasticitySlider = document.querySelector('[data-constraint="elasticity"] .constraint-slider') as HTMLInputElement;
const angleSlider = document.querySelector('[data-constraint="angle"] .constraint-slider') as HTMLInputElement;
const powerSlider = document.querySelector('[data-constraint="power"] .constraint-slider') as HTMLInputElement;

// Constraint Value Displays
const gravityValue = document.querySelector('[data-constraint="gravity"] .value')!;
const frictionValue = document.querySelector('[data-constraint="friction"] .value')!;
const elasticityValue = document.querySelector('[data-constraint="elasticity"] .value')!;
const angleValue = document.querySelector('[data-constraint="angle"] .value')!;
const powerValue = document.querySelector('[data-constraint="power"] .value')!;

// Initial Game State
const gameState: GameState = {
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

// Physics Constants
const TIME_STEP = 0.016; // Approximately 60 FPS
const SPHERE_RADIUS = 15;
const GROUND_Y = 580;
const LAUNCH_X = 100;
const LAUNCH_Y = 500;

// Initialize game
function init() {
    // Update current year in footer
    const yearElement = document.getElementById('currentYear');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear().toString();
    }
    
    updateConstraintDisplays();
    setupEventListeners();
    resetSimulation();
    draw();
}

// Update constraint value displays
function updateConstraintDisplays() {
    gravityValue.textContent = gameState.gravity.toFixed(2);
    frictionValue.textContent = gameState.friction.toFixed(2);
    elasticityValue.textContent = gameState.elasticity.toFixed(2);
    angleValue.textContent = gameState.launchAngle.toString();
    powerValue.textContent = gameState.launchPower.toString();
    
    // Update precision based on constraints
    const precision = calculatePrecision();
    targetPrecisionEl.textContent = precision;
    activeConstraintsEl.textContent = '5'; // All 5 constraints are always active
}

// Calculate target precision based on constraints
function calculatePrecision(): string {
    const stability = 
        (1 - Math.abs(gameState.gravity - 9.81) / 20) * 0.3 +
        (1 - Math.abs(gameState.friction - 0.2) / 1) * 0.2 +
        (1 - Math.abs(gameState.elasticity - 0.8) / 1) * 0.2 +
        (1 - Math.abs(gameState.launchAngle - 45) / 90) * 0.15 +
        (1 - Math.abs(gameState.launchPower - 50) / 100) * 0.15;
    
    if (stability > 0.8) return 'Ultra High';
    if (stability > 0.6) return 'High';
    if (stability > 0.4) return 'Medium';
    if (stability > 0.2) return 'Low';
    return 'Very Low';
}

// Setup event listeners
function setupEventListeners() {
    // Constraint sliders
    gravitySlider.addEventListener('input', () => {
        gameState.gravity = parseFloat(gravitySlider.value);
        updateConstraintDisplays();
        if (!gameState.isSimulating) resetSimulation();
    });
    
    frictionSlider.addEventListener('input', () => {
        gameState.friction = parseFloat(frictionSlider.value);
        updateConstraintDisplays();
        if (!gameState.isSimulating) resetSimulation();
    });
    
    elasticitySlider.addEventListener('input', () => {
        gameState.elasticity = parseFloat(elasticitySlider.value);
        updateConstraintDisplays();
        if (!gameState.isSimulating) resetSimulation();
    });
    
    angleSlider.addEventListener('input', () => {
        gameState.launchAngle = parseFloat(angleSlider.value);
        updateConstraintDisplays();
        if (!gameState.isSimulating) resetSimulation();
    });
    
    powerSlider.addEventListener('input', () => {
        gameState.launchPower = parseFloat(powerSlider.value);
        updateConstraintDisplays();
        if (!gameState.isSimulating) resetSimulation();
    });
    
    // Control buttons
    launchBtn.addEventListener('click', () => {
        if (!gameState.isSimulating) {
            launchSphere();
        }
    });
    
    resetBtn.addEventListener('click', () => {
        resetSimulation();
    });
    
    autoSolveBtn.addEventListener('click', () => {
        if (!gameState.isAutoSolving) {
            startAutoSolve();
        }
    });
}

// Launch the sphere with current constraints
function launchSphere() {
    gameState.attempts++;
    gameState.isSimulating = true;
    gameState.trailPoints = [];
    
    // Convert angle to radians
    const angleRad = gameState.launchAngle * Math.PI / 180;
    
    // Calculate initial velocity based on power (scaled appropriately)
    const velocityMagnitude = gameState.launchPower * 0.5;
    gameState.sphereVelocity = {
        x: Math.cos(angleRad) * velocityMagnitude,
        y: -Math.sin(angleRad) * velocityMagnitude
    };
    
    // Update UI
    updateGameStats();
    
    // Start simulation loop
    simulate();
}

// Reset simulation to initial state
function resetSimulation() {
    gameState.isSimulating = false;
    gameState.isAutoSolving = false;
    gameState.spherePosition = { x: LAUNCH_X, y: LAUNCH_Y };
    gameState.sphereVelocity = { x: 0, y: 0 };
    gameState.trailPoints = [];
    draw();
}

// Update game statistics
function updateGameStats() {
    hitCountEl.textContent = gameState.hits.toString();
    attemptCountEl.textContent = gameState.attempts.toString();
    
    if (gameState.attempts > 0) {
        gameState.efficiency = Math.round((gameState.hits / gameState.attempts) * 100);
    } else {
        gameState.efficiency = 0;
    }
    
    efficiencyEl.textContent = `${gameState.efficiency}%`;
}

// Main simulation loop
function simulate() {
    if (!gameState.isSimulating) return;
    
    // Add current position to trail
    gameState.trailPoints.push({ ...gameState.spherePosition });
    
    // Limit trail length
    if (gameState.trailPoints.length > 50) {
        gameState.trailPoints.shift();
    }
    
    // Apply physics
    updateSpherePosition();
    
    // Check for collisions
    checkCollisions();
    
    // Draw updated state
    draw();
    
    // Continue simulation if still active
    if (gameState.isSimulating) {
        requestAnimationFrame(simulate);
    }
}

// Update sphere position based on physics
function updateSpherePosition() {
    // Apply gravity
    gameState.sphereVelocity.y += gameState.gravity * TIME_STEP;
    
    // Apply friction (only when touching ground)
    if (gameState.spherePosition.y + SPHERE_RADIUS >= GROUND_Y) {
        gameState.sphereVelocity.x *= (1 - gameState.friction * TIME_STEP);
    }
    
    // Update position
    gameState.spherePosition.x += gameState.sphereVelocity.x;
    gameState.spherePosition.y += gameState.sphereVelocity.y;
    
    // Check if sphere has left the canvas or come to rest
    if (
        gameState.spherePosition.x > canvas.width + 100 ||
        gameState.spherePosition.y > canvas.height + 100 ||
        (Math.abs(gameState.sphereVelocity.x) < 0.1 && 
         Math.abs(gameState.sphereVelocity.y) < 0.1 &&
         gameState.spherePosition.y + SPHERE_RADIUS >= GROUND_Y - 1)
    ) {
        gameState.isSimulating = false;
    }
}

// Check for collisions with ground and target
function checkCollisions() {
    // Ground collision
    if (gameState.spherePosition.y + SPHERE_RADIUS >= GROUND_Y) {
        gameState.spherePosition.y = GROUND_Y - SPHERE_RADIUS;
        gameState.sphereVelocity.y = -gameState.sphereVelocity.y * gameState.elasticity;
        
        // If velocity is very low, stop the simulation
        if (Math.abs(gameState.sphereVelocity.y) < 0.5) {
            gameState.sphereVelocity.y = 0;
        }
    }
    
    // Left and right wall collisions
    if (gameState.spherePosition.x - SPHERE_RADIUS <= 0) {
        gameState.spherePosition.x = SPHERE_RADIUS;
        gameState.sphereVelocity.x = -gameState.sphereVelocity.x * gameState.elasticity;
    }
    
    if (gameState.spherePosition.x + SPHERE_RADIUS >= canvas.width) {
        gameState.spherePosition.x = canvas.width - SPHERE_RADIUS;
        gameState.sphereVelocity.x = -gameState.sphereVelocity.x * gameState.elasticity;
    }
    
    // Target collision
    const dx = gameState.spherePosition.x - gameState.targetPosition.x;
    const dy = gameState.spherePosition.y - gameState.targetPosition.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    if (distance < SPHERE_RADIUS + gameState.targetRadius) {
        // Hit the target!
        gameState.hits++;
        updateGameStats();
        
        // Visual feedback
        flashTarget();
        
        // Stop simulation
        gameState.isSimulating = false;
    }
}

// Visual effect for target hit
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

// Start auto-solving algorithm
function startAutoSolve() {
    if (gameState.isAutoSolving) return;
    
    gameState.isAutoSolving = true;
    autoSolveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Solving...';
    autoSolveBtn.classList.add('pulse');
    
    // Simple optimization algorithm
    const initialConstraints = {
        gravity: gameState.gravity,
        friction: gameState.friction,
        elasticity: gameState.elasticity,
        angle: gameState.launchAngle,
        power: gameState.launchPower
    };
    
    let bestScore = -Infinity;
    let bestConstraints = { ...initialConstraints };
    
    // Simulated annealing approach
    const iterations = 50;
    let currentConstraints = { ...initialConstraints };
    
    function tryIteration(iteration: number) {
        if (iteration >= iterations || !gameState.isAutoSolving) {
            finishAutoSolve(bestConstraints);
            return;
        }
        
        // Randomly adjust constraints
        const newConstraints = {
            gravity: Math.max(0.1, Math.min(20, currentConstraints.gravity + (Math.random() - 0.5) * 4)),
            friction: Math.max(0, Math.min(1, currentConstraints.friction + (Math.random() - 0.5) * 0.2)),
            elasticity: Math.max(0, Math.min(1, currentConstraints.elasticity + (Math.random() - 0.5) * 0.2)),
            angle: Math.max(0, Math.min(90, currentConstraints.angle + (Math.random() - 0.5) * 20)),
            power: Math.max(10, Math.min(100, currentConstraints.power + (Math.random() - 0.5) * 30))
        };
        
        // Simulate with these constraints
        const score = simulateConstraints(newConstraints);
        
        // Keep best solution
        if (score > bestScore) {
            bestScore = score;
            bestConstraints = { ...newConstraints };
        }
        
        // Sometimes accept worse solutions (simulated annealing)
        if (score > bestScore * 0.8 || Math.random() > 0.7) {
            currentConstraints = { ...newConstraints };
        }
        
        // Update UI with progress
        autoSolveBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Solving... ${Math.round((iteration + 1) / iterations * 100)}%`;
        
        // Continue with next iteration
        setTimeout(() => tryIteration(iteration + 1), 50);
    }
    
    tryIteration(0);
}

// Simulate constraints and return a score
function simulateConstraints(constraints: { gravity: number; friction: number; elasticity: number; angle: number; power: number }): number {
    // Simplified simulation - calculate if sphere would hit target
    const angleRad = constraints.angle * Math.PI / 180;
    const velocityMagnitude = constraints.power * 0.5;
    
    // Simple projectile motion calculation (ignoring friction for scoring)
    const vx = Math.cos(angleRad) * velocityMagnitude;
    const vy = -Math.sin(angleRad) * velocityMagnitude;
    
    // Time to hit ground
    const t = (vy + Math.sqrt(vy * vy + 2 * constraints.gravity * (LAUNCH_Y - GROUND_Y))) / constraints.gravity;
    
    // Horizontal distance
    const distance = vx * t;
    
    // Score based on distance from target
    const targetDistance = gameState.targetPosition.x - LAUNCH_X;
    const error = Math.abs(distance - targetDistance);
    
    // Higher score for better accuracy
    let score = 100 - error;
    
    // Bonus for using "realistic" constraints
    if (Math.abs(constraints.gravity - 9.81) < 2) score += 10;
    if (constraints.friction > 0.1 && constraints.friction < 0.5) score += 5;
    if (constraints.elasticity > 0.5 && constraints.elasticity < 0.9) score += 5;
    
    return score;
}

// Finish auto-solve and apply best constraints
function finishAutoSolve(bestConstraints: { gravity: number; friction: number; elasticity: number; angle: number; power: number }) {
    gameState.isAutoSolving = false;
    
    // Apply best constraints
    gameState.gravity = bestConstraints.gravity;
    gameState.friction = bestConstraints.friction;
    gameState.elasticity = bestConstraints.elasticity;
    gameState.launchAngle = bestConstraints.angle;
    gameState.launchPower = bestConstraints.power;
    
    // Update sliders
    gravitySlider.value = gameState.gravity.toString();
    frictionSlider.value = gameState.friction.toString();
    elasticitySlider.value = gameState.elasticity.toString();
    angleSlider.value = gameState.launchAngle.toString();
    powerSlider.value = gameState.launchPower.toString();
    
    updateConstraintDisplays();
    resetSimulation();
    
    // Restore button
    autoSolveBtn.innerHTML = '<i class="fas fa-robot"></i> Auto-Solve';
    autoSolveBtn.classList.remove('pulse');
    
    // Show success message
    setTimeout(() => {
        launchSphere();
    }, 500);
}

// Draw everything on canvas
function draw() {
    // Clear canvas with gradient background
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, '#0f172a');
    gradient.addColorStop(1, '#1e293b');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw ground
    ctx.fillStyle = '#334155';
    ctx.fillRect(0, GROUND_Y, canvas.width, canvas.height - GROUND_Y);
    
    // Draw ground texture
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 1;
    for (let i = 0; i < canvas.width; i += 20) {
        ctx.beginPath();
        ctx.moveTo(i, GROUND_Y);
        ctx.lineTo(i, canvas.height);
        ctx.stroke();
    }
    
    // Draw target
    drawTarget();
    
    // Draw launch platform
    drawLaunchPlatform();
    
    // Draw constraint visualization
    drawConstraintVisualization();
    
    // Draw trail
    drawTrail();
    
    // Draw sphere
    drawSphere();
    
    // Draw information text
    drawInfoText();
}

// Draw the target area
function drawTarget() {
    // Target outer circle
    ctx.beginPath();
    ctx.arc(gameState.targetPosition.x, gameState.targetPosition.y, gameState.targetRadius, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(239, 68, 68, 0.3)';
    ctx.fill();
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 3;
    ctx.stroke();
    
    // Target inner circle
    ctx.beginPath();
    ctx.arc(gameState.targetPosition.x, gameState.targetPosition.y, gameState.targetRadius * 0.5, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(239, 68, 68, 0.6)';
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Target crosshairs
    ctx.strokeStyle = '#ffffff';
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

// Draw launch platform
function drawLaunchPlatform() {
    const platformWidth = 60;
    const platformHeight = 20;
    
    // Platform base
    ctx.fillStyle = '#475569';
    ctx.fillRect(LAUNCH_X - platformWidth / 2, LAUNCH_Y + SPHERE_RADIUS, platformWidth, platformHeight);
    
    // Platform details
    ctx.fillStyle = '#64748b';
    ctx.fillRect(LAUNCH_X - platformWidth / 2, LAUNCH_Y + SPHERE_RADIUS, platformWidth, 5);
    
    // Angle indicator
    const angleRad = gameState.launchAngle * Math.PI / 180;
    const indicatorLength = 40;
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(LAUNCH_X, LAUNCH_Y);
    ctx.lineTo(
        LAUNCH_X + Math.cos(angleRad) * indicatorLength,
        LAUNCH_Y - Math.sin(angleRad) * indicatorLength
    );
    ctx.stroke();
}

// Draw constraint visualization
function drawConstraintVisualization() {
    const startX = 20;
    const startY = 50;
    const barWidth = 20;
    const maxHeight = 100;
    
    // Gravity bar
    const gravityHeight = (gameState.gravity / 20) * maxHeight;
    ctx.fillStyle = '#0ea5e9';
    ctx.fillRect(startX, startY + maxHeight - gravityHeight, barWidth, gravityHeight);
    
    // Friction bar
    const frictionHeight = gameState.friction * maxHeight;
    ctx.fillStyle = '#8b5cf6';
    ctx.fillRect(startX + 40, startY + maxHeight - frictionHeight, barWidth, frictionHeight);
    
    // Elasticity bar
    const elasticityHeight = gameState.elasticity * maxHeight;
    ctx.fillStyle = '#10b981';
    ctx.fillRect(startX + 80, startY + maxHeight - elasticityHeight, barWidth, elasticityHeight);
    
    // Labels
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '12px JetBrains Mono';
    ctx.fillText('Gravity', startX, startY + maxHeight + 20);
    ctx.fillText('Friction', startX + 40, startY + maxHeight + 20);
    ctx.fillText('Elasticity', startX + 80, startY + maxHeight + 20);
}

// Draw sphere trail
function drawTrail() {
    if (gameState.trailPoints.length < 2) return;
    
    ctx.strokeStyle = 'rgba(14, 165, 233, 0.6)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(gameState.trailPoints[0].x, gameState.trailPoints[0].y);
    
    for (let i = 1; i < gameState.trailPoints.length; i++) {
        ctx.lineTo(gameState.trailPoints[i].x, gameState.trailPoints[i].y);
    }
    ctx.stroke();
    
    // Draw trail dots
    ctx.fillStyle = 'rgba(14, 165, 233, 0.8)';
    for (let i = 0; i < gameState.trailPoints.length; i += 5) {
        ctx.beginPath();
        ctx.arc(gameState.trailPoints[i].x, gameState.trailPoints[i].y, 2, 0, Math.PI * 2);
        ctx.fill();
    }
}

// Draw the glass sphere
function drawSphere() {
    const { x, y } = gameState.spherePosition;
    
    // Sphere shadow
    ctx.beginPath();
    ctx.ellipse(x, y + SPHERE_RADIUS / 2, SPHERE_RADIUS * 0.8, SPHERE_RADIUS * 0.3, 0, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
    ctx.fill();
    
    // Sphere gradient
    const gradient = ctx.createRadialGradient(
        x - SPHERE_RADIUS * 0.3, y - SPHERE_RADIUS * 0.3, 1,
        x, y, SPHERE_RADIUS
    );
    gradient.addColorStop(0, 'rgba(14, 165, 233, 0.9)');
    gradient.addColorStop(0.7, 'rgba(3, 105, 161, 0.8)');
    gradient.addColorStop(1, 'rgba(2, 75, 115, 0.6)');
    
    // Sphere body
    ctx.beginPath();
    ctx.arc(x, y, SPHERE_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();
    
    // Sphere highlight
    ctx.beginPath();
    ctx.arc(x - SPHERE_RADIUS * 0.3, y - SPHERE_RADIUS * 0.3, SPHERE_RADIUS * 0.3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.fill();
    
    // Sphere border
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    
    // If simulating, draw velocity vector
    if (gameState.isSimulating) {
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + gameState.sphereVelocity.x * 0.5, y + gameState.sphereVelocity.y * 0.5);
        ctx.stroke();
    }
}

// Draw information text
function drawInfoText() {
    ctx.fillStyle = '#f1f5f9';
    ctx.font = '14px JetBrains Mono';
    
    // Current constraints
    ctx.fillText(`Gravity: ${gameState.gravity.toFixed(2)} m/s²`, 20, 30);
    ctx.fillText(`Angle: ${gameState.launchAngle}°`, 180, 30);
    ctx.fillText(`Power: ${gameState.launchPower}%`, 320, 30);
    
    // Status
    if (gameState.isSimulating) {
        ctx.fillStyle = '#10b981';
        ctx.font = 'bold 16px JetBrains Mono';
        ctx.fillText('SIMULATING...', canvas.width - 150, 30);
    } else if (gameState.isAutoSolving) {
        ctx.fillStyle = '#8b5cf6';
        ctx.font = 'bold 16px JetBrains Mono';
        ctx.fillText('AUTO-SOLVING...', canvas.width - 170, 30);
    }
}

// Initialize game when page loads
window.addEventListener('load', init);

// Export for TypeScript module (no actual exports needed)
export {};
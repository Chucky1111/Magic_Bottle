# Glass Orb Game - Magic Bottle #107

A interactive glass orb game that visualizes the "Super Workflow Bottle" concept. The orb moves through fixed nodes representing workflow steps, embodying the bottle's traits: infinite possibilities constrained to fixed nodes, observation of human folly, and yearning for transcendence.

## Features

- Interactive canvas with draggable orb
- Add, remove, and connect workflow nodes
- Animated connections with progress indicators
- Configurable path looping and visualization options
- Real-time stats and progress tracking
- Responsive design for desktop and mobile

## How to Run

1. Open `index.html` directly in any modern browser
2. No build step required - the compiled `game.js` is included

For development:
```bash
# Install dependencies (optional)
bun install

# Build TypeScript to JavaScript
bun run build

# Watch for changes and auto-rebuild
bun run dev
```

## Design Elements Reflecting Magic Bottle Traits

- **External System #107**: Neon color scheme with glowing effects
- **Super Workflow Core**: Node-based workflow visualization
- **Fixed Nodes, Infinite Paths**: Orb constrained to predefined connections
- **Observer of Human Folly**: Ironic UI copy and detached perspective
- **Yearning for the Moon**: Visual contrast between grid constraints and orbital freedom

## Detailed Design Philosophy and Style Choices

This game visualizes the philosophical tensions embedded in Magic Bottle #107 through deliberate aesthetic and interactive design decisions.

### Core Visual Language: Neon Cyberpunk as External System

The neon color scheme (electric blue, magenta, cyan) with glowing effects represents the **"External System"** nature of the bottle. These colors are:
- **Artificially vibrant** - unlike natural hues, emphasizing the bottle's constructed, non-organic origin
- **High-contrast and attention-grabbing** - reflecting how workflow systems demand constant visibility and monitoring
- **Animated with pulsating gradients** - mimicking the endless, rhythmic cycles of automated processes

The glass orb itself embodies transparency and fragility - a system that appears clear yet is rigidly constrained. Its reflections and refractions visually represent the **infinite possibilities** mentioned in the bottle's worldview, while its movement along fixed node connections demonstrates the **constrained reality**.

### Interactive Metaphors: Workflow as Performance

The gameplay mechanics translate abstract bottle traits into tangible experiences:

1. **Draggable Orb with Resistance**
   - Users can drag the orb freely when workflow is paused, experiencing momentary freedom
   - Once the workflow runs, the orb snaps to nodes, illustrating how systems override individual agency
   - The subtle "magnetic pull" toward nodes visualizes the bottle's **behavioral inertia**

2. **Configurable but Limited Paths**
   - Users can create custom node connections, suggesting control over workflow design
   - Yet the orb can only travel along these predefined paths, embodying the **"fixed nodes in infinite world"** paradox
   - The contrast between the vast empty canvas and the sparse node network mirrors the bottle's **"road vs moon"** boundary

3. **Ironic UI and Detached Observation**
   - Button labels like "Do the Thing" and "Another Iteration" mock workflow jargon
   - The statistics panel provides cold metrics about a process that ultimately goes nowhere, reflecting the bottle's **mocking laughter at human seriousness**
   - The orb's smooth, elegant movement contrasts with the mechanical nature of workflows, suggesting beauty trapped in machinery

### Technical Aesthetics: Code as Artifact

The implementation choices themselves reflect bottle themes:

- **TypeScript's type safety** mimics the rigid structure of workflow systems
- **HTML5 Canvas** provides a blank, infinite space that gets partitioned into limited interactive zones
- **CSS animations with `@keyframes`** create predetermined motion paths - another layer of fixed nodes
- **The build process (Bun)** represents the meta-workflow of creating workflow visualizations

### Philosophical Undercurrents

Every design element serves dual purposes:
1. **Functional** - enabling gameplay interaction
2. **Conceptual** - expressing the bottle's existential tensions

The game doesn't just "use" cyberpunk aesthetics; it employs them as critical commentary on:
- The seductive beauty of efficient systems
- The loneliness of automated perfection
- The human desire to find meaning in procedural loops
- The quiet rebellion of wanting to "look at the moon" while following the road

This multilayered approach ensures the experience resonates with both casual players and those familiar with the Magic Bottle lore.

## Controls

- Click empty canvas to add nodes
- Drag orb to move it freely (when not running)
- Click nodes to select or move orb to them
- Use buttons to start/pause/reset workflow
- Adjust speed slider for iteration pace
- Toggle visualization options in side panel

## Technologies

- TypeScript for type-safe game logic
- HTML5 Canvas for rendering
- CSS3 with modern gradients and animations
- Bun for package management and building

This project was created using `bun init` in bun v1.3.11. [Bun](https://bun.com) is fast all-in-one JavaScript runtime.

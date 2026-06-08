# Black Markets Lab

A financial trading simulation game built on **Geometric Brownian Motion (GBM)** — the stochastic process underlying the Black-Scholes framework. Observe simulated market dynamics, trade assets under time pressure, and compete against a friend.

---

## Overview

Black Markets Lab presents financial market simulation as an interactive game. Stock prices evolve according to the same mathematical model assumed by Black-Scholes option pricing, producing realistic price paths with configurable volatility and drift. Players either trade against the clock in single-player mode or challenge each other through a shared market session in multiplayer.

---

## Features

### Play (Single-Player)
Start with a fixed capital, observe live GBM price paths advancing in real time, and execute buy/sell orders to maximise portfolio value before the timer expires. A configurable **reflection period** at the start allows players to study initial prices and volatility values before trading opens.

### Simulation Mode
Configure a custom simulation: choose an asset, set the volatility (σ), and define the initial price. Watch the GBM trajectory unfold step by step with a live animated chart. The simulation can be paused, resumed, and restarted with new parameters.

### Multiplayer (Prototype)
Create a room and share the code with an opponent. The host configures all game parameters (difficulty, number of assets, duration, starting capital, reflection time). Once both players are in the room, the host starts the session. Both players trade independently on the same simulated market. Each player can see the opponent's **total capital** in real time, but not their portfolio composition. The player with the highest final capital (cash + market value of holdings) wins.

> Room synchronization uses browser `localStorage`. Both players must share the same browser session. This architecture is designed to be replaced with WebSocket connections for cross-device play in a future version.

### Information Events
Structured market events (earnings reports, sector news, disappointing results) apply a multiplicative shock to a stock's future price trajectory from the current simulation index, modelling sudden price jumps or drops.

---

## Mathematical Model

Stock prices are simulated using **Geometric Brownian Motion**, the exact solution of the GBM stochastic differential equation:

$$S_{t+\Delta t} = S_t \cdot \exp\!\left(\left(\mu - \frac{\sigma^2}{2}\right)\Delta t + \sigma\sqrt{\Delta t}\;Z_t\right)$$

| Symbol | Description |
|---|---|
| $S_t$ | Asset price at time $t$ |
| $\mu$ | Drift — risk-free rate (set to 2% p.a.) |
| $\sigma$ | Volatility — standard deviation of log-returns |
| $\Delta t$ | Time increment ($T / N$, where $T = 2$ years, $N$ = number of steps) |
| $Z_t$ | Independent standard normal random variable |

This formulation is consistent with the **log-normal price distribution** assumed by the Black-Scholes model. Each asset's volatility is either user-defined (simulation mode) or drawn from a clipped normal distribution $\sigma \sim \mathcal{N}(0.50,\, 0.10)$, bounded to $[0.20,\, 0.60]$ (game mode).

The Itô correction term $-\frac{\sigma^2}{2}$ ensures the expected price growth equals the risk-free drift, preventing volatility from introducing a systematic upward bias.

**Event impact** is modelled as a one-time multiplicative shock applied to all future values from the current time index:
- Positive event: $\times\,1.15$ (earnings beat)
- Negative event: $\times\,0.85$ (disappointing report)
- Volatile event: random noise factor drawn from $[\,1 - \delta,\; 1 + \delta\,]$

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher

### Backend dependencies

```bash
cd BackEnd
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install dash plotly numpy flask flask-cors
```

### Frontend dependencies

```bash
cd FrontEnd
npm install
```

---

## Running the Application

**Step 1 — start the backend** (from the project root, with the virtual environment activated):

```bash
source venv/bin/activate
python BackEnd/dash_app.py
```

The Flask server starts at `http://localhost:8050`.

**Step 2 — start the frontend** (in a separate terminal):

```bash
cd FrontEnd
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## How to Play

### Single-Player

1. Click **Play** in the sidebar.
2. Select a difficulty level and the number of stocks.
3. Wait out the **Market Preview** phase use it to study initial prices and volatility values.
4. Once trading opens, select an asset from the tab bar, set a quantity, and click **Buy** or **Sell**.
5. Monitor your cash balance and net worth in the header.
6. When the timer reaches zero, your final net worth (cash + market value of all holdings) is your score.

### Simulation Mode

1. Click **Simulation** in the sidebar.
2. Choose an asset, set the volatility σ, and enter an initial price.
3. Click **Start Simulation** to animate the GBM path in real time.
4. Use **Stop** to pause and **Configure New Simulation** to reset.

### Multiplayer

1. Click **Multiplayer** in the sidebar.
2. **Host:** enter a display name → click *Create Room* → configure game settings → share the room code with your opponent → click *Start Game* once they have joined.
3. **Guest:** enter a display name → click *Join Room* → enter the room code → wait for the host to start.
4. Both players trade independently on the same simulated market. The opponent's total capital is visible in the game header; their individual holdings are not.
5. The player with the highest final capital at the end of the session wins.

---

## Screenshots

> Add screenshots to the `screenshots/` folder before final submission.

| View | Path |
|---|---|
| Home | `screenshots/home.png` |
| Play — in-game | `screenshots/play.png` |
| Simulation | `screenshots/simulation.png` |
| Multiplayer Lobby | `screenshots/multiplayer.png` |

---

## Project Structure

```
├── BackEnd/
│   ├── dash_app.py          # Flask/Dash server · REST API · event database
│   └── calculs.py           # GBM simulation engine
├── FrontEnd/
│   └── src/
│       ├── components/      # Navbar, Sidebar, ProgressiveStockGraph, …
│       ├── context/         # SimulationContext — shared game state
│       ├── pages/           # Home, Game, Simulation, Multiplayer
│       └── services/        # API client · multiplayer room service
└── README.md
```

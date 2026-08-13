# Classic Minesweeper + Algorithmic Solver

A browser-playable replica of classic Windows 95 Minesweeper built with **Python**, **Pygame**, and **Pygbag (WebAssembly)**. 

This project features a complete game engine along with an automated solver capable of analyzing board states, making logical deductions, and executing safe moves.

---

## Features

* **Retro Aesthetics:** Custom 3D bevel borders, classic tile graphics, status indicator, and digital LCD mine counters.
* **Algorithmic Solver:**
  * **Greedy Deduction:** Instantly flags single-cell guaranteed mines and opens known safe spaces.
  * **Constraint Satisfaction (CSP) Backtracking:** Solves complex multi-cell boundary scenarios when simple logic isn't enough.
  * **Frontier Highlighting:** Visually highlights active boundary tiles under evaluation by the solver algorithm.
* **Control Panel:**
  * **Step:** Executes a single logical move by the solver.
  * **Auto Solve:** Runs the automated solver continuously with an adjustable step timer.
  * **Reset:** Instantly generates a fresh, playable board.
* **Web Ready:** Compiled using Pygbag to run directly inside any modern web browser without installations.

---

## Tech Stack

* **Language:** Python 3
* **Graphics & Engine:** Pygame
* **Web Build:** Pygbag (WebAssembly / HTML5)
* **Hosting:** GitHub Pages

---

## How to Play

### Play Online (Browser)
Visit the live hosted version: **[YOUR-GITHUB-PAGES-LINK-HERE]**

### Run Locally
1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR-USERNAME/minesweeper-game.git](https://github.com/YOUR-USERNAME/minesweeper-game.git)
   cd minesweeper-game

import sys
import random
import math
from collections import deque
import pygame
import asyncio

ROWS, COLS = 9, 9
NUM_MINES = 10

TILE_SIZE = 34
BEVEL_THICK = 3
PADDING = 12

STEP_DELAY = 600

BOARD_W = COLS * TILE_SIZE
BOARD_H = ROWS * TILE_SIZE

TITLE_BAR_H = 28
HEADER_PANEL_H = 50
VERTICAL_GAP = 12

WIDTH = BOARD_W + PADDING * 2 + BEVEL_THICK * 4
HEIGHT = (PADDING + TITLE_BAR_H + HEADER_PANEL_H + 
          VERTICAL_GAP + BOARD_H + PADDING + BEVEL_THICK * 6)

COLOR_BG = (192, 192, 192)
COLOR_LIGHT = (255, 255, 255)
COLOR_DARK = (128, 128, 128)
COLOR_DARK_SHADOW = (64, 64, 64)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_FRONTIER = (255, 235, 150)

COLOR_STATUS_PLAYING = (0, 100, 0)
COLOR_STATUS_WON = (0, 0, 180)
COLOR_STATUS_LOST = (180, 0, 0)

CLASSIC_NUM_COLORS = {
    1: (0, 0, 255),
    2: (0, 128, 0),
    3: (255, 0, 0),
    4: (0, 0, 128),
    5: (128, 0, 0),
    6: (0, 128, 128),
    7: (0, 0, 0),
    8: (128, 128, 128)
}

class MinesweeperBoard:
    def __init__(self, rows=ROWS, cols=COLS, num_mines=NUM_MINES):
        self.rows = rows
        self.cols = cols
        self.num_mines = num_mines
        self.grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self.mines = set()
        self.revealed = set()
        self.flags = set()
        self.first_click = True
        self.game_over = False
        self.won = False
        self.hit_mine = None

    def get_neighbors(self, r, c):
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append((nr, nc))
        return neighbors

    def generate_board(self, safe_r, safe_c):
        safe_zone = set(self.get_neighbors(safe_r, safe_c))
        safe_zone.add((safe_r, safe_c))

        all_positions = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in safe_zone]
        self.mines = set(random.sample(all_positions, self.num_mines))

        for r, c in self.mines:
            for nr, nc in self.get_neighbors(r, c):
                if (nr, nc) not in self.mines:
                    self.grid[nr][nc] += 1

    def reveal(self, start_r, start_c):
        if (start_r, start_c) in self.flags or (start_r, start_c) in self.revealed:
            return True

        if self.first_click:
            self.generate_board(start_r, start_c)
            self.first_click = False

        if (start_r, start_c) in self.mines:
            self.game_over = True
            self.hit_mine = (start_r, start_c)
            return False

        queue = deque([(start_r, start_c)])
        while queue:
            r, c = queue.popleft()
            if (r, c) in self.revealed or (r, c) in self.flags:
                continue

            self.revealed.add((r, c))

            if self.grid[r][c] == 0:
                for nr, nc in self.get_neighbors(r, c):
                    if (nr, nc) not in self.revealed:
                        queue.append((nr, nc))

        self.check_win()
        return True

    def toggle_flag(self, r, c):
        if (r, c) not in self.revealed:
            if (r, c) in self.flags:
                self.flags.remove((r, c))
            elif len(self.flags) < self.num_mines:
                self.flags.add((r, c))

    def check_win(self):
        if len(self.revealed) == (self.rows * self.cols - self.num_mines):
            self.won = True
            self.game_over = True

class MinesweeperSolver:
    def __init__(self, game: MinesweeperBoard):
        self.game = game
        self.frontier_highlight = set()

    def greedy_step(self):
        actions = []
        for r, c in list(self.game.revealed):
            val = self.game.grid[r][c]
            if val == 0:
                continue

            neighbors = self.game.get_neighbors(r, c)
            hidden = [n for n in neighbors if n not in self.game.revealed and n not in self.game.flags]
            flagged = [n for n in neighbors if n in self.game.flags]

            if len(hidden) > 0 and len(flagged) + len(hidden) == val:
                for cell in hidden:
                    actions.append(('flag', cell[0], cell[1]))

            elif len(hidden) > 0 and len(flagged) == val:
                for cell in hidden:
                    actions.append(('reveal', cell[0], cell[1]))

        return list(set(actions))

    def csp_backtracking_step(self):
        frontier = set()
        active_constraints = []

        for r, c in self.game.revealed:
            neighbors = self.game.get_neighbors(r, c)
            hidden = [n for n in neighbors if n not in self.game.revealed and n not in self.game.flags]
            flagged_count = sum(1 for n in neighbors if n in self.game.flags)
            remaining_mines = self.game.grid[r][c] - flagged_count

            if hidden:
                frontier.update(hidden)
                active_constraints.append((hidden, remaining_mines))

        self.frontier_highlight = frontier
        frontier_list = list(frontier)
        if not frontier_list:
            return []

        valid_assignments = []

        def backtrack(index, current_assignment):
            if index == len(frontier_list):
                for hidden_group, req_mines in active_constraints:
                    actual_mines = sum(1 for cell in hidden_group if current_assignment.get(cell, 0) == 1)
                    if actual_mines != req_mines:
                        return
                valid_assignments.append(current_assignment.copy())
                return

            cell = frontier_list[index]
            for val in [0, 1]:
                current_assignment[cell] = val
                possible = True
                for hidden_group, req_mines in active_constraints:
                    assigned_mines = sum(1 for c in hidden_group if c in current_assignment and current_assignment[c] == 1)
                    unassigned = sum(1 for c in hidden_group if c not in current_assignment)
                    if assigned_mines > req_mines or (assigned_mines + unassigned) < req_mines:
                        possible = False
                        break

                if possible:
                    backtrack(index + 1, current_assignment)
                del current_assignment[cell]

        backtrack(0, {})

        if not valid_assignments:
            return []

        cell_mine_counts = {cell: 0 for cell in frontier_list}
        for assignment in valid_assignments:
            for cell, is_mine in assignment.items():
                if is_mine == 1:
                    cell_mine_counts[cell] += 1

        actions = []
        total_valid = len(valid_assignments)
        for cell, mine_count in cell_mine_counts.items():
            if mine_count == 0:
                actions.append(('reveal', cell[0], cell[1]))
            elif mine_count == total_valid:
                actions.append(('flag', cell[0], cell[1]))

        return actions

    def solve_step(self):
        if self.game.game_over:
            return False

        if self.game.first_click:
            self.game.reveal(self.game.rows // 2, self.game.cols // 2)
            return True

        moves = self.greedy_step()
        if not moves:
            moves = self.csp_backtracking_step()

        if not moves:
            unrevealed = [(r, c) for r in range(self.game.rows) for c in range(self.game.cols) 
                          if (r, c) not in self.game.revealed and (r, c) not in self.game.flags]
            if unrevealed:
                r, c = random.choice(unrevealed)
                moves = [('reveal', r, c)]

        for action, r, c in moves:
            if action == 'flag':
                self.game.toggle_flag(r, c)
            elif action == 'reveal':
                self.game.reveal(r, c)

        return len(moves) > 0

def draw_3d_bevel(screen, rect, raised=True, thick=BEVEL_THICK):
    x, y, w, h = rect
    c_high = COLOR_LIGHT if raised else COLOR_DARK
    c_low = COLOR_DARK if raised else COLOR_LIGHT

    for i in range(thick):
        pygame.draw.line(screen, c_high, (x + i, y + i), (x + w - 1 - i, y + i))
        pygame.draw.line(screen, c_high, (x + i, y + i), (x + i, y + h - 1 - i))
        pygame.draw.line(screen, c_low, (x + i, y + h - 1 - i), (x + w - 1 - i, y + h - 1 - i))
        pygame.draw.line(screen, c_low, (x + w - 1 - i, y + i), (x + w - 1 - i, y + h - 1 - i))

def draw_lcd_display(screen, rect, number, font):
    pygame.draw.rect(screen, COLOR_BLACK, rect)
    draw_3d_bevel(screen, rect, raised=False, thick=2)

    val_str = f"{max(-99, min(999, number)):03d}"
    txt_surf = font.render(val_str, True, COLOR_RED)
    txt_rect = txt_surf.get_rect(center=rect.center)
    screen.blit(txt_surf, txt_rect)

def draw_flag(screen, center):
    cx, cy = center
    pygame.draw.line(screen, COLOR_BLACK, (cx - 3, cy + 8), (cx - 3, cy - 7), 2)
    pygame.draw.polygon(screen, COLOR_RED, [(cx - 3, cy - 7), (cx + 6, cy - 3), (cx - 3, cy + 1)])
    pygame.draw.rect(screen, COLOR_DARK_SHADOW, (cx - 7, cy + 6, 8, 3))

def draw_mine(screen, center):
    cx, cy = center
    r = 6
    pygame.draw.circle(screen, COLOR_BLACK, (cx, cy), r)
    lines = [
        ((cx - 8, cy), (cx + 8, cy)),
        ((cx, cy - 8), (cx, cy + 8)),
        ((cx - 6, cy - 6), (cx + 6, cy + 6)),
        ((cx - 6, cy + 6), (cx + 6, cy - 6))
    ]
    for p1, p2 in lines:
        pygame.draw.line(screen, COLOR_BLACK, p1, p2, 2)
    pygame.draw.rect(screen, COLOR_LIGHT, (cx - 2, cy - 2, 2, 2))

async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Minesweeper")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("Arial", 16, bold=True)
    font_status = pygame.font.SysFont("Arial", 13, bold=True)
    font_btn = pygame.font.SysFont("Arial", 11, bold=True)
    font_lcd = pygame.font.SysFont("Consolas", 22, bold=True)
    font_tile = pygame.font.SysFont("Consolas", 22, bold=True)

    board = MinesweeperBoard()
    solver = MinesweeperSolver(board)
    auto_play = False
    last_step_time = 0

    y_cursor = PADDING

    title_bar_y = y_cursor
    y_cursor += TITLE_BAR_H

    header_panel_rect = pygame.Rect(PADDING, y_cursor, BOARD_W, HEADER_PANEL_H)
    
    btn_y = header_panel_rect.centery - 13
    btn_step = pygame.Rect(header_panel_rect.left + 8, btn_y, 52, 26)
    btn_auto = pygame.Rect(header_panel_rect.left + 66, btn_y, 75, 26)
    btn_reset = pygame.Rect(header_panel_rect.left + 147, btn_y, 52, 26)

    lcd_mines_rect = pygame.Rect(header_panel_rect.right - 62, header_panel_rect.centery - 15, 54, 30)

    y_cursor += HEADER_PANEL_H + VERTICAL_GAP

    board_rect = pygame.Rect(PADDING, y_cursor, BOARD_W, BOARD_H)

    running = True
    while running:
        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_step.collidepoint(event.pos):
                    solver.solve_step()

                elif btn_auto.collidepoint(event.pos):
                    auto_play = not auto_play
                    last_step_time = current_time

                elif btn_reset.collidepoint(event.pos):
                    board = MinesweeperBoard()
                    solver = MinesweeperSolver(board)
                    auto_play = False

                elif not board.game_over and board_rect.collidepoint(event.pos):
                    x, y = event.pos
                    c = (x - board_rect.left) // TILE_SIZE
                    r = (y - board_rect.top) // TILE_SIZE

                    if 0 <= r < ROWS and 0 <= c < COLS:
                        if event.button == 1:
                            board.reveal(r, c)
                        elif event.button == 3:
                            board.toggle_flag(r, c)

        if auto_play and not board.game_over:
            if current_time - last_step_time >= STEP_DELAY:
                solver.solve_step()
                last_step_time = current_time

        screen.fill(COLOR_BG)

        draw_3d_bevel(screen, (0, 0, WIDTH, HEIGHT), raised=True, thick=BEVEL_THICK)

        title_surf = font_title.render("Minesweeper", True, COLOR_BLACK)
        screen.blit(title_surf, (PADDING, title_bar_y))

        status_text = "Playing"
        status_color = COLOR_STATUS_PLAYING
        if board.won:
            status_text = "Solved!"
            status_color = COLOR_STATUS_WON
        elif board.game_over:
            status_text = "Game Over"
            status_color = COLOR_STATUS_LOST

        status_surf = font_status.render(status_text, True, status_color)
        screen.blit(status_surf, (WIDTH - PADDING - status_surf.get_width(), title_bar_y + 2))

        pygame.draw.rect(screen, COLOR_BG, header_panel_rect)
        draw_3d_bevel(screen, header_panel_rect, raised=False, thick=BEVEL_THICK)

        buttons_data = [
            (btn_step, "Step", False),
            (btn_auto, "Pause" if auto_play else "Auto Solve", auto_play),
            (btn_reset, "Reset", False)
        ]
        for btn, label, is_active in buttons_data:
            is_hovered = btn.collidepoint(mouse_pos)
            pygame.draw.rect(screen, COLOR_BG, btn)
            draw_3d_bevel(screen, btn, raised=not (is_active or (is_hovered and mouse_pressed[0])), thick=2)
            lbl_surf = font_btn.render(label, True, COLOR_BLACK)
            screen.blit(lbl_surf, lbl_surf.get_rect(center=btn.center))

        draw_lcd_display(screen, lcd_mines_rect, NUM_MINES - len(board.flags), font_lcd)

        pygame.draw.rect(screen, COLOR_BG, board_rect)
        draw_3d_bevel(screen, board_rect, raised=False, thick=BEVEL_THICK)

        for r in range(ROWS):
            for c in range(COLS):
                tx = board_rect.left + c * TILE_SIZE
                ty = board_rect.top + r * TILE_SIZE
                tile_rect = pygame.Rect(tx, ty, TILE_SIZE, TILE_SIZE)

                if (r, c) in board.revealed:
                    pygame.draw.rect(screen, COLOR_BG, tile_rect)
                    pygame.draw.rect(screen, COLOR_DARK, tile_rect, 1)

                    val = board.grid[r][c]
                    if val > 0:
                        txt_color = CLASSIC_NUM_COLORS.get(val, COLOR_BLACK)
                        txt = font_tile.render(str(val), True, txt_color)
                        screen.blit(txt, txt.get_rect(center=tile_rect.center))

                else:
                    pygame.draw.rect(screen, COLOR_BG, tile_rect)

                    if (r, c) in solver.frontier_highlight and not board.game_over:
                        pygame.draw.rect(screen, COLOR_FRONTIER, tile_rect)

                    draw_3d_bevel(screen, tile_rect, raised=True, thick=2)

                    if (r, c) in board.flags:
                        draw_flag(screen, tile_rect.center)

                    if board.game_over and (r, c) in board.mines:
                        if (r, c) == board.hit_mine:
                            pygame.draw.rect(screen, COLOR_RED, tile_rect)
                        draw_mine(screen, tile_rect.center)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
import pygame
import random
import json
import os

# setup the screen
pygame.init()
CELL = 30
COLS = 20
ROWS = 20
TOP = 60                      # top bar for score
W = COLS * CELL
H = ROWS * CELL + TOP
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Snake v2")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("arial", 64, bold=True)
font = pygame.font.SysFont("arial", 28)
font_small = pygame.font.SysFont("arial", 20)

# colors
BG = (20, 24, 30)
GRID = (26, 31, 38)
GREEN = (80, 200, 120)
HEAD = (140, 255, 170)
RED = (230, 70, 70)
GOLD = (255, 200, 50)
GRAY = (110, 115, 125)
WHITE = (235, 235, 235)

# difficulty settings
# speed = moves per second at the start, step = speed added each level
DIFFS = {
    "Easy":   {"speed": 6,  "step": 0.5, "wrap": True,  "rocks": False},
    "Normal": {"speed": 8,  "step": 0.8, "wrap": False, "rocks": False},
    "Hard":   {"speed": 10, "step": 1.0, "wrap": False, "rocks": True},
}
NAMES = ["Easy", "Normal", "Hard"]
MAX_SPEED = 20
FOODS_PER_LEVEL = 5

# best scores are saved in a small file next to the game
SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.json")


def load_scores():
    try:
        with open(SCORE_FILE) as f:
            return json.load(f)
    except Exception:
        return {"Easy": 0, "Normal": 0, "Hard": 0}


def save_scores():
    try:
        with open(SCORE_FILE, "w") as f:
            json.dump(scores, f)
    except Exception:
        pass


scores = load_scores()


def free_cell(min_dist=0):
    # find an empty cell (not on snake, rocks or food)
    while True:
        c = (random.randrange(COLS), random.randrange(ROWS))
        if c in snake or c in rocks or c == food or c == bonus:
            continue
        # keep away from the head so rocks never appear right in front of you
        if abs(c[0] - snake[0][0]) + abs(c[1] - snake[0][1]) < min_dist:
            continue
        return c


def reset(name):
    # start a new game with the chosen difficulty
    global snake, direction, queue, food, bonus, bonus_timer, rocks
    global score, eaten, level, speed, move_timer, msg_timer, new_best, diff_name
    diff_name = name
    snake = [(5, 10), (4, 10), (3, 10)]
    direction = (1, 0)
    queue = []                 # saved key presses (so fast turns are not lost)
    rocks = []
    food = None
    bonus = None
    bonus_timer = 0
    food = free_cell()
    score = 0
    eaten = 0
    level = 1
    speed = DIFFS[name]["speed"]
    move_timer = 0
    msg_timer = 0
    new_best = False


def game_over():
    global state, new_best
    state = "gameover"
    if score > scores[diff_name]:
        scores[diff_name] = score
        new_best = True
        save_scores()


def step():
    # move the snake one cell
    global direction, food, bonus, bonus_timer, score, eaten, level, speed, msg_timer
    if queue:
        direction = queue.pop(0)

    nx = snake[0][0] + direction[0]
    ny = snake[0][1] + direction[1]

    if DIFFS[diff_name]["wrap"]:
        # easy mode: go through walls
        nx %= COLS
        ny %= ROWS
    elif nx < 0 or nx >= COLS or ny < 0 or ny >= ROWS:
        game_over()
        return

    new_head = (nx, ny)

    # hit yourself or a rock
    if new_head in snake or new_head in rocks:
        game_over()
        return

    snake.insert(0, new_head)

    if new_head == food:
        score += 10
        eaten += 1
        food = free_cell()
        # sometimes a golden bonus appears for a few seconds
        if bonus is None and random.random() < 0.25:
            bonus = free_cell()
            bonus_timer = 6
        # next level every few foods
        if eaten % FOODS_PER_LEVEL == 0:
            level += 1
            speed = min(MAX_SPEED, speed + DIFFS[diff_name]["step"])
            msg_timer = 1.5
            if DIFFS[diff_name]["rocks"]:
                rocks.append(free_cell(5))
                rocks.append(free_cell(5))
    elif new_head == bonus:
        score += 30
        bonus = None
    else:
        snake.pop()


def draw_cell(c, color, shrink=4):
    r = pygame.Rect(c[0] * CELL, TOP + c[1] * CELL, CELL, CELL).inflate(-shrink, -shrink)
    pygame.draw.rect(screen, color, r, border_radius=8)


def draw_text(text, f, color, y, x=None):
    img = f.render(text, True, color)
    if x is None:
        x = W // 2 - img.get_width() // 2
    screen.blit(img, (x, y))


def draw_game():
    screen.fill(BG)

    # grid
    for x in range(COLS):
        for y in range(ROWS):
            if (x + y) % 2 == 0:
                pygame.draw.rect(screen, GRID, (x * CELL, TOP + y * CELL, CELL, CELL))

    # rocks
    for r in rocks:
        draw_cell(r, GRAY, 2)

    # food
    pygame.draw.circle(screen, RED, (food[0] * CELL + CELL // 2, TOP + food[1] * CELL + CELL // 2), CELL // 2 - 4)

    # golden bonus (blinks when it is about to disappear)
    if bonus and (bonus_timer > 2 or int(bonus_timer * 6) % 2 == 0):
        pygame.draw.circle(screen, GOLD, (bonus[0] * CELL + CELL // 2, TOP + bonus[1] * CELL + CELL // 2), CELL // 2 - 2)

    # snake
    for part in snake[1:]:
        draw_cell(part, GREEN)
    draw_cell(snake[0], HEAD)

    # eyes
    cx = snake[0][0] * CELL + CELL // 2
    cy = TOP + snake[0][1] * CELL + CELL // 2
    px, py = -direction[1], direction[0]
    for s in (-1, 1):
        ex = cx + direction[0] * 6 + px * 6 * s
        ey = cy + direction[1] * 6 + py * 6 * s
        pygame.draw.circle(screen, (20, 20, 20), (ex, ey), 3)

    # top bar
    pygame.draw.rect(screen, (12, 14, 18), (0, 0, W, TOP))
    draw_text("Score: " + str(score), font, WHITE, 14, 15)
    draw_text("Level: " + str(level), font, GOLD, 14, 230)
    draw_text("Best: " + str(scores[diff_name]), font_small, GRAY, 8, 470)
    draw_text(diff_name + "  " + str(round(speed, 1)) + " mv/s", font_small, GRAY, 32, 440)

    # level up message
    if msg_timer > 0:
        draw_text("LEVEL UP!", font_big, GOLD, H // 2 - 40)


def overlay():
    # dark layer on top of the game
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((0, 0, 0, 160))
    screen.blit(s, (0, 0))


def draw_menu():
    screen.fill(BG)
    draw_text("SNAKE", font_big, GREEN, 70)
    draw_text("choose difficulty", font_small, GRAY, 150)

    infos = {
        "Easy": "walls wrap around - slow start",
        "Normal": "walls are deadly - medium speed",
        "Hard": "walls + rocks + fast speed",
    }
    for i, n in enumerate(NAMES):
        y = 200 + i * 80
        color = GOLD if n == choice else WHITE
        text = ("> " + n + " <") if n == choice else n
        draw_text(text, font, color, y)
        draw_text(infos[n] + "   (best: " + str(scores[n]) + ")", font_small, GRAY, y + 34)

    draw_text("UP / DOWN to choose   ENTER to play", font_small, WHITE, 480)
    draw_text("H  how to play      ESC  quit", font_small, GRAY, 510)
    draw_text("my first game - version 2", font_small, GRAY, 560)


def draw_help():
    screen.fill(BG)
    draw_text("HOW TO PLAY", font, GOLD, 40)
    lines = [
        ("Arrow keys / WASD", "move the snake"),
        ("P", "pause"),
        ("ESC", "back to menu"),
        ("", ""),
        ("Red food", "+10 points, snake grows"),
        ("Golden food", "+30 points, disappears fast"),
        ("", ""),
        ("Every 5 foods", "next level = faster snake"),
        ("Gray rocks", "Hard mode: 2 new rocks every level"),
        ("", ""),
        ("Easy", "you can pass through walls"),
        ("Normal", "walls are deadly"),
        ("Hard", "walls + rocks + more speed"),
    ]
    y = 100
    for a, b in lines:
        draw_text(a, font_small, GREEN, y, 40)
        draw_text(b, font_small, WHITE, y, 240)
        y += 30
    draw_text("press any key to go back", font_small, GRAY, 540)


# game state: menu, help, play, pause, gameover
state = "menu"
choice = "Normal"
reset(choice)

while True:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

        if event.type != pygame.KEYDOWN:
            continue
        k = event.key

        if state == "menu":
            i = NAMES.index(choice)
            if k in (pygame.K_UP, pygame.K_w):
                choice = NAMES[(i - 1) % 3]
            elif k in (pygame.K_DOWN, pygame.K_s):
                choice = NAMES[(i + 1) % 3]
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                reset(choice)
                state = "play"
            elif k == pygame.K_h:
                state = "help"
            elif k == pygame.K_ESCAPE:
                pygame.quit()
                quit()

        elif state == "help":
            state = "menu"

        elif state == "play":
            keys = {
                pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
                pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
                pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
                pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
            }
            if k in keys and len(queue) < 2:
                new_dir = keys[k]
                last = queue[-1] if queue else direction
                # no same direction and no turning back on yourself
                if new_dir != last and (new_dir[0] + last[0], new_dir[1] + last[1]) != (0, 0):
                    queue.append(new_dir)
            elif k == pygame.K_p:
                state = "pause"
            elif k == pygame.K_ESCAPE:
                state = "menu"

        elif state == "pause":
            if k == pygame.K_p:
                state = "play"
            elif k == pygame.K_ESCAPE:
                state = "menu"

        elif state == "gameover":
            if k in (pygame.K_RETURN, pygame.K_r, pygame.K_SPACE):
                reset(diff_name)
                state = "play"
            elif k == pygame.K_ESCAPE:
                state = "menu"

    # update the game
    if state == "play":
        move_timer += dt
        if msg_timer > 0:
            msg_timer -= dt
        if bonus:
            bonus_timer -= dt
            if bonus_timer <= 0:
                bonus = None
        if move_timer >= 1 / speed:
            move_timer -= 1 / speed
            step()

    # draw everything
    if state == "menu":
        draw_menu()
    elif state == "help":
        draw_help()
    else:
        draw_game()
        if state == "pause":
            overlay()
            draw_text("PAUSED", font_big, WHITE, H // 2 - 60)
            draw_text("P to continue   ESC for menu", font_small, GRAY, H // 2 + 20)
        elif state == "gameover":
            overlay()
            draw_text("GAME OVER", font_big, RED, H // 2 - 100)
            draw_text("Score: " + str(score) + "   Level: " + str(level), font, WHITE, H // 2 - 20)
            if new_best:
                draw_text("New best score!", font, GOLD, H // 2 + 25)
            draw_text("ENTER to play again   ESC for menu", font_small, GRAY, H // 2 + 80)

    pygame.display.flip()
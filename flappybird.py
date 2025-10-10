# Imports
import pygame
import os
import random
from array import array

# Setup
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

# Constants
SCREEN_W, SCREEN_H = 1000, 800
FPS = 60
HS_FILE = "highscore.txt"

# Display
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("FLAPPY STONER")
clock = pygame.time.Clock()

# Fonts
font_big = pygame.font.SysFont("Consolas", 62)
font_med = pygame.font.SysFont("Consolas", 32)
font_small = pygame.font.SysFont("Consolas", 20)
font_binary = pygame.font.SysFont("Consolas", 12)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PINK = (255, 0, 255)
SHIELD_COLOR = (60, 180, 255)
SLOWMO_COLOR = (255, 165, 0)
CLOAK_COLOR = (148, 0, 211)
BIRD_COLOR = (255, 255, 0)
STUNNED_EYE_COLOR = (255, 100, 100)
BEER_COLOR = (255, 191, 0)
FOAM_COLOR = (255, 255, 255)
GLASS_COLOR = (120, 120, 120)
BUBBLE_COLOR = (255, 230, 180)
BUBBLE_OUTLINE_COLOR = BLACK
BUBBLE_OUTLINE_THICKNESS = 1

# Ranks
LEVELS = [
    ("CYBERPUP", 10, GREEN),
    ("SCRIPTER", 25, (0, 200, 200)),
    ("HACKTIVIST", 50, (255, 165, 0)),
    ("ELITE", 100, RED),
    ("MASTER", 200, PINK)
]

# Player
player_x = 150
player_y = SCREEN_H // 2
player_rad = 14
gravity = 0.5
lift = -10
player_vel = 0
player_wing_up = True
wing_frame_counter = 0

# Obstacles
pipe_w = 72
pipe_gap = 220
pipe_speed_base = -3
pipe_speed = pipe_speed_base
pipes = []
POWERUP_DUR = 300
powerups = []

# Game
score = 0
active = False
paused = False
frame_count = 0
glitch_fx = 0
shield_on = False
slowmo_time = 0
shrink_time = 0

# Audio
def make_sound(freq, dur):
    sample_rate = pygame.mixer.get_init()[0]
    sampsize = pygame.mixer.get_init()[2]
    period = int(round(sample_rate / freq)) if freq > 0 else 1
    amp = (2 ** (sampsize - 1)) - 1
    samps = array("h", [amp if (i // period) % 2 == 0 else -amp for i in range(int(sample_rate * dur / 1000))])
    try:
        return pygame.mixer.Sound(buffer=samps)
    except Exception:
        return None

s_flap = make_sound(900, 45)
s_score = make_sound(1400, 80)
s_crash = make_sound(300, 300)
s_power = make_sound(1800, 120)
s_shield_break = make_sound(500, 150)

# Load
def load_hs():
    if not os.path.exists(HS_FILE):
        return 0
    with open(HS_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except:
            return 0

# Save
def save_hs(hs):
    with open(HS_FILE, "w") as f:
        f.write(str(hs))

# Text
def draw_text(text, font, color, surf, x, y, center=True):
    obj = font.render(text, True, color)
    rect = obj.get_rect(center=(x, y)) if center else obj.get_rect(topleft=(x, y))
    if not center and x > SCREEN_W / 2:
        rect.topright = (x, y)
    surf.blit(obj, rect)

# Background
def create_static_binary_background():
    bg_surf = pygame.Surface((SCREEN_W, SCREEN_H))
    bg_surf.fill(BLACK)
    char_width, char_height = 10, 15
    for x in range(0, SCREEN_W, char_width):
        for y in range(0, SCREEN_H, char_height):
            if random.randint(1, 10) > 4:
                char = random.choice(['0', '1'])
                if random.randint(1, 20) == 1:
                    color = (150, 255, 150)
                else:
                    brightness = random.randint(50, 110)
                    color = (0, brightness, 0)
                char_render = font_binary.render(char, True, color)
                bg_surf.blit(char_render, (x, y))
    return bg_surf

# Rank
def get_level_info(s):
    current_rank = ("NOVICE", 0, WHITE)
    next_rank = LEVELS[0]
    prev_threshold = 0
    for i, (name, threshold, color) in enumerate(LEVELS):
        if s >= threshold:
            current_rank = (name, threshold, color)
            prev_threshold = threshold
            if i + 1 < len(LEVELS):
                next_rank = LEVELS[i + 1]
            else:
                next_rank = ("LEGEND", threshold + 50, BLUE)
        else:
            next_rank = (name, threshold, color)
            break
    return current_rank, next_rank, prev_threshold

# PlayerArt
def draw_player(x, y):
    global player_wing_up, wing_frame_counter
    if not paused and active:
        wing_frame_counter += 1
        if wing_frame_counter >= 5:
            player_wing_up = not player_wing_up
            wing_frame_counter = 0

    body_pts = [
        (x - player_rad, y),
        (x + player_rad * 1.5, y - player_rad),
        (x + player_rad * 1.5, y + player_rad)
    ]
    pygame.draw.polygon(screen, BIRD_COLOR, body_pts)
    pygame.draw.polygon(screen, WHITE, body_pts, 2)
    
    wing_y_offset = -8 if player_wing_up else 8
    wing_pts = [
        (x + 2, y + wing_y_offset),
        (x - player_rad, y + wing_y_offset + 5),
        (x + 2, y + wing_y_offset + 10)
    ]
    pygame.draw.polygon(screen, (255, 100, 0), wing_pts)

    beak_pts = [
        (x + player_rad * 1.3, y),
        (x + player_rad * 2.0, y - 5),
        (x + player_rad * 2.0, y + 5)
    ]
    pygame.draw.polygon(screen, (255, 100, 0), beak_pts)
    
    eye_center_x = int(x + player_rad * 0.8)
    eye_center_y = int(y - player_rad * 0.4)
    eye_radius = int(player_rad * 0.4)
    pupil_radius = int(player_rad * 0.2)
    pygame.draw.circle(screen, STUNNED_EYE_COLOR, (eye_center_x, eye_center_y), eye_radius)
    pygame.draw.circle(screen, BLACK, (eye_center_x + int(pupil_radius * 0.5), eye_center_y), pupil_radius)

    joint_length = 25
    joint_height = 4
    joint_x_offset = player_rad * 1.9
    joint_y_offset = -1
    joint_rect = pygame.Rect(x + joint_x_offset, y + joint_y_offset, joint_length, joint_height)
    pygame.draw.rect(screen, (150, 150, 150), joint_rect)
    tip_width = 5
    tip_rect = pygame.Rect(joint_rect.right - tip_width, joint_rect.y, tip_width, joint_height)
    pygame.draw.rect(screen, RED, tip_rect)

    if shield_on:
        shield_surf = pygame.Surface((player_rad * 4, player_rad * 4), pygame.SRCALPHA)
        pygame.draw.rect(shield_surf, (*SHIELD_COLOR, 80), (10, 10, player_rad*3, player_rad*2.5), 3)
        screen.blit(shield_surf, (int(x - player_rad * 2), int(y - player_rad * 2)))

# ObstacleArt
def draw_pipe(pipe):
    GLASS_THICKNESS = 4
    BEER_PADDING = 3
    FOAM_HEIGHT = 12
    RIM_HEIGHT = 8
    RIM_COLOR = BLACK

    top_rect = pipe['top_rect']
    beer_fill_top = top_rect.inflate(-BEER_PADDING * 2, 0)
    pygame.draw.rect(screen, BEER_COLOR, beer_fill_top)
    pygame.draw.rect(screen, GLASS_COLOR, top_rect, GLASS_THICKNESS)
    rim_rect_top = pygame.Rect(top_rect.x, top_rect.bottom - RIM_HEIGHT//2, top_rect.width, RIM_HEIGHT)
    pygame.draw.ellipse(screen, RIM_COLOR, rim_rect_top)
    for _ in range(15):
        rand_x = random.randint(beer_fill_top.left + 5, beer_fill_top.right - 5)
        rand_y = random.randint(beer_fill_top.top + 5, beer_fill_top.bottom - 5)
        pygame.draw.circle(screen, BEER_COLOR, (rand_x, rand_y), 2)
        pygame.draw.circle(screen, BUBBLE_OUTLINE_COLOR, (rand_x, rand_y), 2, BUBBLE_OUTLINE_THICKNESS)

    bottom_rect = pipe['bottom_rect']
    beer_fill_bot = bottom_rect.inflate(-BEER_PADDING * 2, 0)
    beer_fill_bot.y += FOAM_HEIGHT
    beer_fill_bot.height -= FOAM_HEIGHT
    pygame.draw.rect(screen, BEER_COLOR, beer_fill_bot)
    pygame.draw.rect(screen, GLASS_COLOR, bottom_rect, GLASS_THICKNESS)
    rim_rect_bot = pygame.Rect(bottom_rect.x, bottom_rect.y - RIM_HEIGHT//2, bottom_rect.width, RIM_HEIGHT)
    pygame.draw.ellipse(screen, RIM_COLOR, rim_rect_bot)
    for _ in range(15):
        rand_x = random.randint(beer_fill_bot.left + 5, beer_fill_bot.right - 5)
        rand_y = random.randint(beer_fill_bot.top + 5, beer_fill_bot.bottom - 5)
        pygame.draw.circle(screen, BEER_COLOR, (rand_x, rand_y), 2)
        pygame.draw.circle(screen, BUBBLE_OUTLINE_COLOR, (rand_x, rand_y), 2, BUBBLE_OUTLINE_THICKNESS)

    foam_rect = pygame.Rect(bottom_rect.x, bottom_rect.y, bottom_rect.width, FOAM_HEIGHT)
    foam_rect_inflated = foam_rect.inflate(8, 0)
    foam_rect_inflated.centerx = bottom_rect.centerx
    pygame.draw.rect(screen, FOAM_COLOR, foam_rect_inflated)
    pygame.draw.line(screen, WHITE,
                     (foam_rect_inflated.left + 2, foam_rect_inflated.top + 2),
                     (foam_rect_inflated.right - 2, foam_rect_inflated.top + 2),
                     3)
# PowerupArt
def draw_powerups():
    for p in powerups:
        color = SHIELD_COLOR if p['type'] == 'shield' else SLOWMO_COLOR if p['type'] == 'slowmo' else CLOAK_COLOR
        # Add 'screen' as the first argument here
        pygame.draw.rect(screen, color, p['rect'])
        pygame.draw.rect(screen, WHITE, p['rect'], 2)

# HUD
def draw_hud(s, hs):
    hud = pygame.Surface((SCREEN_W, 60))
    hud.set_alpha(180)
    hud.fill(BLACK)
    screen.blit(hud, (0, 0))
    draw_text(f"ACCESS LVL {s}", font_med, GREEN, screen, 12, 10, False)
    draw_text(f"HIGH {hs}", font_small, WHITE, screen, SCREEN_W - 12, 12, False)
    
    _, next_rank, prev_threshold = get_level_info(s)
    next_rank_name, next_rank_score, _ = next_rank
    denominator = next_rank_score - prev_threshold
    pct = (s - prev_threshold) / denominator if denominator > 0 else 1.0
    pct = min(pct, 1.0)
    bar_w = SCREEN_W - 40
    pygame.draw.rect(screen, (40,40,40), (20, 40, bar_w, 12))
    pygame.draw.rect(screen, BLUE, (20, 40, int(bar_w * pct), 12))

# Create
def create_pipe():
    h = random.randint(120, SCREEN_H - pipe_gap - 120)
    top = pygame.Rect(SCREEN_W, 0, pipe_w, h)
    bot = pygame.Rect(SCREEN_W, h + pipe_gap, pipe_w, SCREEN_H - h - pipe_gap)
    if random.randint(1, 5) == 1:
        powerups.append({'rect': pygame.Rect(SCREEN_W + pipe_w // 2, h + pipe_gap // 2 - 12, 22, 22),
                          'type': random.choice(['shield', 'slowmo', 'shrink'])})
    moving = random.choice([True, False, False])
    return {'top_rect': top, 'bottom_rect': bot, 'passed': False, 'moving': moving, 'move_dir': random.choice([-1, 1]), 'move_speed': random.uniform(0.4, 1.6)}

# Physics
def update_physics():
    for p in pipes + powerups:
        if 'rect' in p:
            p['rect'].x += pipe_speed
        else:
            p['top_rect'].x += pipe_speed
            p['bottom_rect'].x += pipe_speed
    for p in pipes:
        if p['moving']:
            p['top_rect'].y += p['move_speed'] * p['move_dir']
            p['bottom_rect'].y += p['move_speed'] * p['move_dir']
            if p['top_rect'].bottom < 10 or p['bottom_rect'].top > SCREEN_H - 10:
                p['move_dir'] *= -1

# Collide
def check_collisions():
    global shield_on, slowmo_time, shrink_time, player_y
    player_body_width = player_rad * 3
    player_body_height = player_rad * 2
    pr = pygame.Rect(player_x - player_rad, player_y - player_rad, player_body_width, player_body_height)
    for p in powerups[:]:
        if pr.colliderect(p['rect']):
            if s_power: s_power.play()
            if p['type'] == 'shield': shield_on = True
            elif p['type'] == 'slowmo': slowmo_time = POWERUP_DUR
            elif p['type'] == 'shrink': shrink_time = POWERUP_DUR
            powerups.remove(p)
    for pipe in pipes:
        if pr.colliderect(pipe['top_rect']) or pr.colliderect(pipe['bottom_rect']):
            if shield_on:
                shield_on = False
                if s_shield_break: s_shield_break.play()
                return False
            return True
    if not 0 <= player_y <= SCREEN_H:
        if shield_on:
            shield_on = False
            player_y = max(0, min(player_y, SCREEN_H))
            if s_shield_break: s_shield_break.play()
            return False
        return True
    return False

# Powerups
def handle_powerups():
    global pipe_speed, gravity, slowmo_time, shrink_time, player_rad
    if slowmo_time > 0:
        slowmo_time -= 1
        pipe_speed, gravity = (pipe_speed_base - (score / 10)) * 0.45, 0.25
    else:
        pipe_speed, gravity = pipe_speed_base - (score / 10) * 0.02, 0.5
    if shrink_time > 0:
        shrink_time -= 1
        player_rad = 14 * 0.6
    else:
        player_rad = 14

# Reset
def reset():
    global player_y, player_vel, pipes, score, active, frame_count, pipe_speed
    global powerups, shield_on, slowmo_time, shrink_time, player_rad, paused, glitch_fx
    global player_wing_up, wing_frame_counter
    player_y, player_vel, score, frame_count = SCREEN_H // 2, 0, 0, 0
    pipes, powerups = [], []
    pipe_speed = pipe_speed_base
    shield_on, slowmo_time, shrink_time = False, 0, 0
    player_rad = 14
    active, paused, glitch_fx = True, False, 0
    player_wing_up, wing_frame_counter = True, 0

# Main
def main():
    high_score = load_hs()
    static_background = create_static_binary_background()
    running = True

    global score, active, paused, glitch_fx, pipes, powerups
    global player_vel, player_y, frame_count
    
    score = 0
    active = False
    paused = False
    glitch_fx = 0

    while running:
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    if active:
                        player_vel = lift
                        if s_flap: s_flap.play()
                    else:
                        reset()
                if event.key == pygame.K_p and active:
                    paused = not paused

        # Render
        screen.blit(static_background, (0, 0))

        if active:
            # Logic
            if not paused:
                player_vel += gravity
                player_y += player_vel
                handle_powerups()
                if frame_count % (120 + max(-80, -score * 2)) == 0:
                    pipes.append(create_pipe())
                    frame_count = 0
                frame_count += 1
                update_physics()

                for p in pipes:
                    if not p['passed'] and p['top_rect'].centerx < player_x:
                        p['passed'] = True
                        score += 1
                        if s_score: s_score.play()

                if check_collisions():
                    if s_crash: s_crash.play()
                    active = False
                    glitch_fx = 22
                    if score > high_score:
                        high_score = score
                        save_hs(high_score)
            # Draw
            for pipe in pipes:
                draw_pipe(pipe)
            draw_powerups()
            draw_player(player_x, player_y)
            draw_hud(score, high_score)
            draw_text(str(score), font_big, GREEN, screen, SCREEN_W // 2, 120)
            if paused:
                draw_text("PAUSED", font_big, WHITE, screen, SCREEN_W // 2, SCREEN_H // 2)
        else:
            # Menu
            draw_text("FLAPPY STONER", font_big, PINK, screen, SCREEN_W // 2, SCREEN_H // 6)
            draw_text("Press Space to ENJOY HIGH", font_med, WHITE, screen, SCREEN_W // 2, SCREEN_H // 2)
            draw_text("P to Pause HIGH. ESC to BLACKOUT", font_small, WHITE, screen, SCREEN_W // 2, SCREEN_H // 2 + 40)
            draw_text(f"High: {high_score}", font_med, GREEN, screen, SCREEN_W // 2, SCREEN_H * 2 / 3 + 60)
            if score > 0:
                draw_text(f"Last Run: {score} LVL", font_small, WHITE, screen, SCREEN_W // 2, SCREEN_H * 2 / 3 - 10)
                final_rank, _, _ = get_level_info(score)
                rank_name, _, rank_color = final_rank
                if rank_name != "NOVICE":
                    draw_text(f"RANK: {rank_name}", font_med, rank_color, screen, SCREEN_W // 2, SCREEN_H * 2 / 3 + 20)

        # Effects
        if glitch_fx > 0:
            g_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            g_surf.fill((255, 20, 20, 40 + glitch_fx * 6))
            for _ in range(12):
                pygame.draw.rect(g_surf, (255,255,255,40), (random.randint(0,SCREEN_W), random.randint(0,SCREEN_H), random.randint(10,80), random.randint(2,12)))
            screen.blit(g_surf, (0,0))
            glitch_fx -= 1

        # Cleanup
        pipes = [p for p in pipes if p['top_rect'].right > -50]
        powerups = [p for p in powerups if p['rect'].right > -30]

        # Update
        pygame.display.update()
        clock.tick(FPS)

    # Quit
    pygame.quit()

# Start
if __name__ == "__main__":
    main()
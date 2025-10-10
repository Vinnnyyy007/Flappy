# Flappy Pwn by [Your Name]
# SPACE: flap/start, P: pause, ESC: quit

import pygame, random, sys, os
from array import array

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Config
SCREEN_W, SCREEN_H = 1000, 800
FPS = 60
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Flappy Pwn")
clock = pygame.time.Clock()

# Fonts
font_big = pygame.font.Font(None, 64)
font_med = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 22)
font_binary = pygame.font.Font(None, 18)

# Colors
GREEN = (0, 255, 140)
BLUE = (30, 144, 255)
PINK = (255, 50, 200)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 40, 40)
SHIELD_COLOR = (60, 180, 255)
SLOWMO_COLOR = (255, 165, 0)
CLOAK_COLOR = (148, 0, 211)
BIRD_COLOR = (255, 255, 0) # Bright Yellow for the bird

# Ranks & Levels
LEVELS = [
    ("USER TOKEN", 10, CLOAK_COLOR),
    ("PRIVILEGE ESC", 25, GREEN),
    ("BRONZE EXPLOIT", 60, (205, 127, 50)),
    ("SILVER ROOTKIT", 100, (192, 192, 192)),
    ("GOLDEN ZERODAY", 150, (255, 215, 0)),
    ("PLATINUM BREACH", 200, (229, 228, 226)),
    ("MASTER PWNER", 250, PINK)
]

# Player
player_x, player_y = 75, SCREEN_H // 2
player_rad = 14
gravity = 0.5
lift = -10
player_vel = 0
player_wing_up = True # NEW: Flapping state
wing_frame_counter = 0 # NEW: Flapping timer

# Firewalls
pipe_w = 72
pipe_gap = 180
pipe_speed_base = -3
pipe_speed = pipe_speed_base
pipes = []
pipe_rate = 110
frame_count = 0

# Exploits
powerups = []
shield_on = False
slowmo_time = 0
shrink_time = 0
POWERUP_DUR = 300

# Score
score = 0
high_score = 0
HS_FILE = "highscore_pwn.txt"

# State
active = False
paused = False
glitch_fx = 0

# Sounds
def make_sound(freq, dur):
    sample_rate, sampsize = pygame.mixer.get_init()[0], abs(pygame.mixer.get_init()[1])
    period = int(round(sample_rate / freq)) if freq > 0 else 1
    amp = (2 ** (sampsize - 1)) - 1
    samps = array("h", [amp if (i // period) % 2 == 0 else -amp for i in range(int(sample_rate * dur / 1000))])
    try: return pygame.mixer.Sound(buffer=samps)
    except: return None

s_flap = make_sound(900, 45)
s_score = make_sound(1400, 80)
s_crash = make_sound(360, 220)
s_power = make_sound(1500, 120)
s_shield_break = make_sound(650, 140)

# Files
def load_hs():
    if not os.path.exists(HS_FILE): return 0
    with open(HS_FILE, "r") as f:
        try: return int(f.read().strip())
        except: return 0

def save_hs(hs):
    with open(HS_FILE, "w") as f: f.write(str(hs))

# Drawing
def draw_text(text, font, color, surf, x, y, center=True):
    obj = font.render(text, True, color)
    rect = obj.get_rect(center=(x,y)) if center else obj.get_rect(topleft=(x,y))
    if not center and x > SCREEN_W / 2: rect.topright = (x,y)
    surf.blit(obj, rect)

def create_static_binary_background():
    bg_surf = pygame.Surface((SCREEN_W, SCREEN_H))
    bg_surf.fill(BLACK)
    char_width, char_height = 10, 15
    for x in range(0, SCREEN_W, char_width):
        for y in range(0, SCREEN_H, char_height):
            # Reduce density to create gaps in the columns
            if random.randint(1, 10) > 4: # 60% chance to draw a character
                char = random.choice(['0', '1'])
                # Most characters are dim, with a small chance for a bright one
                if random.randint(1, 20) == 1:
                    color = (150, 255, 150) # Bright highlight
                else:
                    brightness = random.randint(50, 110) # Dimmer base
                    color = (0, brightness, 0)
                
                char_render = font_binary.render(char, True, color)
                bg_surf.blit(char_render, (x, y))
    return bg_surf

def get_level_info(s):
    current_rank = ("NOVICE", 0, WHITE)
    next_rank = LEVELS[0]
    prev_threshold = 0

    for i, (name, threshold, color) in enumerate(LEVELS):
        if s >= threshold:
            current_rank = (name, threshold, color)
            prev_threshold = threshold
            if i + 1 < len(LEVELS):
                next_rank = LEVELS[i+1]
            else:
                next_rank = ("LEGEND", threshold + 50, BLUE)
        else:
            next_rank = (name, threshold, color)
            break
    return current_rank, next_rank, prev_threshold

# MODIFIED: Draw Player function to draw a bird-like triangle with wings
def draw_player(x, y):
    global player_wing_up, wing_frame_counter
    
    # Rotate wing state every few frames for a flapping animation
    if not paused and active:
        wing_frame_counter += 1
        if wing_frame_counter >= 5: # Flap every 5 frames
            player_wing_up = not player_wing_up
            wing_frame_counter = 0

    # 1. Main Bird Body (Triangle/Wedge shape)
    body_pts = [
        (x - player_rad, y),              # Left tip
        (x + player_rad * 1.5, y - player_rad), # Right top corner
        (x + player_rad * 1.5, y + player_rad)  # Right bottom corner
    ]
    pygame.draw.polygon(screen, BIRD_COLOR, body_pts)
    # Outline
    pygame.draw.polygon(screen, WHITE, body_pts, 2)
    
    # 2. Wing (Smaller triangle that flaps)
    wing_y_offset = -8 if player_wing_up else 8
    wing_pts = [
        (x + 2, y + wing_y_offset),      # Pivot near body center
        (x - player_rad, y + wing_y_offset + 5),  # Trailing edge top
        (x + 2, y + wing_y_offset + 10)  # Trailing edge bottom
    ]
    pygame.draw.polygon(screen, (255, 100, 0), wing_pts) # Orange/Beak color for wing

    # 3. Beak (Small triangle on the front)
    beak_pts = [
        (x + player_rad * 1.5, y), 
        (x + player_rad * 2.2, y - 5), 
        (x + player_rad * 2.2, y + 5)
    ]
    pygame.draw.polygon(screen, (255, 100, 0), beak_pts)
    
    # 4. Shield Effect (if on)
    if shield_on:
        shield_surf = pygame.Surface((player_rad * 4, player_rad * 4), pygame.SRCALPHA)
        # Adjusted shield size for the longer bird shape
        pygame.draw.rect(shield_surf, (*SHIELD_COLOR, 80), (10, 10, player_rad*3, player_rad*2.5), 3) 
        screen.blit(shield_surf, (int(x - player_rad * 2), int(y - player_rad * 2)))

def draw_pipe(pipe):
    for rect in [pipe['top_rect'], pipe['bottom_rect']]:
        pygame.draw.rect(screen, RED, rect)
        pygame.draw.rect(screen, (180, 30, 30), rect, 4)
        for i in range(1,4):
            y_off = int(rect.y + (rect.height / 4) * i)
            pygame.draw.line(screen, (255, 100, 100), (rect.x + 6, y_off - 6), (rect.x + pipe_w - 6, y_off + 6), 1)

def draw_powerups():
    for p in powerups:
        r = p['rect']
        color = SHIELD_COLOR if p['type'] == 'shield' else SLOWMO_COLOR if p['type'] == 'slowmo' else CLOAK_COLOR
        pygame.draw.ellipse(screen, color, r)
        pygame.draw.ellipse(screen, WHITE, r, 1)

def draw_hud(s, hs):
    hud = pygame.Surface((SCREEN_W, 70), pygame.SRCALPHA)
    hud.fill((10, 10, 10, 120))
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
    draw_text(f"NEXT RANK: {next_rank_name}", font_small, WHITE, screen, SCREEN_W // 2, 65)

# Game Logic
def create_pipe():
    h = random.randint(120, SCREEN_H - 120 - pipe_gap)
    top = pygame.Rect(SCREEN_W, 0, pipe_w, h)
    bot = pygame.Rect(SCREEN_W, h + pipe_gap, pipe_w, SCREEN_H - h - pipe_gap)
    if random.randint(1, 5) == 1:
        powerups.append({'rect': pygame.Rect(SCREEN_W + pipe_w // 2, h + pipe_gap // 2 - 12, 22, 22), 'type': random.choice(['shield', 'slowmo', 'shrink'])})
    moving = random.choice([True, False, False])
    return {'top_rect': top, 'bottom_rect': bot, 'passed': False, 'moving': moving, 'move_dir': random.choice([-1, 1]), 'move_speed': random.uniform(0.4, 1.6)}

def update_physics():
    for p in pipes + powerups:
        if 'rect' in p: p['rect'].x += pipe_speed
        else:
            p['top_rect'].x += pipe_speed
            p['bottom_rect'].x += pipe_speed

    for p in pipes:
        if p['moving']:
            p['top_rect'].y += p['move_speed'] * p['move_dir']
            p['bottom_rect'].y += p['move_speed'] * p['move_dir']
            if p['top_rect'].bottom < 80 or p['bottom_rect'].top > SCREEN_H - 80:
                p['move_dir'] *= -1

def check_collisions():
    global shield_on, slowmo_time, shrink_time, player_y
    # MODIFIED: Collision box matches the bird's bounding box
    pr = pygame.Rect(player_x - player_rad, player_y - player_rad, player_rad * 3, player_rad * 2)

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
                return False # Saved by shield
            return True # Death

    if not 0 <= player_y <= SCREEN_H:
        if shield_on:
            shield_on = False
            if s_shield_break: s_shield_break.play()
            player_y = max(player_rad, min(player_y, SCREEN_H - player_rad))
            return False
        return True
    return False

def handle_powerups():
    global slowmo_time, shrink_time, player_rad, gravity, pipe_speed
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

def reset():
    global player_y, player_vel, pipes, score, active, frame_count, pipe_speed
    global powerups, shield_on, slowmo_time, shrink_time, player_rad, paused, glitch_fx
    global player_wing_up, wing_frame_counter # Reset animation state
    player_y, player_vel, score, frame_count = SCREEN_H // 2, 0, 0, 0
    pipes, powerups = [], []
    pipe_speed = pipe_speed_base
    shield_on, slowmo_time, shrink_time = False, 0, 0
    player_rad = 14
    active, paused, glitch_fx = True, False, 0
    player_wing_up, wing_frame_counter = True, 0 # Initialize animation

# Game Loop
high_score = load_hs()
static_background = create_static_binary_background()
running = True
while running:
    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if event.key == pygame.K_SPACE:
                if active and not paused:
                    player_vel = lift
                    if s_flap: s_flap.play()
                elif not active:
                    reset()
            if event.key == pygame.K_p and active:
                paused = not paused

    # Background
    screen.blit(static_background, (0, 0))

    if active:
        if not paused:
            # Physics
            player_vel += gravity
            player_y += player_vel
            handle_powerups()
            if frame_count > pipe_rate:
                pipes.append(create_pipe())
                frame_count = 0
            frame_count += 1
            update_physics()

            # Score
            for p in pipes:
                if not p['passed'] and p['top_rect'].centerx < player_x:
                    p['passed'] = True
                    score += 1
                    if s_score: s_score.play()

            # Collide
            if check_collisions():
                if s_crash: s_crash.play()
                active = False
                glitch_fx = 22
                if score > high_score:
                    high_score = score
                    save_hs(high_score)

        # Draw
        for pipe in pipes: draw_pipe(pipe)
        draw_powerups()
        draw_player(player_x, player_y) # Draw player after pipes/powerups so the bird is on top
        draw_hud(score, high_score)
        draw_text(str(score), font_big, GREEN, screen, SCREEN_W // 2, 120)
        if paused: draw_text("PAUSED", font_big, WHITE, screen, SCREEN_W // 2, SCREEN_H // 2)

    else: 
        draw_text("FLAPPY PWN", font_big, PINK, screen, SCREEN_W // 2, SCREEN_H // 6)
        draw_text("Press SPACE to Inject Packet", font_med, WHITE, screen, SCREEN_W // 2, SCREEN_H // 2)
        draw_text("P to Pause. ESC to Quit.", font_small, WHITE, screen, SCREEN_W // 2, SCREEN_H // 2 + 40)
        draw_text(f"High: {high_score}", font_med, GREEN, screen, SCREEN_W // 2, SCREEN_H * 2 / 3 + 60)
        if score > 0:
            draw_text(f"Last Run: {score} LVL", font_small, WHITE, screen, SCREEN_W // 2, SCREEN_H * 2 / 3 - 10)
            final_rank, _, _ = get_level_info(score)
            rank_name, _, rank_color = final_rank
            if rank_name != "NOVICE":
                draw_text(f"RANK: {rank_name}", font_med, rank_color, screen, SCREEN_W // 2, SCREEN_H * 2 / 3 + 20)

    # FX
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

    pygame.display.update()
    clock.tick(FPS)

save_hs(high_score)
pygame.quit()
sys.exit()
import pygame
import random
import sys
import os
import math
from array import array

# Initialization
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Screen Setup
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Pygame")

# Clock
clock = pygame.time.Clock()
FPS = 60

# Fonts
font = pygame.font.Font(None, 60)
small_font = pygame.font.Font(None, 35)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
NIGHT_BLUE = (25, 25, 112)
GREEN = (50, 205, 50)
DARK_GREEN = (0, 100, 0)
YELLOW = (255, 255, 0)
SHIELD_COLOR = (30, 144, 255, 100)
SLOWMO_COLOR = (255, 165, 0)
SHRINK_COLOR = (148, 0, 211)


# Medal Colors
BRONZE = (205, 127, 50)
SILVER = (192, 192, 192)
GOLD = (255, 215, 0)


# Bird Settings
bird_x = 75
bird_y = SCREEN_HEIGHT // 2
original_bird_radius = 15
bird_radius = original_bird_radius
gravity = 0.5
lift = -10
bird_velocity = 0


# Pipe Settings
pipe_width = 70
pipe_gap = 200
base_pipe_velocity = -3
pipe_velocity = base_pipe_velocity
pipes = []
pipe_spawn_rate = 120
frame_count = 0


# Power-up Settings
powerups = []
shield_active = False
slowmo_timer = 0
shrink_timer = 0
POWERUP_DURATION = 300 # 5 seconds at 60 FPS


# Score Settings
score = 0
high_score = 0
HIGH_SCORE_FILE = "highscore.txt"


# Game State
game_active = False
game_paused = False # For the new pause feature


# Sound Generation
def generate_sound(frequency, duration_ms):
    sample_rate = pygame.mixer.get_init()[0]
    period = int(round(sample_rate / frequency))
    amplitude = 2 ** (abs(pygame.mixer.get_init()[1]) - 1) - 1
    samples = array("h", [0] * (sample_rate * duration_ms // 1000))
    for i in range(len(samples)):
        samples[i] = amplitude if (i // period) % 2 == 0 else -amplitude
    return pygame.mixer.Sound(buffer=samples)


# Game Sounds
flap_sound = generate_sound(800, 50)
score_sound = generate_sound(1200, 100)
crash_sound = generate_sound(400, 200)
powerup_sound = generate_sound(1500, 150)
shield_break_sound = generate_sound(600, 150)


# High Score File Handling
def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        with open(HIGH_SCORE_FILE, "r") as file:
            try: return int(file.read())
            except ValueError: return 0
    return 0

def save_high_score(new_high_score):
    with open(HIGH_SCORE_FILE, "w") as file:
        file.write(str(new_high_score))


# Background Color
def get_background_color(current_score):
    transition_progress = min(current_score / 20.0, 1.0)
    r = int(SKY_BLUE[0] + (NIGHT_BLUE[0] - SKY_BLUE[0]) * transition_progress)
    g = int(SKY_BLUE[1] + (NIGHT_BLUE[1] - SKY_BLUE[1]) * transition_progress)
    b = int(SKY_BLUE[2] + (NIGHT_BLUE[2] - SKY_BLUE[2]) * transition_progress)
    return (r, g, b)


# Drawing Functions
def draw_bird(x, y):
    pygame.draw.circle(screen, YELLOW, (int(x), int(y)), bird_radius)
    if shield_active:
        shield_surface = pygame.Surface((bird_radius * 2, bird_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(shield_surface, SHIELD_COLOR, (bird_radius, bird_radius), bird_radius)
        screen.blit(shield_surface, (int(x - bird_radius), int(y - bird_radius)))

def draw_pipe(pipe):
    pygame.draw.rect(screen, GREEN, pipe['top_rect'])
    pygame.draw.rect(screen, DARK_GREEN, pipe['top_rect'], 5)
    pygame.draw.rect(screen, GREEN, pipe['bottom_rect'])
    pygame.draw.rect(screen, DARK_GREEN, pipe['bottom_rect'], 5)

def draw_powerups():
    for powerup in powerups:
        color = BLACK
        if powerup['type'] == 'shield': color = SHIELD_COLOR
        elif powerup['type'] == 'slowmo': color = SLOWMO_COLOR
        elif powerup['type'] == 'shrink': color = SHRINK_COLOR
        pygame.draw.ellipse(screen, color, powerup['rect'])

def draw_text(text, font, color, surface, x, y, center=True):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center: text_rect.center = (x, y)
    else: text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

def draw_medals(current_score):
    medal = None
    if current_score >= 50:
        medal = "Gold"
        medal_color = GOLD
    elif current_score >= 25:
        medal = "Silver"
        medal_color = SILVER
    elif current_score >= 10:
        medal = "Bronze"
        medal_color = BRONZE
    
    if medal:
        pygame.draw.circle(screen, medal_color, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT * 2 / 3 + 15), 20)
        draw_text(f"{medal} Medal!", small_font, WHITE, screen, SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT * 2 / 3 + 15)

# Object Creation
def create_pipe():
    random_height = random.randint(150, SCREEN_HEIGHT - 150 - pipe_gap)
    top_rect = pygame.Rect(SCREEN_WIDTH, 0, pipe_width, random_height)
    bottom_rect = pygame.Rect(SCREEN_WIDTH, random_height + pipe_gap, pipe_width, SCREEN_HEIGHT - (random_height + pipe_gap))
    
    if random.randint(1, 5) == 1:
        create_powerup(random_height + pipe_gap // 2)

    is_moving = random.choice([True, False, False])
    move_dir = random.choice([-1, 1]) if is_moving else 0
    move_speed = random.uniform(0.5, 1.5) if is_moving else 0

    return {'top_rect': top_rect, 'bottom_rect': bottom_rect, 'passed': False,
            'moving': is_moving, 'move_dir': move_dir, 'move_speed': move_speed}

def create_powerup(y_pos):
    powerup_type = random.choice(['shield', 'slowmo', 'shrink'])
    rect = pygame.Rect(SCREEN_WIDTH + pipe_width // 2, y_pos - 15, 20, 20)
    powerups.append({'rect': rect, 'type': powerup_type})

# Game Logic
def move_objects():
    for pipe in pipes:
        pipe['top_rect'].x += pipe_velocity
        pipe['bottom_rect'].x += pipe_velocity
    for powerup in powerups:
        powerup['rect'].x += pipe_velocity

def update_moving_pipes(pipe_list):
    for pipe in pipe_list:
        if pipe['moving']:
            pipe['top_rect'].y += pipe['move_speed'] * pipe['move_dir']
            pipe['bottom_rect'].y += pipe['move_speed'] * pipe['move_dir']
            if pipe['top_rect'].height < 75 or pipe['bottom_rect'].top > SCREEN_HEIGHT - 75:
                pipe['move_dir'] *= -1

def check_collisions():
    global shield_active, slowmo_timer, shrink_timer, bird_radius, bird_y, bird_x
    
    bird_rect = pygame.Rect(bird_x - bird_radius, bird_y - bird_radius, bird_radius * 2, bird_radius * 2)

    for powerup in powerups[:]:
        if bird_rect.colliderect(powerup['rect']):
            powerup_sound.play()
            if powerup['type'] == 'shield': shield_active = True
            elif powerup['type'] == 'slowmo': slowmo_timer = POWERUP_DURATION
            elif powerup['type'] == 'shrink': shrink_timer = POWERUP_DURATION
            powerups.remove(powerup)

    for pipe in pipes:
        if bird_rect.colliderect(pipe['top_rect']) or bird_rect.colliderect(pipe['bottom_rect']):
            if shield_active:
                shield_active = False
                shield_break_sound.play()
                pipes.remove(pipe)
                return False
            return True
            
    if not 0 <= bird_y <= SCREEN_HEIGHT:
        if shield_active:
            shield_active = False
            shield_break_sound.play()
            bird_y = max(bird_radius, min(bird_y, SCREEN_HEIGHT - bird_radius))
            return False
        return True
        
    return False

def apply_powerup_effects():
    global slowmo_timer, shrink_timer, bird_radius, gravity, pipe_velocity, base_pipe_velocity
    
    if slowmo_timer > 0:
        slowmo_timer -= 1
        pipe_velocity = (base_pipe_velocity - (score / 10)) * 0.5
        gravity = 0.25
    else:
        pipe_velocity = base_pipe_velocity - (score / 10)
        gravity = 0.5

    if shrink_timer > 0:
        shrink_timer -= 1
        bird_radius = original_bird_radius * 0.6
    else:
        bird_radius = original_bird_radius

def reset_game():
    global bird_y, bird_velocity, pipes, score, game_active, frame_count, pipe_velocity, powerups, shield_active, slowmo_timer, shrink_timer, bird_radius, game_paused
    bird_y = SCREEN_HEIGHT // 2
    bird_velocity = 0
    pipes = []
    powerups = []
    score = 0
    frame_count = 0
    pipe_velocity = base_pipe_velocity
    shield_active = False
    slowmo_timer = 0
    shrink_timer = 0
    bird_radius = original_bird_radius
    game_active = True
    game_paused = False

# Main Game Execution
high_score = load_high_score()
running = True

while running:
    # Event Loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_active and not game_paused:
                    bird_velocity = lift
                    flap_sound.play()
                elif not game_active:
                    reset_game()
            if event.key == pygame.K_p: # Pause event
                if game_active:
                    game_paused = not game_paused

    # Drawing
    screen.fill(get_background_color(score))

    if game_active:
        if not game_paused:
            # Game Updates
            bird_velocity += gravity
            bird_y += bird_velocity
            
            apply_powerup_effects()
            
            frame_count += 1
            if frame_count > pipe_spawn_rate:
                pipes.append(create_pipe())
                frame_count = 0

            move_objects()
            update_moving_pipes(pipes)

            for pipe in pipes:
                if not pipe['passed'] and pipe['top_rect'].centerx < bird_x:
                    pipe['passed'] = True
                    score += 1
                    score_sound.play()
            
            if check_collisions():
                crash_sound.play()
                game_active = False
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)

        # Render active game
        draw_bird(bird_x, bird_y)
        for pipe in pipes: draw_pipe(pipe)
        draw_powerups()
        draw_text(str(score), font, WHITE, screen, SCREEN_WIDTH // 2, 50)
        
        if game_paused:
            draw_text("Paused", font, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    else:
        # Render menu screen
        draw_text("Flappy Pygame", font, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
        draw_text("Press SPACE to Start", small_font, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        highscore_text = f"High Score: {high_score}"
        draw_text(highscore_text, small_font, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 / 3 + 60)
        
        if score > 0: # Only show score and medals if a game was played
            score_text = f"Score: {score}"
            draw_text(score_text, small_font, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 / 3 + 20)
            draw_medals(score)


    # Update Display
    pygame.display.update()
    clock.tick(FPS)


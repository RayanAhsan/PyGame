import pygame
import sys
import random
import os
import socket
import math

UDP_IP = "0.0.0.0"  # Listen on all interfaces
UDP_PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("Waiting for UDP messages...")

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
NET_HEIGHT = 100  # Height for all bins
ROUND_TIME = 100  # Time limit per round in seconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

# Create the game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Trash Sorting Game")

# Load images AFTER setting the display
ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")

try:
    background = pygame.image.load(os.path.join(ASSET_DIR, "background.jpg")).convert()

    # Load and resize bin images
    black_bin = pygame.image.load(os.path.join(ASSET_DIR, "black_bin.png")).convert_alpha()
    green_bin = pygame.image.load(os.path.join(ASSET_DIR, "green_bin.png")).convert_alpha()
    blue_bin = pygame.image.load(os.path.join(ASSET_DIR, "blue_bin.png")).convert_alpha()

    BLACK_BIN_WIDTH = 110  # Adjusted width
    GREEN_BIN_WIDTH = 110
    BLUE_BIN_WIDTH = 110

    black_bin = pygame.transform.scale(black_bin, (BLACK_BIN_WIDTH, NET_HEIGHT))
    green_bin = pygame.transform.scale(green_bin, (GREEN_BIN_WIDTH, NET_HEIGHT))
    blue_bin = pygame.transform.scale(blue_bin, (BLUE_BIN_WIDTH, NET_HEIGHT))

    bin_images = {"black": black_bin, "green": green_bin, "blue": blue_bin}

    # Load and resize waste items
    waste_items = {
        "black": [
            pygame.image.load(os.path.join(ASSET_DIR, "pizza_box.png")).convert_alpha(),
            pygame.image.load(os.path.join(ASSET_DIR, "used_tissue.png")).convert_alpha(),
            pygame.image.load(os.path.join(ASSET_DIR, "broken_glass.png")).convert_alpha()
        ],
        "green": [
            pygame.image.load(os.path.join(ASSET_DIR, "banana_peel.png")).convert_alpha(),
            pygame.image.load(os.path.join(ASSET_DIR, "eggshell.png")).convert_alpha(),
            pygame.image.load(os.path.join(ASSET_DIR, "coffee_grounds.png")).convert_alpha()
        ],
        "blue": [
            pygame.image.load(os.path.join(ASSET_DIR, "plastic_bottle.png")).convert_alpha(),
            pygame.image.load(os.path.join(ASSET_DIR, "glass_bottle.png")).convert_alpha(),
            pygame.image.load(os.path.join(ASSET_DIR, "cardboard.png")).convert_alpha()
        ]
    }

    # Resize waste items
    for category in waste_items:
        waste_items[category] = [pygame.transform.scale(item, (50, 50)) for item in waste_items[category]]

except pygame.error as e:
    print(f"Error loading images: {e}")
    sys.exit()

# Font for score & timer
font = pygame.font.Font(None, 36)
title_font = pygame.font.Font(None, 50)

# High score functions
highscore_file = "highscore.txt"

def load_high_score():
    if os.path.exists(highscore_file):
        with open(highscore_file, "r") as file:
            return int(file.read().strip())
    return 0

def save_high_score(score):
    with open(highscore_file, "w") as file:
        file.write(str(score))

high_score = load_high_score()

# Function to generate random bin positions
def generate_nets():
    net_positions = []
    colors = ["black", "blue", "green"]
    random.shuffle(colors)

    while len(net_positions) < 3:
        net_x = random.randint(0, WIDTH - BLUE_BIN_WIDTH)
        if all(abs(net_x - pos[0]) > BLUE_BIN_WIDTH for pos in net_positions):
            net_positions.append((net_x, colors[len(net_positions)]))  
    
    return net_positions

# Game Function
def game():
    global high_score
    waste_x, waste_y = WIDTH // 2, 100
    waste_dropped = False
    score = 0
    start_time = pygame.time.get_ticks()

    nets = generate_nets()
    net_y = HEIGHT - NET_HEIGHT - 10

    waste_type = random.choice(["black", "blue", "green"])
    waste_image = random.choice(waste_items[waste_type])

    # Receiving UDP data
    data, addr = sock.recvfrom(1024)
    print(f"Received message: {data.decode()} from {addr}")
    list_ = data.decode().rsplit(":")
    StartingAngleX = float(list_[0])
    StartingAngleY = float(list_[1])
    StartingAngleZ = float(list_[2])
    heldBack = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        
        elapsed_time = (pygame.time.get_ticks() - start_time) // 1000
        remaining_time = max(0, ROUND_TIME - elapsed_time)

        if remaining_time == 0:
            break

        # Receiving UDP data for movement
        if not waste_dropped:
            
            data, addr = sock.recvfrom(1024)
            print(f"Received message: {data.decode()} from {addr}")
            list_ = data.decode().rsplit(":")
            DeltaAngleX = float(list_[0]) - StartingAngleX
            DeltaAngleY = float(list_[1]) - StartingAngleY
            DeltaAngleZ = float(list_[2]) - StartingAngleZ
            if (keys[pygame.K_SPACE] or (heldBack and DeltaAngleY < 10)):
                waste_dropped = True
                heldBack = False

            if DeltaAngleY > 70 and not heldBack:
                heldBack = True
                StartingAngleY = float(list_[1]) - DeltaAngleY
                StartingAngleZ = float(list_[2])
            elif DeltaAngleY > 70 and heldBack:
                DeltaAngleY = 70
                StartingAngleY = float(list_[1]) - DeltaAngleY
            elif DeltaAngleY < 0 and not heldBack:
                DeltaAngleY = 0
                StartingAngleY = float(list_[1])
            if DeltaAngleZ > 60 and heldBack:
                DeltaAngleZ = 60
                StartingAngleZ = float(list_[2]) - 60
            elif DeltaAngleZ < -60 and heldBack:
                DeltaAngleZ = -60
                StartingAngleZ = float(list_[2]) + 60

        # Object movement logic
        if not waste_dropped and heldBack:
            if DeltaAngleZ < 0:
                waste_x = (WIDTH // 2) - (400 * (math.cos(float(1.5*DeltaAngleZ) * (math.pi) / 180))) + 400
            else:
                waste_x = (WIDTH // 2) + (400 * (math.cos(float(1.5*DeltaAngleZ) * (math.pi) / 180))) - 400

        if waste_dropped:
                waste_y += 5
            

        

        # Check collision with bins
        for net_x, net_color in nets:
            if net_x < waste_x < net_x + 80 and net_y < waste_y < net_y + NET_HEIGHT:
                if net_color == waste_type:
                    score += 1
                else:
                    score -= 1

                waste_dropped = False
                waste_y =  100
                nets = generate_nets()
                waste_type = random.choice(["black", "blue", "green"])
                waste_image = random.choice(waste_items[waste_type])

        if waste_y > HEIGHT:
            waste_dropped = False
            waste_y =  100
            nets = generate_nets()
            waste_type = random.choice(["black", "blue", "green"])
            waste_image = random.choice(waste_items[waste_type])

        screen.blit(background, (0, 0))

        for net_x, net_color in nets:
            screen.blit(bin_images[net_color], (net_x, net_y))

        screen.blit(waste_image, (waste_x, waste_y))

        score_text = font.render(f"Score: {score}", True, BLACK)
        timer_text = font.render(f"Time: {remaining_time}s", True, BLACK)

        screen.blit(score_text, (10, 10))
        screen.blit(timer_text, (WIDTH - 150, 10))
        print(DeltaAngleZ)

        pygame.display.flip()
        pygame.time.Clock().tick(60)

    game()

game()

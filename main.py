import math

import pygame
import random

pygame.init()

# Initialize game window
screen_width, screen_height = 1408, 704
block_size = 64
screen = pygame.display.set_mode((screen_width, screen_height))
back_image = pygame.transform.scale(pygame.image.load('Pics/white_with_black_border.png'), (block_size, block_size))
images = []

# Load plain white tile with black border, scaled to block size
for x in [2, 4, 8, 16, 32, 64, 128]:
    image = pygame.transform.scale(pygame.image.load('Pics/#Block%d.png' % x), (block_size, block_size))
    images.append(image)

# Define move states
class MoveState:
    STAY = None
    FREE = 0
    MOVE = 1

# Check if a block can land at the given grid position
def can_land_here(y, x):
    return (
            0 <= y < screen_height // block_size and      # Y within bounds
            0 <= x < screen_width // 2 // block_size and      # X within left half
            received_blocks.get((y, x)) is None   # Position is empty
    )

class Block:
    def __init__(self, pos, target_pos, level):
        # Basic block set up
        self.level = level  # Determines image
        self.image = images[self.level]  # Grab the right image
        self.rect = self.image.get_rect(center=pos)  # Hitbox stuff

        # Initial motion parameters
        self.speed = [0.3, -0.5]  # Initial velocity (x,y)
        self.acc = [0, 0.0005]  # Acceleration (gravity effect)
        self.pos = list(pos)  # Current position (float)
        self.move_state = MoveState.FREE

        # Calculate launch angle toward mouse click
        rad = self.calc_degree(pos, target_pos)
        self.speed[0] += math.cos(rad) * 0.3 # Add velocity x-component
        self.speed[1] += math.sin(rad) * 0.3 # Add velocity y-component

    def update_movement(self, delta_time):
        if self.move_state == MoveState.FREE:
            # Apply acceleration to velocity
            self.speed[0] += self.acc[0] * delta_time
            self.speed[1] += self.acc[1] * delta_time
            # Apply velocity to position
            self.pos[0] += self.speed[0] * delta_time
            self.pos[1] += self.speed[1] * delta_time
            # Update rectangle position
            self.rect.x, self.rect.y = self.pos
        elif self.move_state == MoveState.MOVE:
            # Move gradually toward target grid cell
            self.pos[0] += (self.target_pos[0] - self.pos[0]) / 5
            self.pos[1] += (self.target_pos[1] - self.pos[1]) / 5
            # Snap to target if close enough
            if abs(self.pos[0] - self.target_pos[0]) < 1 and abs(self.pos[1] - self.target_pos[1]) < 1:
                self.pos = list(self.target_pos)
                self.move_state = MoveState.STAY
            self.rect.center = self.pos  # Sync rect with pos
        elif self.move_state == MoveState.FALL:
            # Fall toward target y-position
            self.pos[0] += (self.target_pos[0] - self.pos[0]) / 5
            self.speed[1] += self.acc[1] * delta_time
            self.pos[1] += self.speed[1] * delta_time
            if self.pos[1] > self.target_pos:
                self.pos = self.target_pos
                self.move_state = MoveState.STAY

    def set_move_state(self, move_state, grid_pos=None):
        # Change move state and update target position if needed
        self.move_state = move_state
        self.grid_pos = grid_pos
        if grid_pos:
            target_x = grid_pos[1] * block_size + block_size // 2 + screen_width // 2
            target_y = grid_pos[0] * block_size + block_size // 2
            self.target_pos = [target_x, target_y]
            self.rect.center = self.target_pos

    def calc_degree(self, ori, tar):
        # Return angle (in radians) from origin to target
        dx = tar[0] - ori[0]
        dy = tar[1] - ori[1]
        return math.atan2(dy, dx) if dx or dy else math.atan2(1, 0)

    def is_horizontal_collision(block, received):
        # Determine if two blocks overlap more horizontally than vertically
        dx = min(block.rect.right, received.rect.right) - max(block.rect.left, received.rect.left)
        dy = min(block.rect.bottom, received.rect.bottom) - max(block.rect.top, received.rect.top)
        return dx <= dy

    def level_up(self):
        # Upgrade block level if not at max
        if self.level < 5:
            self.level += 1
            self.image = images[self.level]
            return True
        return False


# Game state - blocks in motion and blocks that have landed
active_blocks = []   # Currently falling or moving blocks
received_blocks = {}   # Grid of blocks that have landed and stayed
back_blocks = {}   # Background tile rectangle (for visual reference)

# Initialize grid on right half of the screen
for i in range(screen_height // block_size):
    for j in range(screen_width // 2 // block_size):
        rect = pygame.rect.Rect(screen_width // 2 + j * block_size,   # X position offset to right half
                                i * block_size, block_size, block_size
                                )   # Y position
        back_blocks[(i, j)] = rect # Background tile reference
        received_blocks[(i, j)] = None   # No block placed yet

# Main game loop flag
running = True
clock = pygame.time.Clock()  # Controls frame rate
delta_time = 0  # Time passed between frames

def check_and_merge(block, received_blocks):
    y, x = block.grid_pos
    current = block
    merged = False

    # Check adjacent positions (up, down, left, right)
    neighbors = [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]
    for ny, nx in neighbors:
        neighbor = received_blocks.get((ny, nx))
        if neighbor and neighbor.level == current.level and neighbor.move_state == MoveState.STAY:
            if neighbor.level < len(images) - 1:
                # Neighbor levels up, current block is removed
                neighbor.level_up()
                neighbor.image = images[neighbor.level]
                received_blocks[(y, x)] = None
                merged = True
                # Allow chain merges after leveling uo
                check_and_merge(neighbor, received_blocks)
    return merged

# Grid setup
cols = screen_width // 2 // block_size
rows = screen_height // block_size

# Use colum-major storage (each colum is a list of stacked blocks)
received_blocks = [[] for _ in range(cols)]
back_blocks = []

# Create background tiles (visual reference)
for i in range(rows):
    for j in range(cols):
        rect = pygame.rect.Rect(screen_width // 2 + j * block_size, i * block_size, block_size, block_size)
        back_blocks.append((rect, i, j))

    # Game loop setup
    running = True
    clock = pygame.time.Clock()
    delta_time = 0

def stack_or_merge(block, col):
    tower = received_blocks[col]
    if tower and tower[-1].level == block.level:
        # Merge with top block
        tower[-1].level_up()
        tower[-1].image = images[tower[-1].level]
    else:
        # Stack on top
        block.set_move_state(MoveState.MOVE, (rows - len(tower) - 1, col))
        block.grid_pos = (rows - len(tower) - 1, col)
        tower.append(block)
    merge_column(col)
    # Check for horizontal matches after stacking
    clear_horizontal_matches()


def merge_column(col):
    tower = received_blocks[col]
    i = len(tower) - 1
    while i > 0:
        if tower[i].level == tower[i-1].level:
            # Merge top two blocks
            tower[i].level_up()
            tower[i].image = images[tower[i].level]
            del tower[i-1]
            i -= 1  # Stay at same index to check next pair
        else:
            i -= 1

def clear_horizontal_matches():
    changed = False
    # 按行从底到顶遍历
    for row in range(rows):
        # Build a list of blocks on this row from all columns
        this_row = []
        for col in range(cols):
            tower = received_blocks[col]
            # Index of block at this row
            idx = row - (rows - len(tower))
            if 0 <= idx < len(tower):
                this_row.append((col, idx, tower[idx]))
            else:
                this_row.append(None)

        # Scan for runs of matching levels
        start = 0
        while start < cols:
            if not this_row[start]:
                start += 1
                continue
            color = this_row[start][2].level
            end = start + 1
            while end < cols and this_row[end] and this_row[end][2].level == color:
                end += 1
            if end - start >= 2:
                # Found match of 2 or more
                for i in range(start, end):
                    col, idx, _ = this_row[i]
                    del received_blocks[col][idx]
                changed = True
            start = end
    return changed

def random_level():
    # Return a block level based on weighted probability
    r = random.random()
    if r < 0.7:
        return 0
    elif r < 0.88:
        return 1
    elif r < 0.96:
        return 2
    elif r < 0.985:
        return 3
    elif r < 0.995:
        return 4
    elif r < 0.999:
        return 5
    else:
        return 6

level = random_level()

# Game loop
while running:
    # Handle events (quit, mouse, click)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # EXIT GAME
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            mouse_pos = pygame.mouse.get_pos()
            level = random_level()
            # Spawn new block from bottom-left, aimed at mouse
            active_blocks.append(Block([0, screen_height], mouse_pos, level))

    # Clear the screen
    screen.fill((0, 0, 0))

    # Update all active (falling) blocks
    for block in active_blocks[:]:
        block.update_movement(delta_time)

        block_x = int((block.rect.centerx - screen_width // 2) // block_size)

        # Check horizontal bounds
        if block.move_state != MoveState.FREE:
            continue
        if block.rect.right > screen_width:
            block.speed[0] = -abs(block.speed[0])
        if block.rect.left < 0:
            block.speed[0] = abs(block.speed[0])
        if block.rect.top < 0:
            block.speed[1] = abs(block.speed[1])

        # Block has crossed into right-side grid
        if block.rect.centerx > screen_width // 2:
            block_x = int((block.rect.centerx - screen_width // 2) // block_size)
            if 0 <= block_x < cols:
                current_col = received_blocks[block_x]
                stack_x_tolerance = block_size * 0.3

            # Check collisions with blocks in this colum
            collision_with_side = False
            for idx, stacked_block in enumerate(current_col):
                stacked_rect = pygame.Rect(
                    screen_width // 2 + block_x * block_size,
                    (rows - len(current_col) + idx) * block_size,
                    block_size, block_size
                )
                stacked_center_x = screen_width // 2 + block_x * block_size + block_size // 2
                center_dist = abs(block.rect.centerx - stacked_center_x)
                is_vertical = center_dist < stack_x_tolerance
                if block.rect.colliderect(stacked_rect):
                    if not is_vertical:
                        # Side collision - bounce left or right
                        if block.rect.centerx < stacked_center_x:
                            block.speed[0] = -abs(block.speed[0])
                            block.rect.right = stacked_rect.left
                            block.pos[0] = block.rect.x
                        else:
                            block.speed[0] = abs(block.speed[0])
                            block.rect.left = stacked_rect.right
                            block.pos[0] = block.rect.x
                        collision_with_side = True
                        break  # Stop checking once bounced
            if collision_with_side:
                continue  # Skip landing check this frame

            # check if stacking is allowed (aligned horizontally)
            can_stack = False
            if current_col:
                top_block = current_col[-1]
                top_block_center_x = screen_width // 2 + block_x * block_size + block_size // 2
                stack_x_tolerance = block_size * 0.3
                if abs(block.rect.centerx - top_block_center_x) < stack_x_tolerance:
                    can_stack = True

            if current_col:
                # Collision with top of the column
                top_block_center_x = screen_width // 2 + block_x * block_size + block_size // 2

                tower_top_rect = pygame.Rect(
                    screen_width // 2 + block_x * block_size,
                    (rows - len(current_col)) * block_size,
                    block_size, block_size
                )
                if block.rect.colliderect(tower_top_rect) and not can_stack:
                    # Bounce away from tower top
                    if block.rect.centerx < top_block_center_x:
                        block.speed[0] = -abs(block.speed[0])
                        block.rect.right = tower_top_rect.left
                        block.pos[0] = block.rect.x
                    else:
                        block.speed[0] = abs(block.speed[0])
                        block.rect.left = tower_top_rect.right
                        block.pos[0] = block.rect.x
                    continue  # Wait for next frame

            # Block hits ground or stacks on column
            if (not current_col and block.rect.bottom >= screen_height):
                stack_or_merge(block, block_x)
                active_blocks.remove(block)
            elif (current_col and
                  block.rect.colliderect(
                      pygame.Rect(
                          screen_width // 2 + block_x * block_size,
                          (rows - len(current_col)) * block_size,
                          block_size, block_size
                      )
                  ) and can_stack):
                stack_or_merge(block, block_x)
                active_blocks.remove(block)

    # Draw grid background
    for (rect, i, j) in back_blocks:
        screen.blit(back_image, rect)

    # Draw landed blocks
    for j, col in enumerate(received_blocks):
        for idx, block in enumerate(col):
            row = rows - len(col) + idx
            x = screen_width // 2 + j * block_size + block_size // 2
            y = row * block_size + block_size // 2
            block.rect.center = (x, y)
            screen.blit(block.image, block.rect)

     # Draw active (falling) blocks
    for block in active_blocks:
        screen.blit(block.image, block.rect)

    # Refresh display
    pygame.display.flip()
    delta_time = clock.tick(60)

# Exit cleanly
pygame.quit()
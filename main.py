from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random 

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================
W_WIDTH, W_HEIGHT = 1000, 800
GRID_LENGTH = 700
WALL_HEIGHT = 100

current_level = 1
score = 0
game_over = False
game_won = False
frame_count = 0 
cheat_mode = False 

# --- SPEED ADJUSTMENTS (PLAYER) ---
player = {
    'x': 0, 'y': 0, 'angle': 0, 
    'lives': 10, 'max_lives': 10, 
    'speed': 1.5,      # Reduced from 8.0 to 1.5 for control
    'rot_speed': 3.0,  # Reduced rotation speed
    'collision_cooldown': 0, 
    'obstacle_cooldown': 0
}

bullets = [] 
enemies = []   
obstacles = [] # Placeholder for Member 3
trees = []     # Placeholder for Member 3
camera_mode = "FOLLOW"

# =============================================================================
# MATH HELPER FUNCTIONS
# =============================================================================

def deg_to_rad(deg):
    return deg * (math.pi / 180.0)

def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def get_vector(x1, y1, x2, y2):
    dist = distance(x1, y1, x2, y2)
    if dist == 0: return 0, 0
    return (x2 - x1) / dist, (y2 - y1) / dist

# =============================================================================
# GAME LOGIC (MEMBER 2 WORK AREA)
# =============================================================================

def create_enemy(hp, spd, dmg, col, scl, shoots=False):
    return {
        'x': 0, 'y': 0, 
        'active': True, 
        'health': hp,   
        'speed': spd,
        'damage': dmg,  
        'color': col, 
        'scale': scl,
        'can_shoot': shoots,
        'last_shot_frame': frame_count + random.randint(0, 100)
    }

def init_level(level):
    global obstacles, enemies, bullets, trees, game_over, game_won, frame_count, player
    
    # Reset basics
    player['x'], player['y'] = 0, 0
    player['collision_cooldown'] = 0
    game_over = False
    game_won = False
    bullets = []
    obstacles = [] 
    trees = []     
    enemies = []   

    # --- LEVEL SPAWNING LOGIC (SPEEDS REDUCED TO ~1/30th) ---
    
    # LEVEL 01: Slow, basic enemies
    # Speed: 0.07 (Original was 2.0)
    if level == 1:
        for _ in range(5):
            ex = random.randint(-500, 500)
            ey = random.randint(-500, 500)
            if distance(0, 0, ex, ey) < 300: continue
            
            e = create_enemy(60, 0.07, 0.5, (0.6, 0.6, 0.7), 1.2, shoots=False)
            e['x'], e['y'] = ex, ey
            enemies.append(e)

    # LEVEL 02: Faster, red enemies
    # Speed: 0.12 (Original was 3.5)
    elif level == 2:
        for _ in range(8):
            ex = random.randint(-600, 600)
            ey = random.randint(-600, 600)
            if distance(0, 0, ex, ey) < 300: continue
            
            e = create_enemy(40, 0.12, 0.8, (0.8, 0.2, 0.2), 1.0, shoots=False)
            e['x'], e['y'] = ex, ey
            enemies.append(e)

    # LEVEL 03: Boss + Minions
    elif level == 3:
        # BOSS: Very slow but tanky
        # Speed: 0.05 (Original was 1.5)
        e = create_enemy(400, 0.05, 2.0, (0.1, 0.1, 0.1), 3.0, shoots=True)
        e['x'], e['y'] = 0, 600
        e['bullet_damage'] = 30 
        enemies.append(e)
        
        # MINIONS
        # Speed: 0.10 (Original was 3.0)
        for _ in range(6):
            ex = random.randint(-600, 600)
            ey = random.randint(-600, 600)
            if distance(0, 0, ex, ey) < 400: continue
            e = create_enemy(20, 0.10, 0.5, (0.9, 0.5, 0.0), 0.8, shoots=False)
            e['x'], e['y'] = ex, ey
            enemies.append(e)

def update_bullets():
    global bullets, player, score, enemies
    
    for b in bullets[:]:
        b['x'] += b['dx']
        b['y'] += b['dy']
        
        # Bounds check
        if abs(b['x']) > GRID_LENGTH or abs(b['y']) > GRID_LENGTH:
            bullets.remove(b)
            continue
            
        # Bullet vs Enemy Collision
        if b['owner'] == 'player':
            for e in enemies:
                if e['active'] and distance(b['x'], b['y'], e['x'], e['y']) < (25 * e['scale']):
                    damage = 15 
                    e['health'] -= damage
                    if b in bullets: bullets.remove(b)
                    
                    if e['health'] <= 0:
                        e['active'] = False
                        score += 100
                    break
        
        # Enemy Bullet vs Player
        elif b['owner'] == 'enemy':
            if distance(b['x'], b['y'], player['x'], player['y']) < 25:
                if player['collision_cooldown'] == 0:
                    player['lives'] -= 1
                    player['collision_cooldown'] = 120 # Invincibility frames
                if b in bullets: bullets.remove(b)
                break

def update_enemies():
    global enemies, player, bullets, frame_count
    active_count = 0
    
    if player['collision_cooldown'] > 0:
        player['collision_cooldown'] -= 1
    
    for e in enemies:
        if not e['active']: continue
        active_count += 1
        
        dx, dy = get_vector(e['x'], e['y'], player['x'], player['y'])
        dist_to_player = distance(e['x'], e['y'], player['x'], player['y'])
        
        # 1. Movement (Chase Player)
        if dist_to_player > 20: 
            e['x'] += dx * e['speed']
            e['y'] += dy * e['speed']

        # 2. Collision (Body Slam)
        collision_dist = 30 * e['scale'] 
        if dist_to_player < collision_dist:
            if player['collision_cooldown'] == 0:
                player['lives'] -= 1
                player['collision_cooldown'] = 120 

        # 3. Boss Shooting Logic
        if e['can_shoot']:
            # Fire every ~3 seconds (200 frames)
            if frame_count - e['last_shot_frame'] >= 200:
                e['last_shot_frame'] = frame_count
                
                # Boss Bullet Speed: 0.2 (Original was 5.0)
                bullets.append({
                    'x': e['x'], 'y': e['y'],
                    'dx': dx * 0.2, 
                    'dy': dy * 0.2,
                    'owner': 'enemy',
                    'damage': e.get('bullet_damage', 10)
                })

    return active_count

# =============================================================================
# VISUALS (DRAWING FUNCTIONS)
# =============================================================================

def draw_tank(x, y, angle, color, scale=1.0):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(scale, scale, scale)
    glRotatef(angle, 0, 0, 1)

    # Simple Body
    glColor3f(color[0], color[1], color[2])
    glPushMatrix()
    glTranslatef(0, 0, 10)
    glScalef(2.0, 1.2, 0.8)
    glutSolidCube(10)
    glPopMatrix()
    
    # Turret
    glColor3f(color[0]*0.8, color[1]*0.8, color[2]*0.8)
    glPushMatrix()
    glTranslatef(0, 0, 15)
    glutSolidCube(6)
    glPopMatrix()
    
    glPopMatrix()

def draw_arena_basic():
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, -1)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, -1)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, -1)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, -1)
    glEnd()

def draw_text(x, y, text):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, W_WIDTH, 0, W_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# =============================================================================
# INPUT & MAIN LOOP
# =============================================================================

def keyboardListener(key, x, y):
    global player, game_over, current_level, game_won
    try: key = key.decode('utf-8')
    except: pass
    
    # Restart
    if key == 'r':
        current_level = 1
        score = 0
        player['lives'] = player['max_lives']
        init_level(1)
        return

    # Next Level
    if key == 'n' and game_won:
        if current_level < 3:
            current_level += 1
            init_level(current_level)

    if not game_over:
        rad = deg_to_rad(player['angle'])
        if key == 'w':
            player['x'] += math.cos(rad) * player['speed']
            player['y'] += math.sin(rad) * player['speed']
        if key == 's':
            player['x'] -= math.cos(rad) * player['speed']
            player['y'] -= math.sin(rad) * player['speed']
        if key == 'a':
            player['angle'] += player['rot_speed']
        if key == 'd':
            player['angle'] -= player['rot_speed']
            
        # Boundaries
        player['x'] = max(-GRID_LENGTH + 20, min(GRID_LENGTH - 20, player['x']))
        player['y'] = max(-GRID_LENGTH + 20, min(GRID_LENGTH - 20, player['y']))

def mouseListener(button, state, x, y):
    global bullets, player, game_over
    if game_over: return
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        rad = deg_to_rad(player['angle'])
        bullets.append({
            'x': player['x'], 'y': player['y'],
            'dx': math.cos(rad) * 4.0, # Bullet Speed (Moderated)
            'dy': math.sin(rad) * 4.0,
            'owner': 'player'
        })

def idle():
    global game_over, game_won, frame_count
    frame_count += 1
    
    if game_over or game_won:
        glutPostRedisplay()
        return

    update_bullets()
    active_enemies = update_enemies() 
    
    # Win/Loss conditions
    if player['lives'] <= 0:
        game_over = True
    elif active_enemies == 0:
        game_won = True
        
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Basic Camera
    gluPerspective(60, W_WIDTH/W_HEIGHT, 0.1, 3000)
    rad = deg_to_rad(player['angle'])
    cx = player['x'] - math.cos(rad) * 300
    cy = player['y'] - math.sin(rad) * 300
    gluLookAt(cx, cy, 300, player['x'], player['y'], 20, 0, 0, 1)

    draw_arena_basic()
    
    # Draw Player (Green)
    if player['lives'] > 0:
        if player['collision_cooldown'] % 10 < 5: 
            draw_tank(player['x'], player['y'], player['angle'], (0.2, 0.85, 0.25))

    # Draw Enemies
    for e in enemies:
        if e['active']:
            dx, dy = get_vector(e['x'], e['y'], player['x'], player['y'])
            angle = math.degrees(math.atan2(dy, dx))
            draw_tank(e['x'], e['y'], angle, e['color'], e['scale'])

    # Draw Bullets
    for b in bullets:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], 15)
        if b['owner'] == 'player':
            glColor3f(1, 1, 0)
            sz = 2
        else:
            glColor3f(1, 0, 0) 
            sz = 3
        glutSolidCube(sz)
        glPopMatrix()

    # Simple HUD
    draw_text(10, 770, f"LEVEL {current_level} | SCORE: {score} | LIVES: {player['lives']}")
    
    if game_over:
        draw_text(W_WIDTH//2 - 100, W_HEIGHT//2, "GAME OVER! Press 'R'")
    if game_won:
        draw_text(W_WIDTH//2 - 150, W_HEIGHT//2, "VICTORY! Press 'N' for Next Level")

    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(W_WIDTH, W_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Tank Battle - Stage 2 (Balanced Speed)")
    
    init_level(1)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
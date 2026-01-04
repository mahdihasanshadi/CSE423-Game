from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random


W_WIDTH, W_HEIGHT = 1000, 800
GRID_LENGTH = 700
WALL_HEIGHT = 100

current_level = 1
score = 0
game_over = False
game_won = False
cheat_mode = False
night_mode = False

frame_count = 0 

player = {
    'x': 0, 'y': 0, 'angle': 0, 
    'lives': 10, 'max_lives': 10,  
    'speed': 8.0, 'rot_speed': 5.0,
    'collision_cooldown': 0,
    'obstacle_cooldown': 0  
}

bullets = [] 
enemies = [] 
obstacles = [] 
trees = []  
camera_mode = "FOLLOW"



def deg_to_rad(deg):
    return deg * (math.pi / 180.0)

def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def get_vector(x1, y1, x2, y2):
    dist = distance(x1, y1, x2, y2)
    if dist == 0: return 0, 0
    return (x2 - x1) / dist, (y2 - y1) / dist


def init_level(level):
    global obstacles, enemies, bullets, trees, game_over, game_won, frame_count
    
    obstacles = []
    enemies = []
    bullets = []
    trees = [] 
    
    player['x'], player['y'] = 0, 0
    player['collision_cooldown'] = 0
    player['obstacle_cooldown'] = 0
    game_over = False
    game_won = False
    
    obstacles = []
    obstacle_count = 15 + (level * 5)
    
    for i in range(obstacle_count):
        ox = random.randint(-GRID_LENGTH + 60, GRID_LENGTH - 60)
        oy = random.randint(-GRID_LENGTH + 60, GRID_LENGTH - 60)
        if distance(0, 0, ox, oy) < 200: continue
        
        obs_type = i % 2 
        size = random.randint(40, 60)
        damage = 1 if obs_type == 0 else 2  
        
        obstacles.append({
            'x': ox, 'y': oy, 
            'size': size,
            'type': obs_type, 
            'damage': damage
        })
    tree_count = 20 + (level * 5)
    for i in range(tree_count):
        tx = random.randint(-GRID_LENGTH + 80, GRID_LENGTH - 80)
        ty = random.randint(-GRID_LENGTH + 80, GRID_LENGTH - 80)
        # Make sure trees are not too close to spawn point or obstacles
        if distance(0, 0, tx, ty) < 250: continue
        too_close_to_obs = False
        for obs in obstacles:
            if distance(tx, ty, obs['x'], obs['y']) < 80:
                too_close_to_obs = True
                break
        if too_close_to_obs: continue
        
        trees.append({
            'x': tx,
            'y': ty,
            'size': random.randint(50, 80), 
            'type': i % 3  
        })

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

    if level == 1:
        for _ in range(5):
            ex = random.randint(-500, 500)
            ey = random.randint(-500, 500)
            if distance(0, 0, ex, ey) < 300: continue
            e = create_enemy(60, 0.05, 0.5, (0.6, 0.6, 0.7), 1.2, shoots=False)
            e['x'], e['y'] = ex, ey
            enemies.append(e)
    elif level == 2:
        for _ in range(8):
            ex = random.randint(-600, 600)
            ey = random.randint(-600, 600)
            if distance(0, 0, ex, ey) < 300: continue
            e = create_enemy(40, 0.08, 0.8, (0.8, 0.2, 0.2), 1.0, shoots=False)
            e['x'], e['y'] = ex, ey
            enemies.append(e)
    elif level == 3:
        e = create_enemy(400, 0.02, 2.0, (0.1, 0.1, 0.1), 3.0, shoots=True)
        e['x'], e['y'] = 0, 600
        e['bullet_damage'] = 30 
        enemies.append(e)
    
        for _ in range(6):
            ex = random.randint(-600, 600)
            ey = random.randint(-600, 600)
            if distance(0, 0, ex, ey) < 400: continue
            e = create_enemy(20, 0.06, 0.5, (0.9, 0.5, 0.0), 0.8, shoots=False)
            e['x'], e['y'] = ex, ey
            enemies.append(e)

def draw_wall(x, y, w, h, d):
    glPushMatrix()
    glTranslatef(x, y, d/2)
    glScalef(w, h, d)
    glutSolidCube(1)
    glPopMatrix()

def draw_obstacle(obs):
    """Draw brick-shaped obstacles"""
    global night_mode
    glPushMatrix()
    glTranslatef(obs['x'], obs['y'], 0)
    size = obs['size']
    obs_type = obs['type']
    brick_width = size * 1.5
    brick_height = size * 0.7
    brick_depth = size * 0.8
    
    if obs_type == 0:  
        if night_mode:
            glColor3f(0.6, 0.15, 0.15)
        else:
            glColor3f(0.8, 0.2, 0.2)  
    else: 
        if night_mode:
            glColor3f(0.3, 0.3, 0.35)
        else:
            glColor3f(0.5, 0.5, 0.55) 

    glPushMatrix()
    glTranslatef(0, 0, brick_depth/2)
    glScalef(brick_width, brick_height, brick_depth)
    glutSolidCube(1)
    glPopMatrix()
    
    # Add brick texture lines (mortar lines) for realism
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_LINES)
    # Horizontal line
    glVertex3f(-brick_width*0.5, 0, brick_depth*0.55)
    glVertex3f(brick_width*0.5, 0, brick_depth*0.55)
    # Vertical lines
    glVertex3f(-brick_width*0.3, -brick_height*0.5, brick_depth*0.55)
    glVertex3f(-brick_width*0.3, brick_height*0.5, brick_depth*0.55)
    glVertex3f(brick_width*0.3, -brick_height*0.5, brick_depth*0.55)
    glVertex3f(brick_width*0.3, brick_height*0.5, brick_depth*0.55)
    glEnd()
    
    glPopMatrix()

def draw_tree(tree):
    """Draw a decorative tree (non-dangerous)"""
    global night_mode
    glPushMatrix()
    glTranslatef(tree['x'], tree['y'], 0)
    size = tree['size']
    tree_type = tree['type']
    q = gluNewQuadric()
    
    if night_mode:
        glColor3f(0.3, 0.2, 0.15)  
    else:
        glColor3f(0.4, 0.25, 0.15) 
    glPushMatrix()
    glTranslatef(0, 0, size * 0.3)
    glRotatef(90, 1, 0, 0)
    gluCylinder(q, size * 0.12, size * 0.12, size * 0.6, 8, 1)
    glPopMatrix()
    
    if tree_type == 0: 
        if night_mode:
            glColor3f(0.05, 0.15, 0.05)  
        else:
            glColor3f(0.1, 0.5, 0.1)  
        glPushMatrix()
        glTranslatef(0, 0, size * 0.7)
        gluSphere(q, size * 0.4, 10, 10)
        glPopMatrix()
        
    elif tree_type == 1:  
        if night_mode:
            glColor3f(0.08, 0.2, 0.08)  
        else:
            glColor3f(0.15, 0.6, 0.15) 
        glPushMatrix()
        glTranslatef(0, 0, size * 0.65)
        gluSphere(q, size * 0.35, 10, 10)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(size * 0.15, 0, size * 0.85)
        gluSphere(q, size * 0.3, 10, 10)
        glPopMatrix()
        
    else:  
        if night_mode:
            glColor3f(0.1, 0.25, 0.1)  
        else:
            glColor3f(0.2, 0.7, 0.2)  
        glPushMatrix()
        glTranslatef(0, 0, size * 0.75)
        gluSphere(q, size * 0.4, 10, 10)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(size * 0.2, size * 0.15, size * 0.85)
        gluSphere(q, size * 0.32, 10, 10)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-size * 0.15, size * 0.1, size * 0.9)
        gluSphere(q, size * 0.28, 10, 10)
        glPopMatrix()
    
    glPopMatrix()

def draw_arena():
    global night_mode
    

    if night_mode:
        glColor3f(0.05, 0.05, 0.1) 
    else:
        glColor3f(0.4, 0.5, 0.6)  
    glBegin(GL_QUADS)
    glVertex3f(-3000, -3000, -500)
    glVertex3f(3000, -3000, -500)
    glVertex3f(3000, 3000, -500)
    glVertex3f(-3000, 3000, -500)
    glEnd()
    
    # Floor - Brown ground color (Day/Night)
    if night_mode:
        glColor3f(0.2, 0.15, 0.1)  # Dark brown for night
    else:
        glColor3f(0.4, 0.3, 0.2)  # Brown ground for day
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, -1)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, -1)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, -1)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, -1)
    glEnd()

    # Grid - Day/Night colors
    if night_mode:
        glColor3f(0.15, 0.15, 0.25)  # Dim blue lines for night
    else:
        glColor3f(0.4, 0.42, 0.45)  # Brighter grid for day
    glBegin(GL_LINES)
    step = 50
    for i in range(-GRID_LENGTH, GRID_LENGTH + 1, step):
        glVertex3f(-GRID_LENGTH, i, 0.1)
        glVertex3f(GRID_LENGTH, i, 0.1)
        glVertex3f(i, -GRID_LENGTH, 0.1)
        glVertex3f(i, GRID_LENGTH, 0.1)
    glEnd()

    # Borders - Day/Night colors
    if night_mode:
        glColor3f(0.3, 0.05, 0.15)  # Darker red for night
    else:
        glColor3f(0.6, 0.15, 0.2)  # Brighter red for day
    thk = 20 
    draw_wall(0, GRID_LENGTH + thk/2, GRID_LENGTH*2 + thk*2, thk, WALL_HEIGHT)
    draw_wall(0, -GRID_LENGTH - thk/2, GRID_LENGTH*2 + thk*2, thk, WALL_HEIGHT)
    draw_wall(GRID_LENGTH + thk/2, 0, thk, GRID_LENGTH*2, WALL_HEIGHT)
    draw_wall(-GRID_LENGTH - thk/2, 0, thk, GRID_LENGTH*2, WALL_HEIGHT)

def draw_tank(x, y, angle, color, scale=1.0):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(scale, scale, scale)
    glRotatef(angle, 0, 0, 1)

    # Treads - Enhanced design
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(0, 15, 5)
    glScalef(2.5, 0.5, 1.0)
    glutSolidCube(10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, -15, 5)
    glScalef(2.5, 0.5, 1.0)
    glutSolidCube(10)
    glPopMatrix()

    # Body - More stylized
    glColor3f(color[0], color[1], color[2])
    glPushMatrix()
    glTranslatef(0, 0, 12)
    glScalef(2.0, 1.2, 0.8)
    glutSolidCube(15)
    glPopMatrix()
    
    # Side panels for cooler look
    glColor3f(color[0]*0.7, color[1]*0.7, color[2]*0.7)
    glPushMatrix()
    glTranslatef(8, 0, 12)
    glScalef(0.3, 1.2, 0.8)
    glutSolidCube(15)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-8, 0, 12)
    glScalef(0.3, 1.2, 0.8)
    glutSolidCube(15)
    glPopMatrix()

    # Turret
    glColor3f(color[0]*0.8, color[1]*0.8, color[2]*0.8)
    glPushMatrix()
    glTranslatef(-5, 0, 22)
    q = gluNewQuadric()
    gluSphere(q, 8, 10, 10)
    
    # Barrel - Thicker and more powerful looking
    glColor3f(0.2, 0.2, 0.2)
    glTranslatef(10, 0, 0)
    glRotatef(90, 0, 1, 0)
    gluCylinder(q, 2.5, 2.5, 22, 10, 10)
    glPopMatrix()
    glPopMatrix()

def draw_text(x, y, text, color=(1,1,1)):
    glColor3f(color[0], color[1], color[2])
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

def draw_crosshair():
    """Draw a crosshair/aimer at the center of the screen"""
    center_x = W_WIDTH / 2
    center_y = W_HEIGHT / 2
    size = 15  # Crosshair size
    gap = 5  # Gap in the center
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, W_WIDTH, 0, W_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw crosshair lines - white with slight transparency effect
    glColor3f(1.0, 1.0, 1.0)  # White color
    glBegin(GL_LINES)
    
    # Top line
    glVertex3f(center_x, center_y + gap, 0)
    glVertex3f(center_x, center_y + size, 0)
    
    # Bottom line
    glVertex3f(center_x, center_y - gap, 0)
    glVertex3f(center_x, center_y - size, 0)
    
    # Left line
    glVertex3f(center_x - gap, center_y, 0)
    glVertex3f(center_x - size, center_y, 0)
    
    # Right line
    glVertex3f(center_x + gap, center_y, 0)
    glVertex3f(center_x + size, center_y, 0)
    
    glEnd()
    
    # Draw center dot
    glBegin(GL_LINES)
    glVertex3f(center_x - 1, center_y, 0)
    glVertex3f(center_x + 1, center_y, 0)
    glVertex3f(center_x, center_y - 1, 0)
    glVertex3f(center_x, center_y + 1, 0)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def update_bullets():
    global bullets, player, score, enemies, cheat_mode
    
    for b in bullets[:]:
        b['x'] += b['dx']
        b['y'] += b['dy']
        
        # Bounds check
        if abs(b['x']) > GRID_LENGTH or abs(b['y']) > GRID_LENGTH:
            bullets.remove(b)
            continue
            
        hit_obs = False
        for obs in obstacles:
            brick_width = obs['size'] * 1.5
            brick_height = obs['size'] * 0.7
            collision_dist = max(brick_width, brick_height) * 0.5
            dist_to_bullet = distance(b['x'], b['y'], obs['x'], obs['y'])
            if dist_to_bullet < collision_dist:
                hit_obs = True
                score += 5  # Bonus for destroying obstacles
                respawn_obstacle(obs)
                break
        if hit_obs:
            bullets.remove(b)
            continue

        if b['owner'] == 'player':
            for e in enemies:
                if e['active'] and distance(b['x'], b['y'], e['x'], e['y']) < (25 * e['scale']):
                    damage = 1000 if cheat_mode else 15  # Slightly more damage
                    e['health'] -= damage
                    if b in bullets: bullets.remove(b)
                    if e['health'] <= 0:
                        e['active'] = False
                        score += 100
                    break
        
        # Enemy (Boss) Bullet vs Player - Now reduces lives in cheat mode
        elif b['owner'] == 'enemy':
            if distance(b['x'], b['y'], player['x'], player['y']) < 25:
                if not cheat_mode and player['collision_cooldown'] == 0:
                    player['lives'] -= 1
                    player['collision_cooldown'] = 120  # 2 seconds cooldown at 60fps
                if b in bullets: bullets.remove(b)
                break

def respawn_obstacle(obs):
    """Respawn obstacle at a new random location"""
    max_attempts = 50
    for _ in range(max_attempts):
        new_x = random.randint(-GRID_LENGTH + 60, GRID_LENGTH - 60)
        new_y = random.randint(-GRID_LENGTH + 60, GRID_LENGTH - 60)
        
        if distance(new_x, new_y, player['x'], player['y']) > 150:
            too_close = False
            for other_obs in obstacles:
                if distance(new_x, new_y, other_obs['x'], other_obs['y']) < 100:
                    too_close = True
                    break
            if not too_close:
                obs['x'] = new_x
                obs['y'] = new_y
                obs['size'] = random.randint(40, 60)
                return
    obs['x'] = random.randint(-GRID_LENGTH + 60, GRID_LENGTH - 60)
    obs['y'] = random.randint(-GRID_LENGTH + 60, GRID_LENGTH - 60)

def update_obstacles():
    """Check collision with player and handle respawning"""
    global obstacles, player, cheat_mode
    
    # Update obstacle cooldown
    if player['obstacle_cooldown'] > 0:
        player['obstacle_cooldown'] -= 1
    
    for obs in obstacles:
        brick_width = obs['size'] * 1.5
        brick_height = obs['size'] * 0.7
        collision_dist = max(brick_width, brick_height) * 0.5
        
        dist_to_player = distance(obs['x'], obs['y'], player['x'], player['y'])
        
        if dist_to_player < collision_dist:
            if not cheat_mode and player['obstacle_cooldown'] == 0:
                player['lives'] -= obs['damage']
                player['obstacle_cooldown'] = 90  # 1.5 seconds cooldown
                # Respawn obstacle at new location
                respawn_obstacle(obs)

def update_enemies():
    global enemies, player, bullets, cheat_mode, frame_count
    active_count = 0
    
    if player['collision_cooldown'] > 0:
        player['collision_cooldown'] -= 1
    
    for e in enemies:
        if not e['active']: continue
        active_count += 1
        
        dx, dy = get_vector(e['x'], e['y'], player['x'], player['y'])
        dist_to_player = distance(e['x'], e['y'], player['x'], player['y'])
        
        # 1. Movement
        if dist_to_player > 20: 
            e['x'] += dx * e['speed']
            e['y'] += dy * e['speed']

        collision_dist = 30 * e['scale'] 
        if dist_to_player < collision_dist:
            if not cheat_mode and player['collision_cooldown'] == 0:
                player['lives'] -= 1
                player['collision_cooldown'] = 120  # 2 seconds cooldown

        if e['can_shoot']:
            if frame_count - e['last_shot_frame'] >= 200:
                e['last_shot_frame'] = frame_count
                
                # Boss Bullet Speed
                bullet_speed = 0.16 
                
                bullets.append({
                    'x': e['x'], 'y': e['y'],
                    'dx': dx * bullet_speed, 
                    'dy': dy * bullet_speed,
                    'owner': 'enemy',
                    'damage': e.get('bullet_damage', 10)
                })

    return active_count

def keyboardListener(key, x, y):
    global camera_mode, current_level, game_over, cheat_mode, night_mode, player
    try: key = key.decode('utf-8')
    except: pass
    
    if not game_over:
        # Enhanced movement - even faster in cheat mode
        speed_mult = 1.5 if cheat_mode else 1.0
        rad = deg_to_rad(player['angle'])
        if key == 'w':
            player['x'] += math.cos(rad) * player['speed'] * speed_mult
            player['y'] += math.sin(rad) * player['speed'] * speed_mult
        if key == 's':
            player['x'] -= math.cos(rad) * player['speed'] * speed_mult
            player['y'] -= math.sin(rad) * player['speed'] * speed_mult
        if key == 'a':
            player['angle'] += player['rot_speed'] * speed_mult
        if key == 'd':
            player['angle'] -= player['rot_speed'] * speed_mult
            
        player['x'] = max(-GRID_LENGTH + 20, min(GRID_LENGTH - 20, player['x']))
        player['y'] = max(-GRID_LENGTH + 20, min(GRID_LENGTH - 20, player['y']))

    if key == 'h':
        cheat_mode = not cheat_mode
        print(f"Cheat Mode: {'ON' if cheat_mode else 'OFF'}")

    if key == 'm' or key == 'M':
        night_mode = not night_mode
        print(f"Night Mode: {'ON' if night_mode else 'OFF'}")

    if key == 'c':
        if camera_mode == "FOLLOW":
            camera_mode = "TOP"
        elif camera_mode == "TOP":
            camera_mode = "FIRST_PERSON"
        else:
            camera_mode = "FOLLOW"
        print(f"Camera Mode: {camera_mode}")
    if key == 'n' and game_won:
        if current_level < 3:
            current_level += 1
            init_level(current_level)
    if key == 'r':
        current_level = 1
        score = 0
        player['lives'] = player['max_lives']
        init_level(1)

def mouseListener(button, state, x, y):
    global bullets, cheat_mode, frame_count, player
    if game_over: return
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        rad = deg_to_rad(player['angle'])
        # Faster bullets in cheat mode
        bullet_speed = 1.8 if cheat_mode else 1.2
        bullets.append({
            'x': player['x'], 'y': player['y'],
            'dx': math.cos(rad) * bullet_speed, 
            'dy': math.sin(rad) * bullet_speed,
            'owner': 'player'
        })

def idle():
    global game_over, game_won, frame_count
    
    frame_count += 1
    
    if game_over or game_won:
        glutPostRedisplay()
        return

    update_bullets()
    update_obstacles()  
    active_enemies = update_enemies()

    if player['lives'] <= 0:
        game_over = True
    elif active_enemies == 0:
        game_won = True
    glutPostRedisplay()

def showScreen():
    global night_mode
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, W_WIDTH/W_HEIGHT, 0.1, 3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if camera_mode == "FOLLOW":
        rad = deg_to_rad(player['angle'])
        cx = player['x'] - math.cos(rad) * 300
        cy = player['y'] - math.sin(rad) * 300
        gluLookAt(cx, cy, 300, player['x'], player['y'], 20, 0, 0, 1)
    elif camera_mode == "FIRST_PERSON":
        rad = deg_to_rad(player['angle'])
        eye_x = player['x']
        eye_y = player['y']
        eye_z = 30  
        look_x = player['x'] + math.cos(rad) * 100
        look_y = player['y'] + math.sin(rad) * 100
        look_z = 25  # Look slightly downward
        gluLookAt(eye_x, eye_y, eye_z, look_x, look_y, look_z, 0, 0, 1)
    else:  # TOP view
        gluLookAt(0, 0, 1800, 0, 0, 0, 0, 1, 0)

    draw_arena()
    
    for tree in trees:
        draw_tree(tree)
    
    for obs in obstacles:
        draw_obstacle(obs)
    if player['lives'] > 0 and camera_mode != "FIRST_PERSON":
        if cheat_mode:
            p_color = (1.0, 0.9, 0.0)  
        elif night_mode:
            p_color = (0.1, 0.9, 0.3)  
        else:
            p_color = (0.2, 0.85, 0.25)  
        draw_tank(player['x'], player['y'], player['angle'], p_color)

    # Draw Enemies
    for e in enemies:
        if e['active']:
            dx, dy = get_vector(e['x'], e['y'], player['x'], player['y'])
            angle = math.degrees(math.atan2(dy, dx))
            draw_tank(e['x'], e['y'], angle, e['color'], e['scale'])

  
    for b in bullets:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], 15)
        if b['owner'] == 'player':
            if cheat_mode:
                glColor3f(1, 1, 0.2)  
                sz = 4
            else:
                glColor3f(1, 0.9, 0.3) 
                sz = 3
        else:
            glColor3f(1, 0.1, 0.1) 
            sz = 5
            
        gluSphere(gluNewQuadric(), sz, 8, 8)
        glPopMatrix()

    text_color = (0.9, 0.9, 0.9) if night_mode else (0.1, 0.1, 0.1)
    draw_text(10, 770, f"LEVEL {current_level} | SCORE: {score}", text_color)
  
    lives_text = "LIVES: INFINITE" if cheat_mode else f"LIVES: {player['lives']}"
    lives_color = (1, 0.9, 0) if cheat_mode else (1, 0.3, 0.3) if player['lives'] <= 2 else text_color
    draw_text(10, 740, lives_text, lives_color)
 
    if cheat_mode:
        draw_text(W_WIDTH - 280, 770, "CHEAT MODE ON (H)", (1, 0.9, 0))
    if night_mode:
        draw_text(W_WIDTH - 280, 740, "NIGHT MODE (M)", (0.5, 0.7, 1))
    else:
        draw_text(W_WIDTH - 280, 740, "DAY MODE (M)", (1, 0.8, 0.3))
    
    camera_text = f"C: Camera ({camera_mode})"
    draw_text(10, 710, f"WASD: Move | Click: Shoot | {camera_text} | M: Day/Night | H: Cheat", (0.6, 0.6, 0.6))
    
    draw_crosshair()
    
    if game_over:
        draw_text(W_WIDTH//2 - 120, W_HEIGHT//2, "GAME OVER! Press 'R' to Restart", (1, 0.2, 0.2))
    if game_won:
        msg = "LEVEL COMPLETE! Press 'N' for Next Level" if current_level < 3 else "VICTORY! Press 'R' to Play Again"
        draw_text(W_WIDTH//2 - 180, W_HEIGHT//2, msg, (0.2, 1, 0.2))

    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(W_WIDTH, W_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D Tank Battle: Student Project")
    
    init_level(1)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
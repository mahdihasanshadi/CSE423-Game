from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# =============================================================================
# MEMBER 1: GLOBAL VARIABLES
# =============================================================================
W_WIDTH, W_HEIGHT = 1000, 800
GRID_LENGTH = 700
game_over = False
game_won = False
score = 0
frame_count = 0

player = {
    'x': 0, 'y': 0, 'angle': 0, 
    'lives': 10, 'max_lives': 10,
    'speed': 8.0, 'rot_speed': 5.0,
    'collision_cooldown': 0,
    'obstacle_cooldown': 0
}

bullets = [] 
enemies = [] # Placeholder for Member 2
obstacles = [] # Placeholder for Member 3
trees = [] # Placeholder for Member 3

# =============================================================================
# MEMBER 1: MATH HELPERS
# =============================================================================
def deg_to_rad(deg):
    return deg * (math.pi / 180.0)

def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def get_vector(x1, y1, x2, y2):
    dist = distance(x1, y1, x2, y2)
    if dist == 0: return 0, 0
    return (x2 - x1) / dist, (y2 - y1) / dist

# ===================================================================
# MEMBER 1: CORE LOGIC
# ===================================================================
def init_level(level):
    global player, bullets, game_over
    player['x'], player['y'] = 0, 0
    bullets = []
    game_over = False
    # Member 2 and 3 will add code here later

def update_bullets():
    global bullets
    for b in bullets[:]:
        b['x'] += b['dx']
        b['y'] += b['dy']
        # Remove if out of bounds
        if abs(b['x']) > GRID_LENGTH or abs(b['y']) > GRID_LENGTH:
            bullets.remove(b)

def keyboardListener(key, x, y):
    global player
    try: key = key.decode('utf-8')
    except: pass
    
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

def mouseListener(button, state, x, y):
    global bullets, player
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        rad = deg_to_rad(player['angle'])
        bullets.append({
            'x': player['x'], 'y': player['y'],
            'dx': math.cos(rad) * 1.2, 
            'dy': math.sin(rad) * 1.2,
            'owner': 'player'
        })

# =============================================================================
# MEMBER 1: DRAWING
# =============================================================================
def draw_tank(x, y, angle, color, scale=1.0):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(scale, scale, scale)
    glRotatef(angle, 0, 0, 1)
    glColor3f(color[0], color[1], color[2])
    glutSolidCube(10) # Simple cube for now
    glPopMatrix()

def draw_arena_basic():
    # Simple grey floor so we aren't floating in void
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, -1)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, -1)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, -1)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, -1)
    glEnd()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Basic Camera (Member 3 will upgrade this)
    gluPerspective(60, W_WIDTH/W_HEIGHT, 0.1, 3000)
    gluLookAt(player['x'], player['y'] - 300, 300, player['x'], player['y'], 0, 0, 0, 1)
    
    draw_arena_basic()
    draw_tank(player['x'], player['y'], player['angle'], (0, 1, 0))
    
    for b in bullets:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], 5)
        glColor3f(1, 1, 0)
        glutSolidCube(2)
        glPopMatrix()
        
    glutSwapBuffers()

def idle():
    global frame_count
    frame_count += 1
    update_bullets()
    glutPostRedisplay()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(W_WIDTH, W_HEIGHT)
    glutCreateWindow(b"Tank Battle - Step 1")
    init_level(1)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
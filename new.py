 #code boass =     boss = None, line 1794


"""
SKY ASSAULT v3.0 — Full Feature Edition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5 NEW SYSTEMS added on top of v2.0:

  1. COMBO SYSTEM
     • Kill streak multiplier: 1× → 2× → 3× → 4× → 5× MAX
     • 3-second window between kills to maintain combo
     • Getting hit resets combo instantly
     • Large animated combo pop at centre-screen
     • Score is multiplied by current combo value

  2. POWER-UP SYSTEM (expanded)
     • Double Shot, Rapid Fire, Shield, Extra Life, Triple Shot, Laser
     • Distinct icon sprites + glowing pickup effect
     • Timed power-ups show countdown bar in HUD
     • "DOUBLE FIRE ACTIVATED" style notification on pickup

  3. FOUR ENEMY TYPES (now extended to 8 types)
     • Scout, Tank, Zigzag, Hunter + Bomber, Cloaked, Summoner, Bouncer

  4. EXPLOSION EFFECTS
     • Multi-wave particle bursts (debris + flash + sparks)
     • Screen shake scales with enemy size / type
     • Player hit: red flash overlay + shake
     • Spatial SFX panning (left/right by screen X)

  5. SCORE UI (full HUD redesign)
     • Score | Time | Lives — clean top bar
     • Combo multiplier near score with flash animation
     • Lives display with heart icons (3 lives system)
     • Red colour when lives = 1, critical flash when HP < 30
     • Power-up name notification toast on pickup

Controls: Arrow Keys / WASD | ESC = Quit | P = Pause
"""

import pygame
import random
import math
import sys
import numpy as np

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1500, 780
FPS        = 100
TITLE      = "SKY WASEEM v3.0"

BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
DARK_BG     = (4,   8,  20)
CYAN        = (0,   220, 255)
NEON_BLUE   = (60,  140, 255)
NEON_GREEN  = (0,   255, 120)
NEON_YELLOW = (255, 240,  40)
NEON_PINK   = (255,  50, 200)
NEON_ORANGE = (255, 140,  20)
RED         = (220,  40,  40)
DARK_RED    = (140,  20,  20)
GREY        = (120, 120, 140)
SHIELD_BLUE = (40,  160, 255)
GOLD        = (255, 215,   0)
PURPLE      = (180,  60, 255)

SAMPLE_RATE = 22050

# ─────────────────────────────────────────────
#  PROCEDURAL AUDIO
# ─────────────────────────────────────────────
def _make_sound(arr):
    arr = np.clip(arr, -32767, 32767).astype(np.int16)
    stereo = np.column_stack([arr, arr])
    return pygame.sndarray.make_sound(stereo)

def generate_laser_sfx():
    t    = np.linspace(0, 0.08, int(SAMPLE_RATE * 0.08))
    freq = np.linspace(1800, 800, len(t))
    wave = np.sin(2 * np.pi * freq * t)
    env  = np.exp(-t * 30)
    return _make_sound((wave * env * 18000).astype(np.float32))

def generate_explosion_sfx():
    t     = np.linspace(0, 0.45, int(SAMPLE_RATE * 0.45))
    noise = np.random.uniform(-1, 1, len(t))
    freq  = np.linspace(200, 40, len(t))
    tone  = np.sin(2 * np.pi * freq * t)
    wave  = noise * 0.7 + tone * 0.3
    env   = np.exp(-t * 7)
    return _make_sound((wave * env * 28000).astype(np.float32))

def generate_powerup_sfx():
    t    = np.linspace(0, 0.35, int(SAMPLE_RATE * 0.35))
    freq = np.linspace(500, 1600, len(t))
    wave = np.sin(2 * np.pi * freq * t) * 0.5 + np.sin(4 * np.pi * freq * t) * 0.5
    env  = np.exp(-t * 4)
    return _make_sound((wave * env * 22000).astype(np.float32))

def generate_combo_sfx():
    """Rising chime for combo increase."""
    t    = np.linspace(0, 0.2, int(SAMPLE_RATE * 0.2))
    freq = np.linspace(600, 1400, len(t))
    wave = np.sin(2 * np.pi * freq * t) * 0.6 + np.sin(3 * np.pi * freq * t) * 0.4
    env  = np.exp(-t * 12)
    return _make_sound((wave * env * 20000).astype(np.float32))

def generate_hit_sfx():
    """Thud for player getting hit."""
    t     = np.linspace(0, 0.18, int(SAMPLE_RATE * 0.18))
    noise = np.random.uniform(-1, 1, len(t))
    freq  = np.linspace(300, 80, len(t))
    tone  = np.sin(2 * np.pi * freq * t)
    wave  = noise * 0.5 + tone * 0.5
    env   = np.exp(-t * 15)
    return _make_sound((wave * env * 24000).astype(np.float32))

def generate_bgm():
    bar_len = int(SAMPLE_RATE * 0.5)
    total   = bar_len * 16
    t_full  = np.linspace(0, total / SAMPLE_RATE, total)
    wave    = np.zeros(total)
    bass_notes = [55, 55, 73.4, 82.4] * 4
    for i, freq in enumerate(bass_notes):
        s = i * bar_len; e = s + bar_len
        t = t_full[s:e] - t_full[s]
        wave[s:e] += np.sin(2 * np.pi * freq * t) * 0.4
    arp = [440, 554, 659, 880, 659, 554, 440, 330] * 8
    step = total // len(arp)
    for i, freq in enumerate(arp):
        s = i * step; e = min(s + step, total)
        t = t_full[s:e] - t_full[s]
        wave[s:e] += np.sin(2 * np.pi * freq * t) * 0.15
    for i in range(0, total, bar_len // 4):
        end = min(i + 800, total)
        wave[i:end] += np.random.uniform(-0.12, 0.12, end - i)
    fade = int(SAMPLE_RATE * 0.05)
    env  = np.ones(total)
    env[:fade]  = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    return _make_sound((wave * env * 22000).astype(np.float32))

# ─────────────────────────────────────────────
#  UTILITIES
# ─────────────────────────────────────────────
def lerp(a, b, t):
    return a + (b - a) * t

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def draw_glow(surface, colour, pos, radius, alpha=80):
    if radius < 2:
        return
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    r, g, b = colour
    for i in range(radius, 0, -3):
        a = int(alpha * (i / radius) ** 2)
        pygame.draw.circle(glow, (r, g, b, a), (radius, radius), i)
    surface.blit(glow, (pos[0] - radius, pos[1] - radius),
                 special_flags=pygame.BLEND_RGBA_ADD)

def draw_neon_rect(surface, colour, rect, width=2, glow_radius=8):
    draw_glow(surface, colour, rect.center, glow_radius + rect.width // 2, alpha=40)
    pygame.draw.rect(surface, colour, rect, width, border_radius=4)

def play_sfx(sound, volume=1.0, pan_x=None):
    """Play a sound; if pan_x given (0-SCREEN_W), pan left/right."""
    try:
        ch = sound.play()
        if ch:
            if pan_x is not None:
                pct = clamp(pan_x / SCREEN_W, 0, 1)
                ch.set_volume(volume * (1 - pct * 0.6), volume * (0.4 + pct * 0.6))
            else:
                ch.set_volume(volume)
    except Exception:
        pass

# ─────────────────────────────────────────────
#  ICON SPRITES
# ─────────────────────────────────────────────
def make_lightning_icon(size=28):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    pts = [(cx+4,2),(cx-2,cy-2),(cx+3,cy-2),(cx-6,size-2),(cx+2,cy+4),(cx-4,cy+4)]
    pygame.draw.polygon(surf, (255, 60, 60), pts)
    pygame.draw.polygon(surf, (255, 200, 200), pts, 1)
    return surf

def make_shield_icon(size=28):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    pts = [(cx,2),(size-3,6),(size-3,cy+4),(cx,size-2),(3,cy+4),(3,6)]
    pygame.draw.polygon(surf, (40, 140, 255, 200), pts)
    pygame.draw.polygon(surf, (160, 220, 255), pts, 2)
    pygame.draw.line(surf, (200, 230, 255, 180), (cx, 8), (cx, size-8), 2)
    pygame.draw.line(surf, (200, 230, 255, 180), (7, cy), (size-7, cy), 2)
    return surf

def make_health_icon(size=28):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    arm = size // 5
    pygame.draw.rect(surf, (40, 220, 100), (cx-arm, 4, arm*2, size-8), border_radius=3)
    pygame.draw.rect(surf, (40, 220, 100), (4, cy-arm, size-8, arm*2), border_radius=3)
    pygame.draw.rect(surf, (160, 255, 200), (cx-arm, 4, arm*2, size-8), 1, border_radius=3)
    pygame.draw.rect(surf, (160, 255, 200), (4, cy-arm, size-8, arm*2), 1, border_radius=3)
    return surf

def make_double_icon(size=28):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for ox in [-5, 5]:
        cx = size // 2 + ox
        pts = [(cx+3,2),(cx-2,size//2-2),(cx+2,size//2-2),(cx-4,size-2),(cx+1,size//2+3),(cx-3,size//2+3)]
        pygame.draw.polygon(surf, NEON_YELLOW, pts)
        pygame.draw.polygon(surf, WHITE, pts, 1)
    return surf

def make_life_icon(size=28):
    """Heart shape for extra life."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2 + 2
    # two circles + triangle approximation
    r = size // 5
    pygame.draw.circle(surf, RED, (cx - r, cy - r + 1), r)
    pygame.draw.circle(surf, RED, (cx + r, cy - r + 1), r)
    pts = [(cx - size//2 + 2, cy - 1), (cx + size//2 - 2, cy - 1), (cx, cy + size//3)]
    pygame.draw.polygon(surf, RED, pts)
    pygame.draw.circle(surf, (255, 120, 120), (cx - r, cy - r + 1), r, 1)
    pygame.draw.circle(surf, (255, 120, 120), (cx + r, cy - r + 1), r, 1)
    return surf

# ─────────────────────────────────────────────
#  POWER-UP DEFINITIONS
# ─────────────────────────────────────────────
POWERUP_TYPES = {
    "double": {
        "colour": NEON_YELLOW, "glow": 20, "duration": 600,
        "aura": NEON_YELLOW,   "desc": "DOUBLE SHOT ACTIVATED",
    },
    "rapid": {
        "colour": (255, 60, 60), "glow": 20, "duration": 600,
        "aura": (255, 80, 80),   "desc": "RAPID FIRE ACTIVATED",
    },
    "shield": {
        "colour": SHIELD_BLUE, "glow": 24, "duration": 480,
        "aura": SHIELD_BLUE,   "desc": "SHIELD ACTIVATED",
    },
    "health": {
        "colour": NEON_GREEN, "glow": 18, "duration": 0,
        "aura": NEON_GREEN,   "desc": "HEALTH RESTORED  +40",
    },
    "triple": {
        "colour": CYAN, "glow": 22, "duration": 600,
        "aura": CYAN,   "desc": "TRIPLE SHOT ACTIVATED",
    },
    "laser": {
        "colour": NEON_PINK, "glow": 22, "duration": 600,
        "aura": NEON_PINK,   "desc": "LASER BEAM ACTIVATED",
    },
    "life": {
        "colour": RED, "glow": 22, "duration": 0,
        "aura": RED,   "desc": "EXTRA LIFE  +1",
    },
    "timeslow": {
        "colour": (0, 200, 255), "glow": 20, "duration": 300,
        "aura": (0, 150, 200), "desc": "TIME SLOW ACTIVATED",
    },
    "homing": {
        "colour": (255, 100, 255), "glow": 20, "duration": 400,
        "aura": (200, 50, 200), "desc": "HOMING MISSILE ACTIVATED",
    },
    "magnet": {
        "colour": (255, 215, 0), "glow": 22, "duration": 350,
        "aura": (255, 200, 0), "desc": "MAGNET ACTIVATED",
    },
    "reflect": {
        "colour": (100, 200, 255), "glow": 24, "duration": 300,
        "aura": (80, 180, 255), "desc": "SHIELD REFLECT ACTIVATED",
    },



    "pet_drone": {
        "colour": (0, 200, 255), "glow": 18, "duration": 0,
        "aura": (0, 150, 200), "desc": "DRONE PET SUMMONED!",
    },
    "pet_robot": {
        "colour": (255, 200, 0), "glow": 18, "duration": 0,
        "aura": (200, 150, 0), "desc": "ROBOT PET SUMMONED!",
    },
    "pet_jet": {
        "colour": (255, 100, 255), "glow": 18, "duration": 0,
        "aura": (200, 50, 200), "desc": "MINI JET PET SUMMONED!",
    },


    # Special Weapons
    "nuke": {
        "colour": (255, 50, 50), "glow": 30, "duration": 0,
        "aura": (255, 0, 0), "desc": "💣 NUKE ACTIVATED! All enemies destroyed!",
    },
    "time_bomb": {
        "colour": (255, 200, 0), "glow": 25, "duration": 0,
        "aura": (255, 150, 0), "desc": "⏰ TIME BOMB DROPPED! 3 seconds!",
    },
    "lightning": {
        "colour": (0, 255, 255), "glow": 28, "duration": 0,
        "aura": (0, 200, 200), "desc": "⚡ LIGHTNING STORM! Chain lightning!",
    },


}

_ICON_MAKERS = {
    "double": make_double_icon,
    "rapid":  make_lightning_icon,
    "shield": make_shield_icon,
    "health": make_health_icon,
    "triple": make_lightning_icon,
    "laser":  make_lightning_icon,
    "life":   make_life_icon,
    "timeslow": make_lightning_icon,
    "homing": make_lightning_icon,
    "magnet": make_lightning_icon,
    "reflect": make_shield_icon,
    "pet_drone": make_lightning_icon,
    "pet_robot": make_shield_icon,
    "pet_jet": make_double_icon,   
    "pet_drone": make_lightning_icon,
    "pet_robot": make_shield_icon,
    "pet_jet": make_double_icon,
    "nuke": make_lightning_icon,
    "time_bomb": make_lightning_icon,
    "lightning": make_lightning_icon,

}
_ICON_CACHE = {}

def get_icon(kind, size=28):
    key = f"{kind}_{size}"
    if key not in _ICON_CACHE:
        _ICON_CACHE[key] = _ICON_MAKERS[kind](size)
    return _ICON_CACHE[key]

# ─────────────────────────────────────────────
#  COMBO SYSTEM
# ─────────────────────────────────────────────
class ComboSystem:
    MAX_COMBO    = 5
    WINDOW_SECS  = 3.0   # seconds between kills to keep combo alive
    WINDOW_FRAMES = int(WINDOW_SECS * 60)

    def __init__(self):
        self.multiplier  = 1
        self.timer       = 0     # frames since last kill
        self._pop        = 0.0   # visual pop animation
        self._flash      = 0     # frames of flash on increase

    def on_kill(self):
        """Call when an enemy is killed. Returns True if multiplier increased."""
        self.timer = 0
        increased  = False
        if self.multiplier < self.MAX_COMBO:
            self.multiplier += 1
            self._pop   = 1.0
            self._flash = 18
            increased   = True
        else:
            self._pop = 0.5
        return increased

    def on_hit(self):
        """Call when player takes damage — resets combo."""
        self.multiplier = 1
        self.timer      = 0
        self._pop       = 0.0

    def update(self):
        if self.multiplier > 1:
            self.timer += 1
            if self.timer >= self.WINDOW_FRAMES:
                self.multiplier = 1
                self.timer      = 0
        self._pop   = max(0.0, self._pop - 0.05)
        self._flash = max(0, self._flash - 1)

    @property
    def score_mult(self):
        return self.multiplier

    def draw(self, surface, font_lg, font_sm):
        if self.multiplier <= 1 and self._pop < 0.05:
            return
        # Centre-screen floating combo display
        scale = 1.0 + self._pop * 0.6
        colours = [WHITE, NEON_GREEN, NEON_YELLOW, NEON_ORANGE, RED, PURPLE]
        col = colours[min(self.multiplier - 1, len(colours) - 1)]
        if self._flash % 4 < 2 and self._flash > 0:
            col = WHITE
        text = f"{self.multiplier}× COMBO"
        base = font_lg.render(text, True, col)
        if scale > 1.01:
            w = int(base.get_width() * scale)
            h = int(base.get_height() * scale)
            base = pygame.transform.smoothscale(base, (w, h))
        rect = base.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 60))
        draw_glow(surface, col, rect.center, int(40 * scale), alpha=int(60 * self._pop))
        surface.blit(base, rect)

        # Combo decay bar (shows time left in window)
        if self.multiplier > 1:
            bar_w = 200
            bx    = SCREEN_W // 2 - bar_w // 2
            by    = rect.bottom + 6
            pct   = 1.0 - self.timer / self.WINDOW_FRAMES
            pygame.draw.rect(surface, (40, 40, 60), (bx, by, bar_w, 5), border_radius=3)
            if pct > 0:
                pygame.draw.rect(surface, col, (bx, by, int(bar_w * pct), 5), border_radius=3)

# ─────────────────────────────────────────────
#  PICKUP NOTIFICATION TOAST
# ─────────────────────────────────────────────
class Toast:
    def __init__(self):
        self.text   = ""
        self.colour = WHITE
        self.timer  = 0
        self.max_t  = 120

    def show(self, text, colour):
        self.text   = text
        self.colour = colour
        self.timer  = self.max_t

    def update(self):
        self.timer = max(0, self.timer - 1)

    def draw(self, surface, font):
        if self.timer <= 0:
            return
        alpha = min(1.0, self.timer / 30)
        col   = tuple(int(c * alpha) for c in self.colour)
        surf  = font.render(self.text, True, col)
        # Slide in from bottom
        y = SCREEN_H - 120 - int((1 - alpha) * 20)
        rect = surf.get_rect(center=(SCREEN_W // 2, y))
        draw_glow(surface, self.colour, rect.center, 60, alpha=int(50 * alpha))
        surface.blit(surf, rect)

# ─────────────────────────────────────────────
#  STAR FIELD
# ─────────────────────────────────────────────
class StarField:
    def __init__(self, count=130):
        self.stars = []
        for _ in range(count):
            x   = random.randint(0, SCREEN_W)
            y   = random.randint(0, SCREEN_H)
            spd = random.uniform(0.5, 3.5)
            r   = random.randint(1, 2) if spd < 2 else 1
            br  = int(clamp(spd / 3.5 * 200 + 55, 55, 255))
            self.stars.append([x, y, spd, r, br])

    def update(self):
        for s in self.stars:
            s[1] += s[2]
            if s[1] > SCREEN_H:
                s[1] = 0
                s[0] = random.randint(0, SCREEN_W)

    def draw(self, surface):
        for x, y, _, r, br in self.stars:
            col = (br, br, min(255, br + 40))
            pygame.draw.circle(surface, col, (int(x), int(y)), r)

# ─────────────────────────────────────────────
#  PARTICLE
# ─────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, colour, vx=None, vy=None,
                 life=None, radius=None, gravity=0.06):
        self.x       = x
        self.y       = y
        self.colour  = colour
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1, 5)
        self.vx      = vx if vx is not None else math.cos(angle) * speed
        self.vy      = vy if vy is not None else math.sin(angle) * speed
        self.life    = life   if life   is not None else random.randint(20, 45)
        self.max_life = self.life
        self.radius  = radius if radius is not None else random.uniform(2, 5)
        self.gravity = gravity

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += self.gravity
        self.vx *= 0.97
        self.life -= 1

    def draw(self, surface):
        alpha = self.life / self.max_life
        r, g, b = self.colour
        faded = (int(r * alpha), int(g * alpha), int(b * alpha))
        rad   = max(1, int(self.radius * alpha))
        pygame.draw.circle(surface, faded, (int(self.x), int(self.y)), rad)

    @property
    def alive(self):
        return self.life > 0

# ─────────────────────────────────────────────
#  BULLET
# ─────────────────────────────────────────────
class Bullet:
    PLAYER_SPEED = 18
    ENEMY_SPEED  = 5
    TRAIL_LENGTH = 7

    def __init__(self, x, y, angle=0, is_player=True,
                 colour=CYAN, speed=None, damage=1):
        self.x         = x
        self.y         = y
        self.is_player = is_player
        self.colour    = colour
        spd = speed if speed else (self.PLAYER_SPEED if is_player else self.ENEMY_SPEED)
        self.vx        = math.sin(angle) * spd
        self.vy        = -math.cos(angle) * spd
        self.damage    = damage
        self.trail     = []
        self.radius    = 4 if is_player else 3
        self.alive     = True

    def update(self):
        global game_speed_factor
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.TRAIL_LENGTH:
            self.trail.pop(0)
        self.x += self.vx * game_speed_factor
        self.y += self.vy * game_speed_factor
        if (self.x < -20 or self.x > SCREEN_W + 20 or
                self.y < -20 or self.y > SCREEN_H + 20):
            self.alive = False

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            frac  = (i + 1) / len(self.trail)
            rad   = max(1, int(self.radius * frac * 0.8))
            r, g, b = self.colour
            col = (min(255, int(r*frac)), min(255, int(g*frac)), min(255, int(b*frac)))
            draw_glow(surface, col, (int(tx), int(ty)), rad + 4, alpha=int(frac * 70))
            pygame.draw.circle(surface, col, (int(tx), int(ty)), rad)
        draw_glow(surface, self.colour, (int(self.x), int(self.y)), self.radius + 6, alpha=120)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, self.colour, (int(self.x), int(self.y)), self.radius - 1)

    def get_rect(self):
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

# ─────────────────────────────────────────────
#  POWER-UP
# ─────────────────────────────────────────────
class PowerUp:
    SPEED  = 1.8
    RADIUS = 16

    def __init__(self, x, y):
        self.x      = x
        self.y      = y
        self.kind   = random.choice(list(POWERUP_TYPES.keys()))
        info        = POWERUP_TYPES[self.kind]
        self.colour = info["colour"]
        self.glow_r = info["glow"]
        self.angle  = 0.0
        self.alive  = True

    def update(self):
        self.y += self.SPEED
        self.angle += 0.045
        if self.y > SCREEN_H + 40:
            self.alive = False

    def draw(self, surface, font):
        pulse = int(8 * abs(math.sin(self.angle * 2)))
        draw_glow(surface, self.colour, (int(self.x), int(self.y)),
                  self.glow_r + pulse, alpha=110)
        for i in range(8):
            a  = self.angle + i * math.pi / 4
            px = self.x + math.cos(a) * (self.RADIUS + 4)
            py = self.y + math.sin(a) * (self.RADIUS + 4)
            pygame.draw.circle(surface, self.colour, (int(px), int(py)), 2)
        pygame.draw.circle(surface, (10, 10, 30), (int(self.x), int(self.y)), self.RADIUS)
        pygame.draw.circle(surface, self.colour, (int(self.x), int(self.y)), self.RADIUS, 2)
        icon = get_icon(self.kind, 24)
        surface.blit(icon, icon.get_rect(center=(int(self.x), int(self.y))))

    def get_rect(self):
        r = self.RADIUS
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

# ─────────────────────────────────────────────
#  ENEMY — 8 TYPES
# ─────────────────────────────────────────────
class Enemy:
    DROP_CHANCE = 0.30

    PROFILES = {
        "scout":    ((80,  200, 255), (3.5, 5.5), (1, 2),  (120, 180), 15, 16),
        "tank":     ((180,  30,  30), (1.0, 1.8), (5, 9),  (60,  90),  30, 28),
        "zigzag":   ((200, 100, 255), (2.0, 3.2), (2, 3),  (110, 160), 20, 20),
        "hunter":   ((255, 180,  20), (1.8, 2.8), (3, 5),  (80,  130), 25, 22),
        "bomber":   ((139, 69, 19),  (0.8, 1.2), (5, 8),   (60,  90),  40, 28),
        "cloaked":  ((120, 120, 120), (1.5, 2.5), (2, 4),  (70, 110), 25, 22),
        "summoner": ((100, 40, 120), (0.8, 1.2), (8, 12),  (120, 180), 50, 30),
        "bouncer":  ((255, 100, 50), (1.8, 2.5), (3, 6),   (90, 130), 25, 24),
    }

    def __init__(self, score=0, kind=None):
        difficulty = min(score / 500, 3.0)
        if kind is None:
            # All enemy types can spawn
            self.kind = random.choice(list(self.PROFILES.keys()))
        else:
            self.kind = kind

        col, spd_r, hp_r, sh_r, pts, rad = self.PROFILES[self.kind]
        self.colour      = col
        self.wing_colour = tuple(max(0, c - 60) for c in col)
        self.x           = random.randint(50, SCREEN_W - 50)
        self.y           = -40
        self.base_speed  = random.uniform(*spd_r) + difficulty * 0.3
        self.speed       = self.base_speed
        self.radius      = rad
        self.max_hp      = random.randint(*hp_r) + int(difficulty * 0.5)
        self.hp          = self.max_hp
        self.points      = pts
        self.alive       = True
        self.shoot_cd    = random.randint(*sh_r)
        self.shoot_timer = random.randint(0, self.shoot_cd)
        self.angle       = 0.0
        self.wave_offset = random.uniform(0, math.tau)
        self.vx          = random.uniform(-0.5, 0.5)  # for scout drift

        # Special variables for new enemy types
        if self.kind == "bomber":
            self.bomb_timer = 0
            self.bomb_interval = 30
        elif self.kind == "cloaked":
            self.visible = False
            self.visible_timer = random.randint(30, 90)
            self.invisible_duration = random.randint(60, 120)
            self.attack_duration = 45
        elif self.kind == "summoner":
            self.summon_timer = 0
            self.summon_interval = 90
        elif self.kind == "bouncer":
            self.vx = random.choice([-2, -1.5, 1.5, 2])
            self.vy = random.uniform(1, 2)

    def update(self, player_x=None):
        global game_speed_factor
        self.angle += 0.04
        self.shoot_timer += 1

        if self.kind == "scout":
            self.x += math.sin(self.angle * 2 + self.wave_offset) * 1.5 + self.vx
            self.y += self.speed * game_speed_factor
        elif self.kind == "tank":
            self.y += self.speed * game_speed_factor
        elif self.kind == "zigzag":
            self.x += math.sin(self.angle * 1.5 + self.wave_offset) * 4
            self.y += self.speed * game_speed_factor
        elif self.kind == "hunter":
            if player_x is not None:
                dx = player_x - self.x
                self.x += clamp(dx * 0.018, -2.5, 2.5)
            self.y += self.speed * game_speed_factor
        elif self.kind == "bomber":
            self.y += self.speed * game_speed_factor
            self.bomb_timer += 1
            if self.bomb_timer >= self.bomb_interval:
                self.bomb_timer = 0
                # Bomb would be created here (requires bomb list, not implemented yet)
        elif self.kind == "cloaked":
            self.y += self.speed * game_speed_factor
            self.visible_timer -= 1
            if self.visible_timer <= 0:
                self.visible = not self.visible
                if self.visible:
                    self.visible_timer = self.attack_duration
                else:
                    self.visible_timer = self.invisible_duration
        elif self.kind == "summoner":
            self.y += self.speed * game_speed_factor
            self.summon_timer += 1
            if self.summon_timer >= self.summon_interval:
                self.summon_timer = 0
                # Minion spawning would be handled in main loop, we'll just create an enemy
                # but we can't directly access enemies list here, so we'll rely on a separate system.
                # For now, we skip actual summoning to avoid complexity.
                pass
        elif self.kind == "bouncer":
            self.x += self.vx * game_speed_factor
            self.y += self.vy * game_speed_factor
            if self.x <= 20 or self.x >= SCREEN_W - 20:
                self.vx = -self.vx
            if self.y <= 20 or self.y >= SCREEN_H - 60:
                self.vy = -self.vy

        self.x = clamp(self.x, 20, SCREEN_W - 20)
        if self.y > SCREEN_H + 50:
            self.alive = False

    def can_shoot(self):
        if self.shoot_timer >= self.shoot_cd:
            self.shoot_timer = 0
            return True
        return False

    def get_bullets(self):
        bullets = []
        if self.kind == "tank":
            for a in (-0.18, 0, 0.18):
                bullets.append(Bullet(self.x, self.y + self.radius,
                                      angle=math.pi + a,
                                      is_player=False, colour=NEON_ORANGE, damage=12))
        else:
            angle = math.atan2(SCREEN_W // 2 - self.x, SCREEN_H - self.y) * 0.15
            bullets.append(Bullet(self.x, self.y + self.radius,
                                  angle=math.pi + angle,
                                  is_player=False, colour=self.colour, damage=8))
        return bullets

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface):
        # For cloaked enemies: don't draw when invisible
        if self.kind == "cloaked" and not self.visible:
            return

        ix = int(self.x)
        iy = int(self.y)
        r  = self.radius
        wobble = int(math.sin(self.angle) * 2)

        draw_glow(surface, self.colour, (ix, iy), r + 10, alpha=50)

        wing_pts_l = [(ix - r - 10, iy + wobble), (ix - r + 4, iy - 8), (ix - 4, iy + 4)]
        wing_pts_r = [(ix + r + 10, iy + wobble), (ix + r - 4, iy - 8), (ix + 4, iy + 4)]
        pygame.draw.polygon(surface, self.wing_colour, wing_pts_l)
        pygame.draw.polygon(surface, self.wing_colour, wing_pts_r)

        body_surf = pygame.Surface((r * 2, r * 3), pygame.SRCALPHA)
        pygame.draw.ellipse(body_surf, (*self.colour, 220), (0, 0, r * 2, r * 3))
        pygame.draw.ellipse(body_surf, WHITE, (0, 0, r * 2, r * 3), 1)
        surface.blit(body_surf, (ix - r, iy - int(r * 1.5)))

        # Cockpit colour by type
        ck_colours = {"scout": (100,230,255), "tank": (255,100,100),
                      "zigzag": (220,130,255), "hunter": (255,220,80),
                      "bomber": (255,140,0), "cloaked": (150,150,150),
                      "summoner": (200,80,200), "bouncer": (255,180,80)}
        pygame.draw.ellipse(surface, ck_colours.get(self.kind, (200,200,200)),
                            (ix - 5, iy - 8, 10, 14))

        # HP bar
        bar_w = r * 2
        pygame.draw.rect(surface, DARK_RED, (ix - r, iy + r + 5, bar_w, 4))
        fill_w = int(bar_w * self.hp / self.max_hp)
        hcol   = (80,220,80) if self.hp/self.max_hp > 0.5 else \
                 (220,200,20) if self.hp/self.max_hp > 0.25 else RED
        pygame.draw.rect(surface, hcol, (ix - r, iy + r + 5, fill_w, 4))

    def get_rect(self):
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)








# ─────────────────────────────────────────────
#  BOSS CLASS - Big Monster
# ─────────────────────────────────────────────
class Boss:
    def __init__(self, score):
        self.x = SCREEN_W // 2
        self.y = -80
        self.width = 80
        self.height = 80
        self.max_hp = 500
        self.hp = self.max_hp
        self.alive = True
        self.angle = 0
        self.shoot_timer = 0
        self.spawn_timer = 0
        self.phase = 1
        
        # Colors
        self.color = (180, 50, 50)
        self.eye_color = (255, 50, 50)
        
        # Movement
        self.speed_x = 2
        self.direction = 1
        
        # Attack patterns
        self.pattern = 0
        self.pattern_timer = 0
        
    def update(self, player_x, player_y):
        self.angle += 0.03
        self.shoot_timer += 1
        self.spawn_timer += 1
        self.pattern_timer += 1
        
        # Boss movement (left-right)
        self.x += self.speed_x * self.direction
        if self.x <= 100 or self.x >= SCREEN_W - 100:
            self.direction *= -1
        
        # Phase change based on HP
        if self.hp < self.max_hp // 2:
            self.phase = 2
            self.color = (200, 100, 50)
        if self.hp < self.max_hp // 4:
            self.phase = 3
            self.color = (220, 150, 50)
            self.speed_x = 3
        
        # Move down slowly
        if self.y < 100:
            self.y += 1
        
        # Change attack pattern every 2 seconds
        if self.pattern_timer > 120:
            self.pattern_timer = 0
            self.pattern = (self.pattern + 1) % 4
        
        return self.get_bullets()
    
    def get_bullets(self):
        bullets = []
        
        if self.shoot_timer > 20:
            self.shoot_timer = 0
            
            if self.pattern == 0:  # Spread shot
                for angle_offset in [-0.5, -0.3, -0.1, 0.1, 0.3, 0.5]:
                    bullets.append(Bullet(self.x, self.y + 40, 
                                         angle=math.pi/2 + angle_offset,
                                         is_player=False, colour=RED, damage=15))
            
            elif self.pattern == 1:  # Triple shot
                for angle_offset in [-0.3, 0, 0.3]:
                    bullets.append(Bullet(self.x, self.y + 40,
                                         angle=math.pi/2 + angle_offset,
                                         is_player=False, colour=NEON_ORANGE, damage=20))
            
            elif self.pattern == 2:  # Circle burst
                for i in range(8):
                    angle = i * math.pi * 2 / 8 + self.angle
                    bullets.append(Bullet(self.x, self.y + 20,
                                         angle=angle,
                                         is_player=False, colour=NEON_PINK, damage=12))
            
            elif self.pattern == 3:  # Homing missiles (phase 3)
                if self.phase >= 2:
                    for i in range(3):
                        bullet = Bullet(self.x - 20 + i*20, self.y + 40,
                                       angle=math.pi/2 + random.uniform(-0.2, 0.2),
                                       is_player=False, colour=GOLD, damage=18)
                        bullets.append(bullet)
        
        return bullets
    
    def spawn_minions(self, enemies, score):
        """Spawn small enemies every 3 seconds"""
        if self.spawn_timer > 180:  # Every 3 seconds
            self.spawn_timer = 0
            if self.phase >= 2:  # Phase 2 and 3 spawn minions
                for i in range(random.randint(1, 3)):
                    minion = Enemy(score, kind=random.choice(["scout", "zigzag"]))
                    minion.x = self.x + random.randint(-50, 50)
                    minion.y = self.y + 50
                    enemies.append(minion)
    
    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False
            return True
        return False
    
    def draw(self, surface):
        ix = int(self.x)
        iy = int(self.y)
        
        # Boss glow
        draw_glow(surface, self.color, (ix, iy), 60, alpha=80)
        
        # === BOSS BODY ===
        # Main body (big oval)
        body_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.ellipse(body_surf, self.color, (0, 0, self.width, self.height))
        pygame.draw.ellipse(body_surf, (255, 100, 100), (0, 0, self.width, self.height), 3)
        surface.blit(body_surf, (ix - self.width//2, iy - self.height//2))
        
        # === WINGS ===
        # Left wing
        wing_l_pts = [(ix - 40, iy - 10), (ix - 80, iy - 30), (ix - 70, iy + 10), (ix - 40, iy + 20)]
        pygame.draw.polygon(surface, (100, 40, 40), wing_l_pts)
        pygame.draw.polygon(surface, (200, 80, 80), wing_l_pts, 2)
        
        # Right wing
        wing_r_pts = [(ix + 40, iy - 10), (ix + 80, iy - 30), (ix + 70, iy + 10), (ix + 40, iy + 20)]
        pygame.draw.polygon(surface, (100, 40, 40), wing_r_pts)
        pygame.draw.polygon(surface, (200, 80, 80), wing_r_pts, 2)
        
        # === EYES ===
        # Left eye
        pygame.draw.circle(surface, self.eye_color, (ix - 20, iy - 10), 10)
        pygame.draw.circle(surface, WHITE, (ix - 20, iy - 10), 5)
        pygame.draw.circle(surface, BLACK, (ix - 22, iy - 12), 3)
        
        # Right eye
        pygame.draw.circle(surface, self.eye_color, (ix + 20, iy - 10), 10)
        pygame.draw.circle(surface, WHITE, (ix + 20, iy - 10), 5)
        pygame.draw.circle(surface, BLACK, (ix + 18, iy - 12), 3)
        
        # === MOUTH ===
        mouth_pts = [(ix - 25, iy + 15), (ix, iy + 30), (ix + 25, iy + 15)]
        pygame.draw.polygon(surface, (100, 30, 30), mouth_pts)
        pygame.draw.polygon(surface, (255, 50, 50), mouth_pts, 2)
        
        # === HORNS ===
        horn_l = [(ix - 35, iy - 35), (ix - 45, iy - 60), (ix - 25, iy - 40)]
        pygame.draw.polygon(surface, (80, 30, 30), horn_l)
        
        horn_r = [(ix + 35, iy - 35), (ix + 45, iy - 60), (ix + 25, iy - 40)]
        pygame.draw.polygon(surface, (80, 30, 30), horn_r)
        
        # === ARMOR PLATES ===
        for offset in [-15, 0, 15]:
            pygame.draw.line(surface, (200, 80, 80), (ix + offset, iy + 10), (ix + offset, iy + 30), 3)
        
        # === PHASE INDICATOR ===
        phase_text = pygame.font.Font(None, 24).render(f"PHASE {self.phase}", True, WHITE)
        surface.blit(phase_text, (ix - 30, iy - 55))
        
        # === BOSS HP BAR ===
        bar_w = 300
        bar_x = SCREEN_W // 2 - bar_w // 2
        bar_y = 30
        
        # Background
        pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_w, 15), border_radius=5)
        # Health fill
        fill_w = int(bar_w * self.hp / self.max_hp)
        
        if self.hp / self.max_hp > 0.6:
            hcol = NEON_GREEN
        elif self.hp / self.max_hp > 0.3:
            hcol = NEON_YELLOW
        else:
            hcol = RED
        
        pygame.draw.rect(surface, hcol, (bar_x, bar_y, fill_w, 15), border_radius=5)
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, 15), 2, border_radius=5)
        
        # Boss name
        boss_name = pygame.font.Font(None, 28).render("DRAGON LORD", True, RED)
        surface.blit(boss_name, (SCREEN_W // 2 - 70, bar_y - 25))
        
        # Health text
        hp_text = pygame.font.Font(None, 20).render(f"{int(self.hp)}/{int(self.max_hp)}", True, WHITE)
        surface.blit(hp_text, (SCREEN_W // 2 - 30, bar_y + 18))
        
        # Pulse effect when low health
        if self.hp < self.max_hp // 4:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            draw_glow(surface, RED, (ix, iy), 70 + int(pulse * 20), alpha=60)
    
    def get_rect(self):
        return pygame.Rect(self.x - 40, self.y - 40, self.width, self.height)










# ─────────────────────────────────────────────
#  PET SYSTEM - Companion Drone
# ─────────────────────────────────────────────
class Pet:
    def __init__(self, pet_type="drone"):
        self.type = pet_type  # "drone", "robot", "mini_jet"
        self.x = SCREEN_W // 2
        self.y = SCREEN_H - 80
        self.angle = 0
        self.alive = True
        self.shoot_timer = 0
        self.shoot_delay = 15  # frames between shots
        
        # Pet properties based on type
        if self.type == "drone":
            self.color = (0, 200, 255)
            self.size = 12
            self.damage = 5
            self.speed = 3
        elif self.type == "robot":
            self.color = (255, 200, 0)
            self.size = 14
            self.damage = 8
            self.speed = 2
        else:  # mini_jet
            self.color = (255, 100, 255)
            self.size = 10
            self.damage = 6
            self.speed = 4
    
    def update(self, player_x, player_y):
        # Pet follows the player
        self.x = player_x
        self.y = player_y - 35  # sits above player
        
        # Pet orbit movement (slight circle)
        self.angle += 0.05
        self.x += math.sin(self.angle) * 8
        
        # Shooting timer
        self.shoot_timer += 1
    
    def shoot(self):
        if self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = 0
            bullet = Bullet(self.x, self.y - 5, angle=0, is_player=True,
                           colour=self.color, damage=self.damage)
            return bullet
        return None
    
    def draw(self, surface):
        ix = int(self.x)
        iy = int(self.y)
        
        if self.type == "drone":
            # Drone - Quadcopter style
            # Body
            pygame.draw.circle(surface, self.color, (ix, iy), self.size)
            pygame.draw.circle(surface, WHITE, (ix, iy), self.size - 2, 1)
            # Rotors
            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle + self.angle * 20)
                rx = ix + int(14 * math.cos(rad))
                ry = iy + int(14 * math.sin(rad))
                pygame.draw.line(surface, self.color, (ix, iy), (rx, ry), 2)
                pygame.draw.circle(surface, (150, 150, 150), (rx, ry), 3)
            # Eye
            pygame.draw.circle(surface, (0, 100, 255), (ix - 3, iy - 2), 2)
            pygame.draw.circle(surface, (0, 100, 255), (ix + 3, iy - 2), 2)
            
        elif self.type == "robot":
            # Robot - Small cute robot
            # Head
            pygame.draw.rect(surface, self.color, (ix - 7, iy - 8, 14, 14), border_radius=3)
            pygame.draw.rect(surface, WHITE, (ix - 7, iy - 8, 14, 14), 1, border_radius=3)
            # Eyes
            pygame.draw.circle(surface, (0, 255, 0), (ix - 3, iy - 4), 2)
            pygame.draw.circle(surface, (0, 255, 0), (ix + 3, iy - 4), 2)
            # Antenna
            pygame.draw.line(surface, self.color, (ix, iy - 9), (ix, iy - 14), 2)
            pygame.draw.circle(surface, (255, 50, 50), (ix, iy - 14), 2)
            # Body
            pygame.draw.rect(surface, self.color, (ix - 5, iy + 1, 10, 8), border_radius=2)
            
        else:  # mini_jet
            # Mini Jet Fighter
            body_pts = [
                (ix, iy - 8), (ix + 8, iy - 2), (ix + 10, iy + 2),
                (ix + 6, iy + 4), (ix, iy + 6), (ix - 6, iy + 4),
                (ix - 10, iy + 2), (ix - 8, iy - 2)
            ]
            pygame.draw.polygon(surface, self.color, body_pts)
            pygame.draw.polygon(surface, WHITE, body_pts, 1)
            # Cockpit
            pygame.draw.circle(surface, CYAN, (ix, iy - 2), 2)
            # Trail
            pygame.draw.line(surface, NEON_ORANGE, (ix, iy + 5), (ix, iy + 9), 2)
        
        # Pet glow effect
        draw_glow(surface, self.color, (ix, iy), self.size + 4, alpha=30)

    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size, 
                          self.size * 2, self.size * 2)






# ─────────────────────────────────────────────
#  PET SUMMON ICON - Appears every minute
# ─────────────────────────────────────────────
class PetSummonIcon:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.alive = True
        self.angle = 0
        self.pulse = 0
        
    def update(self):
        self.y += 1.5
        self.angle += 0.05
        self.pulse = abs(math.sin(self.angle * 2)) * 10
        if self.y > SCREEN_H + 50:
            self.alive = False
            
    def draw(self, surface):
        ix = int(self.x)
        iy = int(self.y)
        draw_glow(surface, GOLD, (ix, iy), 30 + int(self.pulse), alpha=80)
        points = []
        for i in range(5):
            angle = i * 72 - 90 + self.angle * 50
            px = ix + math.cos(math.radians(angle)) * 18
            py = iy + math.sin(math.radians(angle)) * 18
            points.append((px, py))
            angle2 = angle + 36
            px2 = ix + math.cos(math.radians(angle2)) * 8
            py2 = iy + math.sin(math.radians(angle2)) * 8
            points.append((px2, py2))
        pygame.draw.polygon(surface, GOLD, points)
        pygame.draw.polygon(surface, NEON_YELLOW, points, 2)
        font_small = pygame.font.Font(None, 24)
        text = font_small.render("P", True, WHITE)
        surface.blit(text, text.get_rect(center=(ix, iy)))
        
    def get_rect(self):
        return pygame.Rect(self.x - 20, self.y - 20, 40, 40)




# ─────────────────────────────────────────────
#  PLAYER
# ─────────────────────────────────────────────
class Player:
    MAX_HP    = 100
    MAX_LIVES = 3
    SPEED     = 5.5
    ACCEL     = 0.18
    DECEL     = 0.88
    RADIUS    = 20
    FIRE_RATE = 5

    def __init__(self, lives=3):
        self.x      = SCREEN_W // 2
        self.y      = SCREEN_H - 100
        self.vx     = 0.0
        self.vy     = 0.0
        self.hp     = self.MAX_HP
        self.lives  = lives
        self.alive  = True
        self.fire_timer     = 0
        self.invincible     = 0
        self.power_kind     = None
        self.power_timer    = 0
        self.power_duration = 1
        self.trail          = []
        self.TRAIL_LEN      = 18
        self.angle          = 0.0
        self._aura_pulse    = 0.0
        self._hit_flash     = 0
        self.time_slow_active = False
        self.slow_timer = 0
        self.pet = None
        self.pet_type = None 
        self.nuke_count = 0
        self.time_bomb_count = 0
        self.lightning_count = 0
        self.time_bomb_active = None
        self.time_bomb_timer = 0
        # Special weapons
        self.nuke_count = 0
        self.time_bomb_count = 0
        self.lightning_count = 0
        self.time_bomb_active = None
        self.time_bomb_timer = 0



    def respawn(self):
        self.x          = SCREEN_W // 2
        self.y          = SCREEN_H - 100
        self.vx         = 0.0
        self.vy         = 0.0
        self.hp         = self.MAX_HP
        self.alive      = True
        self.invincible = 120   # 2 sec grace
        self.trail      = []
        self.power_kind = None
        self.pet = None
        self.pet_type = None
    def update(self, keys):
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1
        if dx and dy:
            dx *= 0.707; dy *= 0.707
        self.vx = lerp(self.vx, dx * self.SPEED, self.ACCEL)
        self.vy = lerp(self.vy, dy * self.SPEED, self.ACCEL)
        if not dx: self.vx *= self.DECEL
        if not dy: self.vy *= self.DECEL
        self.x = clamp(self.x + self.vx, self.RADIUS, SCREEN_W - self.RADIUS)
        self.y = clamp(self.y + self.vy, self.RADIUS, SCREEN_H - self.RADIUS)
        target_angle = self.vx * 0.04
        self.angle   = lerp(self.angle, target_angle, 0.1)
        self.trail.append((self.x, self.y + self.RADIUS + 4))
        if len(self.trail) > self.TRAIL_LEN:
            self.trail.pop(0)
        self.fire_timer  = max(0, self.fire_timer - 1)
        self.invincible  = max(0, self.invincible - 1)
        self._hit_flash  = max(0, self._hit_flash - 1)
        self._aura_pulse = (self._aura_pulse + 0.12) % math.tau

        if self.time_slow_active:
            self.slow_timer -= 1
            if self.slow_timer <= 0:
                self.time_slow_active = False

        if self.power_kind:
            self.power_timer -= 1
            if self.power_kind == "shield":
                self.invincible = max(self.invincible, 2)
            if self.power_timer <= 0:
                self.power_kind  = None
                self.power_timer = 0
                # Update pet
        if self.pet:
            self.pet.update(self.x, self.y) 

        # Time bomb update
        if self.time_bomb_active:
            self.time_bomb_active["timer"] -= 1
            if self.time_bomb_active["timer"] <= 0:
                self.time_bomb_active = None


    def get_fire_rate(self):
        if self.power_kind == "rapid":  return 2
        if self.power_kind == "laser":  return 3
        return self.FIRE_RATE

    def shoot(self):
        if self.fire_timer > 0:
            return []
        self.fire_timer = self.get_fire_rate()
        cx = self.x
        cy = self.y - self.RADIUS
        bullets = []
        if self.power_kind == "triple":
            for a in (-0.22, 0, 0.22):
                bullets.append(Bullet(cx, cy, angle=a, is_player=True, colour=CYAN, damage=1))
        elif self.power_kind == "double":
            for ox in (-8, 8):
                bullets.append(Bullet(cx + ox, cy, angle=0, is_player=True,
                                      colour=NEON_YELLOW, damage=1))
        elif self.power_kind == "laser":
            bullets.append(Bullet(cx, cy, angle=0, is_player=True, colour=NEON_PINK,
                                  speed=Bullet.PLAYER_SPEED * 1.3, damage=3))
        elif self.power_kind == "rapid":
            bullets.append(Bullet(cx, cy, angle=0, is_player=True, colour=(255,80,80), damage=1))
        else:
            bullets.append(Bullet(cx, cy, angle=0, is_player=True, colour=CYAN, damage=1))
        
        
        
        
                # Pet shooting (if pet exists)
        if self.pet:
            pet_bullet = self.pet.shoot()
            if pet_bullet:
                bullets.append(pet_bullet)
               # play_sfx(sfx_laser, 0.15)
        
        
        return bullets
    def collect_power(self, kind):
        info = POWERUP_TYPES[kind]
        if kind == "health":
            self.hp = min(self.MAX_HP, self.hp + 40)
        elif kind == "life":
            self.lives = min(self.MAX_LIVES + 2, self.lives + 1)
        elif kind == "shield":
            self.power_kind = kind
            self.power_duration = info["duration"]
            self.power_timer = info["duration"]
        elif kind == "timeslow":
            self.time_slow_active = True
            self.slow_timer = info["duration"]
        elif kind == "pet_drone":
            self.summon_pet("drone")
        elif kind == "pet_robot":
            self.summon_pet("robot")
        elif kind == "pet_jet":
            self.summon_pet("mini_jet")
        # Special Weapons
        elif kind == "nuke":
            self.nuke_count += 1
        elif kind == "time_bomb":
            self.time_bomb_count += 1
        elif kind == "lightning":
            self.lightning_count += 1
        else:
            self.power_kind = kind
            self.power_duration = info["duration"]
            self.power_timer = info["duration"]
        


    def use_nuke(self, enemies):
        """Destroy all enemies on screen"""
        if self.nuke_count > 0:
            self.nuke_count -= 1
            for enemy in enemies[:]:
                enemy.alive = False
            return True
        return False
    
    def use_time_bomb(self, enemies, x, y):
        """Drop a time bomb that explodes after 3 seconds"""
        if self.time_bomb_count > 0:
            self.time_bomb_count -= 1
            self.time_bomb_active = {"x": x, "y": y, "timer": 3 * FPS}  # 3 seconds
            return True
        return False
    
    def use_lightning(self, enemies):
        """Chain lightning damages all enemies"""
        if self.lightning_count > 0:
            self.lightning_count -= 1
            damage = 30
            for enemy in enemies[:]:
                enemy.take_damage(damage)
            return True
        return False



    def summon_pet(self, pet_type="drone"):
        """Summon a pet companion"""
        self.pet = Pet(pet_type)
        self.pet_type = pet_type



    # 👇 یہ method یہاں ڈالیں
    def take_damage(self, dmg, combo=None):
        if self.invincible:
            return False
        self.hp -= dmg
        self.invincible = 45
        self._hit_flash = 20
        if combo:
            combo.on_hit()
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True
        return False

    def draw(self, surface):
        ix = int(self.x)
        iy = int(self.y)
        
        # Power-up aura
        if self.power_kind:
            aura_col = POWERUP_TYPES[self.power_kind]["aura"]
            aura_r = int(35 + math.sin(self._aura_pulse) * 5)
            draw_glow(surface, aura_col, (ix, iy), aura_r, alpha=90)
            if self.power_kind == "shield":
                ss = pygame.Surface((aura_r*2+10, aura_r*2+10), pygame.SRCALPHA)
                pa = int(120 + 60 * math.sin(self._aura_pulse))
                pygame.draw.circle(ss, (*SHIELD_BLUE, pa), (aura_r+5, aura_r+5), aura_r, 3)
                surface.blit(ss, (ix - aura_r - 5, iy - aura_r - 5))
        
        # FIGHTER JET BODY
        fuselage_pts = [
            (ix, iy - 35), (ix + 16, iy - 16), (ix + 22, iy - 2),
            (ix + 26, iy + 16), (ix + 14, iy + 14), (ix + 8, iy + 10),
            (ix, iy + 26), (ix - 8, iy + 10), (ix - 14, iy + 14),
            (ix - 26, iy + 16), (ix - 22, iy - 2), (ix - 16, iy - 16)
        ]
        pygame.draw.polygon(surface, (25, 55, 150), fuselage_pts)
        pygame.draw.polygon(surface, (60, 120, 220), fuselage_pts, 2)
        
        # Cockpit
        cockpit_pts = [(ix, iy - 35), (ix + 12, iy - 14), (ix - 12, iy - 14)]
        pygame.draw.polygon(surface, (80, 200, 255), cockpit_pts)
        pygame.draw.polygon(surface, (180, 230, 255), cockpit_pts, 2)
        
        # Right wing
        wing_r_main = [(ix + 12, iy - 4), (ix + 34, iy + 14), (ix + 18, iy + 18), (ix + 8, iy + 6)]
        pygame.draw.polygon(surface, (35, 75, 190), wing_r_main)
        
        # Left wing
        wing_l_main = [(ix - 12, iy - 4), (ix - 34, iy + 14), (ix - 18, iy + 18), (ix - 8, iy + 6)]
        pygame.draw.polygon(surface, (35, 75, 190), wing_l_main)
        
        # Afterburner flame
        flame_len = 10 + int(abs(self.vx) * 3)
        flame_pts = [(ix, iy + 24), (ix - 4, iy + 24 + flame_len), (ix + 4, iy + 24 + flame_len)]
        pygame.draw.polygon(surface, (255, 80, 0), flame_pts)
        pygame.draw.polygon(surface, (255, 200, 50), [(ix, iy + 24), (ix - 2, iy + 20 + flame_len//2), (ix + 2, iy + 20 + flame_len//2)])
        
        # Engine trail
        for i, (tx, ty) in enumerate(self.trail[-8:]):
            alpha = int((i / 8) * 100)
            rad = max(2, 6 - i)
            col = (255, 100 + i * 20, 0)
            draw_glow(surface, col, (int(tx), int(ty)), rad, alpha=alpha)
            pygame.draw.circle(surface, col, (int(tx), int(ty)), rad)
        
        # Invincibility flicker
        if self.invincible and self.power_kind != "shield" and self.invincible % 6 < 3:
            pygame.draw.circle(surface, WHITE, (ix, iy), 35, 3)
        
        # Hit flash
        if self._hit_flash > 0:
            alpha = int(self._hit_flash / 20 * 100)
            flash_surf = pygame.Surface((70, 70), pygame.SRCALPHA)
            flash_surf.fill((255, 0, 0, alpha))
            surface.blit(flash_surf, (ix - 35, iy - 35))

        # Draw pet
        if self.pet:
            self.pet.draw(surface)
        
        # Draw special weapons count (on bottom left)
        font_small = pygame.font.Font(None, 24)
        y_offset = SCREEN_H - 80
        
        if hasattr(self, 'nuke_count') and self.nuke_count > 0:
            pygame.draw.circle(surface, (255, 50, 50), (30, y_offset), 15)
            text = font_small.render(f"x{self.nuke_count}", True, WHITE)
            surface.blit(text, (45, y_offset - 8))
            y_offset += 30
        
        if hasattr(self, 'time_bomb_count') and self.time_bomb_count > 0:
            pygame.draw.circle(surface, (255, 200, 0), (30, y_offset), 15)
            text = font_small.render(f"x{self.time_bomb_count}", True, WHITE)
            surface.blit(text, (45, y_offset - 8))
            y_offset += 30
        
        if hasattr(self, 'lightning_count') and self.lightning_count > 0:
            pygame.draw.circle(surface, (0, 255, 255), (30, y_offset), 15)
            text = font_small.render(f"x{self.lightning_count}", True, WHITE)
            surface.blit(text, (45, y_offset - 8))
             
    





    
    
    def get_rect(self):
        r = self.RADIUS - 6
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    @property
    def power_pct(self):
        if not self.power_kind:
            return 0
        return self.power_timer / self.power_duration

















# ─────────────────────────────────────────────
#  HUD v3 — Score | Time | Lives + Combo
# ─────────────────────────────────────────────
class HUD:
    def __init__(self, font_lg, font_md, font_sm):
        self.font_lg = font_lg
        self.font_md = font_md
        self.font_sm = font_sm
        self._score_prev = 0
        self._score_pop  = 0.0

    def notify_score(self, score):
        if score != self._score_prev:
            self._score_pop  = 1.0
            self._score_prev = score

    def draw(self, surface, player, score, elapsed_secs, high_score, combo):
        self._score_pop = max(0.0, self._score_pop - 0.06)

        # Top bar background strip
        bar_surf = pygame.Surface((SCREEN_W, 85), pygame.SRCALPHA)
        bar_surf.fill((0, 0, 20, 160))
        surface.blit(bar_surf, (0, 0))

        # LEFT: Health bar
        lbl = self.font_sm.render("HEALTH", True, GREY)
        surface.blit(lbl, (14, 8))
        bar_w = 150
        crit  = player.hp < 30 and (pygame.time.get_ticks() // 200) % 2 == 0
        pygame.draw.rect(surface, (40, 40, 60), (14, 24, bar_w, 12), border_radius=6)
        fill  = int(bar_w * player.hp / Player.MAX_HP)
        hcol  = RED if crit else (NEON_GREEN if player.hp > 60 else
                                  NEON_YELLOW if player.hp > 30 else RED)
        if fill > 0:
            pygame.draw.rect(surface, hcol, (14, 24, fill, 12), border_radius=6)
        draw_neon_rect(surface, GREY, pygame.Rect(14, 24, bar_w, 12), width=1, glow_radius=3)
        hp_txt = self.font_sm.render(f"{player.hp}", True, WHITE)
        surface.blit(hp_txt, (14 + bar_w + 6, 24))

        # LEFT: Lives hearts
        lives_lbl = self.font_sm.render("LIVES", True, GREY)
        surface.blit(lives_lbl, (14, 44))
        heart = get_icon("life", 16)
        for i in range(player.lives):
            surface.blit(heart, (50 + i * 22, 42))

        # LEFT: Power-up bar
        if player.power_kind:
            info   = POWERUP_TYPES[player.power_kind]
            colour = info["colour"]
            icon   = get_icon(player.power_kind, 18)
            surface.blit(icon, (14, 64))
            desc_txt = self.font_sm.render(info["desc"].split()[0], True, colour)
            surface.blit(desc_txt, (36, 65))
            secs_left = math.ceil(player.power_timer / FPS)
            if info["duration"] > 0:
                stxt = self.font_sm.render(f"{secs_left}s", True, WHITE)
                surface.blit(stxt, (36 + desc_txt.get_width() + 6, 65))
            pygame.draw.rect(surface, (40,40,60), (14, 78, 150, 6), border_radius=3)
            pw = int(150 * player.power_pct)
            if pw > 0:
                pygame.draw.rect(surface, colour, (14, 78, pw, 6), border_radius=3)

        # CENTRE: Timer
        mins = elapsed_secs // 60
        secs = elapsed_secs % 60
        t_surf = self.font_lg.render(f"{mins:02d}:{secs:02d}", True, CYAN)
        t_rect = t_surf.get_rect(centerx=SCREEN_W // 2, y=8)
        draw_glow(surface, CYAN, t_rect.center, 40, alpha=40)
        surface.blit(t_surf, t_rect)

        # CENTRE: Combo multiplier
        if combo.multiplier > 1:
            cols = [WHITE, NEON_GREEN, NEON_YELLOW, NEON_ORANGE, RED, PURPLE]
            cc   = cols[min(combo.multiplier-1, len(cols)-1)]
            ct   = self.font_md.render(f"× {combo.multiplier}  COMBO", True, cc)
            surface.blit(ct, ct.get_rect(centerx=SCREEN_W//2, y=44))

        # RIGHT: Score (pop animation)
        pop_scale = 1.0 + self._score_pop * 0.4
        base_surf = self.font_lg.render(f"{score:06d}", True, NEON_YELLOW)
        if pop_scale > 1.01:
            w = int(base_surf.get_width()  * pop_scale)
            h = int(base_surf.get_height() * pop_scale)
            sc_surf = pygame.transform.smoothscale(base_surf, (w, h))
        else:
            sc_surf = base_surf
        sc_rect = sc_surf.get_rect(right=SCREEN_W - 14, y=8)
        draw_glow(surface, NEON_YELLOW, sc_rect.center, 50, alpha=40)
        surface.blit(sc_surf, sc_rect)

        hi_label = self.font_sm.render(f"BEST {high_score:06d}", True, GREY)
        surface.blit(hi_label, hi_label.get_rect(right=SCREEN_W - 14, y=46))

# ─────────────────────────────────────────────
#  SCREEN SHAKE
# ─────────────────────────────────────────────
class ScreenShake:
    def __init__(self):
        self.frames    = 0
        self.intensity = 0

    def trigger(self, intensity=8, frames=10):
        if intensity > self.intensity:
            self.intensity = intensity
            self.frames    = frames

    def get_offset(self):
        if self.frames > 0:
            self.frames -= 1
            ox = random.randint(-self.intensity, self.intensity)
            oy = random.randint(-self.intensity // 2, self.intensity // 2)
            return ox, oy
        return 0, 0

# ─────────────────────────────────────────────
#  EXPLOSION HELPER (multi-wave)
# ─────────────────────────────────────────────
def create_explosion(x, y, particles, colour, scale=1.0):
    count = int(30 * scale)
    for _ in range(count):
        r, g, b = colour
        col = (clamp(r + random.randint(-40,40),0,255),
               clamp(g + random.randint(-40,40),0,255),
               clamp(b + random.randint(-40,40),0,255))
        particles.append(Particle(x, y, col,
                                  radius=random.uniform(2, 5*scale)))
    # White flash
    for _ in range(int(10 * scale)):
        particles.append(Particle(x, y, WHITE,
                                  life=random.randint(5,14),
                                  radius=random.uniform(3, 8*scale), gravity=0))
    # Orange shards
    for _ in range(int(14 * scale)):
        angle = random.uniform(0, math.tau)
        spd   = random.uniform(3, 9 * scale)
        particles.append(Particle(x, y, NEON_ORANGE,
                                  vx=math.cos(angle)*spd, vy=math.sin(angle)*spd,
                                  life=random.randint(15,35),
                                  radius=random.uniform(1,3), gravity=0.12))

# ─────────────────────────────────────────────
#  SCREENS
# ─────────────────────────────────────────────
def draw_title_screen(surface, font_xl, font_lg, font_sm, stars, frame):
    stars.update()
    stars.draw(surface)
    pulse = abs(math.sin(frame * 0.04))
    draw_glow(surface, CYAN, (SCREEN_W//2, 170), int(80+pulse*30), alpha=int(50+pulse*40))
    title = font_xl.render("SKY ASSAULT", True, CYAN)
    surface.blit(title, title.get_rect(center=(SCREEN_W//2, 170)))
    sub = font_lg.render("v3.0  |  FULL FEATURE EDITION", True, NEON_YELLOW)
    surface.blit(sub, sub.get_rect(center=(SCREEN_W//2, 228)))

    lines = [
        ("MOVE",   "Arrow Keys / WASD"),
        ("FIRE",   "Auto-fires"),
        ("PAUSE",  "P key"),
        ("SCOUT",  "Blue — fast & agile        ×15 pts"),
        ("TANK",   "Red  — armoured, spread fire ×30 pts"),
        ("ZIGZAG", "Purple — hard sine movement  ×20 pts"),
        ("HUNTER", "Gold — tracks you sideways  ×25 pts"),
        ("COMBO",  "Kill streak = score multiplier up to 5×"),
        ("LIVES",  "3 lives — collect hearts to gain more"),
    ]
    y0 = 278
    for key, val in lines:
        k = font_sm.render(key + ":", True, NEON_GREEN)
        v = font_sm.render(val, True, WHITE)
        surface.blit(k, (140, y0))
        surface.blit(v, (270, y0))
        y0 += 24

    blink = int(frame * 0.06) % 2 == 0
    if blink:
        start = font_lg.render("PRESS SPACE TO LAUNCH", True, CYAN)
        surface.blit(start, start.get_rect(center=(SCREEN_W//2, 510)))

    credit = font_sm.render("SKY ASSAULT v3.0  •  Pygame Production", True, GREY)
    surface.blit(credit, credit.get_rect(center=(SCREEN_W//2, SCREEN_H - 16)))

def draw_game_over(surface, font_xl, font_lg, font_sm, score, high_score, stars, frame):
    stars.update()
    stars.draw(surface)
    draw_glow(surface, RED, (SCREEN_W//2, 180), 100, alpha=60)
    go = font_xl.render("GAME OVER", True, RED)
    surface.blit(go, go.get_rect(center=(SCREEN_W//2, 180)))
    sc = font_lg.render(f"SCORE: {score:06d}", True, NEON_YELLOW)
    surface.blit(sc, sc.get_rect(center=(SCREEN_W//2, 270)))
    hi = font_lg.render(f"BEST:  {high_score:06d}", True, CYAN)
    surface.blit(hi, hi.get_rect(center=(SCREEN_W//2, 318)))
    if score >= high_score:
        new = font_sm.render("★  NEW HIGH SCORE!  ★", True, NEON_GREEN)
        surface.blit(new, new.get_rect(center=(SCREEN_W//2, 362)))
    blink = int(frame * 0.06) % 2 == 0
    if blink:
        restart = font_lg.render("PRESS SPACE TO RETRY", True, CYAN)
        surface.blit(restart, restart.get_rect(center=(SCREEN_W//2, 450)))

def draw_pause_screen(surface, font_xl, font_lg):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    surface.blit(overlay, (0, 0))
    draw_glow(surface, CYAN, (SCREEN_W//2, SCREEN_H//2), 80, alpha=50)
    p = font_xl.render("PAUSED", True, CYAN)
    surface.blit(p, p.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 20)))
    r = font_lg.render("Press P to resume", True, WHITE)
    surface.blit(r, r.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 40)))

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    global game_speed_factor
    pygame.init()
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
    pygame.mixer.init(SAMPLE_RATE, -16, 2, 512)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    try:
        font_xl = pygame.font.Font(None, 72)
        font_lg = pygame.font.Font(None, 40)
        font_md = pygame.font.Font(None, 30)
        font_sm = pygame.font.Font(None, 22)
    except Exception:
        font_xl = font_lg = font_md = font_sm = pygame.font.SysFont("monospace", 24)

    print("Generating audio…")
    sfx_laser   = generate_laser_sfx()
    sfx_boom    = generate_explosion_sfx()
    sfx_powerup = generate_powerup_sfx()
    sfx_combo   = generate_combo_sfx()
    sfx_hit     = generate_hit_sfx()
    bgm_sound   = generate_bgm()
    print("Audio ready.")

    sfx_laser.set_volume(0.30)
    sfx_boom.set_volume(0.60)
    sfx_powerup.set_volume(0.80)
    sfx_combo.set_volume(0.70)
    sfx_hit.set_volume(0.80)
    bgm_sound.set_volume(0.26)

    hud        = HUD(font_lg, font_md, font_sm)
    stars      = StarField(140)
    shake      = ScreenShake()
    combo      = ComboSystem()
    toast      = Toast()
    high_score = 0

    state      = "title"
    paused     = False
    frame      = 0

    player      = None
    enemies     = []
    bullets     = []
    powerups    = []
    particles   = []
    score       = 0
    enemy_timer = 0
    enemy_spawn_interval = 90
    elapsed_secs = 0
    sec_timer    = 0
    bgm_channel  = None
    respawn_timer = 0

    game_surf = pygame.Surface((SCREEN_W, SCREEN_H))
    game_speed_factor = 1.0

    # Boss variables
    boss = None
    boss_spawn_timer = 0
    boss_spawn_interval = 180 * FPS  # 3 minutes at 80 FPS
    pet_summon_timer = 0
    pet_summon_interval = 60 * FPS  # 60 seconds
    pet_summon_icon = None


    def reset_game():
        nonlocal player, enemies, bullets, powerups, particles
        nonlocal score, enemy_timer, enemy_spawn_interval
        nonlocal elapsed_secs, sec_timer, respawn_timer
        player    = Player(lives=3)
        enemies   = []
        bullets   = []
        powerups  = []
        particles = []
        score     = 0
        enemy_timer = 0
        enemy_spawn_interval = 90
        elapsed_secs = 0
        sec_timer    = 0
        respawn_timer = 0
        combo.multiplier = 1
        combo.timer      = 0
        pet_summon_timer = 0
        pet_summon_icon = None
        boss = None
        boss_spawn_timer = 0

    running = True
    while running:
        clock.tick(FPS)
        frame += 1

        keys_pressed = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_p and state == "playing":
                    paused = not paused
                if event.key == pygame.K_SPACE:
                    if state == "title":
                        reset_game()
                        state = "playing"
                        bgm_channel = bgm_sound.play(loops=-1)
                    elif state == "gameover":
                        reset_game()
                        state = "playing"
                        bgm_channel = bgm_sound.play(loops=-1)

                # Special Weapons Keys
                if event.key == pygame.K_1:  # Nuke
                    if player and player.nuke_count > 0:
                        player.use_nuke(enemies)
                        toast.show("💥 NUKE DETONATED! All enemies destroyed!", RED)
                        play_sfx(sfx_boom, 1.0)
                
                if event.key == pygame.K_2:  # Time Bomb
                    if player and player.time_bomb_count > 0:
                        player.use_time_bomb(enemies, player.x, player.y)
                        toast.show("⏰ TIME BOMB DROPPED! Get away!", NEON_YELLOW)
                        play_sfx(sfx_powerup, 0.8)
                
                if event.key == pygame.K_3:  # Lightning
                    if player and player.lightning_count > 0:
                        player.use_lightning(enemies)
                        toast.show("⚡ LIGHTNING STORM! Chain lightning!", CYAN)
                        play_sfx(sfx_laser, 0.9)


        # Time Slow effect – update game speed factor

        if state == "playing" and not paused and player and player.alive:
            if player.time_slow_active:
                game_speed_factor = 0.5
            else:
                game_speed_factor = 1.0
        else:
            game_speed_factor = 1.0

        game_surf.fill(DARK_BG)

        if state == "title":
            draw_title_screen(game_surf, font_xl, font_lg, font_sm, stars, frame)
        elif state == "playing":
            if paused:   # PAUSE SCREEN
                stars.draw(game_surf)
                for e in enemies: 
                    e.draw(game_surf)
                for p in powerups:
                    p.draw(game_surf, font_sm)
                for b in bullets: 
                    b.draw(game_surf)
                for p in particles: 
                    p.draw(game_surf)
                if player and player.alive:
                    player.draw(game_surf)
                hud.draw(game_surf, player, score, elapsed_secs, high_score, combo)
                draw_pause_screen(game_surf, font_xl, font_lg)
            
            else:   # GAME RUNNING
                stars.update()
                stars.draw(game_surf)

                # Respawn logic
                if not player.alive:
                    respawn_timer -= 1
                    if respawn_timer <= 0 and player.lives > 0:
                        player.lives -= 1
                        player.respawn()
                        combo.on_hit()
                    elif player.lives <= 0:
                        if score > high_score:
                            high_score = score
                        state = "gameover"
                        pygame.mixer.stop()
                        bgm_channel = None
                        boss = None

                # Player update
                if player.alive:
                    player.update(keys_pressed)
                    new_bullets = player.shoot()
                    if new_bullets:
                        bullets.extend(new_bullets)
                        play_sfx(sfx_laser, 0.28)

                # Enemy spawning
                enemy_timer += 1
                enemy_spawn_interval = max(30, 90 - score // 60)
                if enemy_timer >= enemy_spawn_interval:
                    enemy_timer = 0
                    enemies.append(Enemy(score))


                # Boss spawn every 3 minutes
                if not boss and player.alive:                    
                    boss_spawn_timer += 1
                    print(f"Boss timer: {boss_spawn_timer} / {boss_spawn_interval}")  # test

                    if boss_spawn_timer >= boss_spawn_interval:
                        boss_spawn_timer = 0
                        boss = Boss(score)
                        toast.show("⚠️ DRAGON LORD APPEARS! ⚠️", RED)
                        play_sfx(sfx_boom, 1.0)


                # Update enemies
                for enemy in enemies:
                    enemy.update(player_x=player.x if player.alive else None)
                    if enemy.can_shoot():
                        for b in enemy.get_bullets():
                            bullets.append(b)
                # Update boss
                if boss is not None and boss.alive:
                    boss_bullets = boss.update(player.x, player.y)
                    if boss_bullets:
                        bullets.extend(boss_bullets)
                    boss.spawn_minions(enemies, score)


                # Update bullets, powerups, particles
                for b in bullets:   
                    b.update()
                for p in powerups:  
                    p.update()
                for p in particles: 
                    p.update()

                # Boss collision
                if boss is not None and boss.alive:
                    for b in bullets[:]:
                        if b.is_player and b.alive:
                            if boss.get_rect().colliderect(b.get_rect()):
                                pass
                                killed = boss.take_damage(b.damage)
                                b.alive = False
                                if killed:
                                    for _ in range(5):
                                        powerups.append(PowerUp(boss.x + random.randint(-30, 30), 
                                                                boss.y + random.randint(-30, 30)))
                                    score += 2000
                                    toast.show("🎉 BOSS DEFEATED! +2000 POINTS! 🎉", GOLD)
                                    play_sfx(sfx_boom, 1.5)
                                    create_explosion(boss.x, boss.y, particles, NEON_ORANGE, 3.0)
                                    boss = None


                         # Boss collision
#                if boss is not None and boss.alive:
#                    for b in bullets[:]:
 #                       if b.is_player and b.alive:
  #                          if boss.get_rect().colliderect(b.get_rect()):
   #                             pass
    #                            killed = boss.take_damage(b.damage)
     #                           b.alive = False
      #                          if killed:
       #                             for _ in range(5):
        #                                powerups.append(PowerUp(boss.x + random.randint(-30, 30), 
         #                                                       boss.y + random.randint(-30, 30)))
          #                          score += 2000
           #                         toast.show("🎉 BOSS DEFEATED! +2000 POINTS! 🎉", GOLD)
            #                        play_sfx(sfx_boom, 1.5)
             #                       create_explosion(boss.x, boss.y, particles, NEON_ORANGE, 3.0)
              #                      boss = None


                # Time bomb explosion
                if player and player.time_bomb_active and player.time_bomb_active["timer"] <= 0:
                    bx = player.time_bomb_active["x"]
                    by = player.time_bomb_active["y"]
                    # Destroy enemies in radius
                    for enemy in enemies[:]:
                        dx = enemy.x - bx
                        dy = enemy.y - by
                        dist = math.hypot(dx, dy)
                        if dist < 100:
                            enemy.alive = False
                            create_explosion(enemy.x, enemy.y, particles, enemy.colour, 1.2)
                    # Big explosion effect
                    create_explosion(bx, by, particles, NEON_ORANGE, 2.0)
                    shake.trigger(intensity=12, frames=15)
                    play_sfx(sfx_boom, 1.2)
                    player.time_bomb_active = None

                # Combo update
                combo.update()
                toast.update()

                # Collisions: player bullets -> enemies
                for enemy in enemies[:]:
                    for b in bullets[:]:
                        if b.is_player and b.alive and enemy.alive:
                            if enemy.get_rect().colliderect(b.get_rect()):
                                killed = enemy.take_damage(b.damage)
                                b.alive = False
                                if killed:
                                    pts = enemy.points * combo.score_mult
                                    score += pts
                                    hud.notify_score(score)
                                    scale = enemy.radius / 20
                                    create_explosion(enemy.x, enemy.y, particles,
                                                     enemy.colour, scale=scale)
                                    shake.trigger(intensity=int(5*scale), frames=int(7*scale))
                                    play_sfx(sfx_boom, 0.60, pan_x=enemy.x)
                                    increased = combo.on_kill()
                                    if increased:
                                        play_sfx(sfx_combo, 0.65)
                                    if random.random() < Enemy.DROP_CHANCE:
                                        powerups.append(PowerUp(enemy.x, enemy.y))





               # Boss collision
                if boss is not None and boss.alive:
                    for b in bullets[:]:
                        if b.is_player and b.alive:
                            if boss.get_rect().colliderect(b.get_rect()):
                                killed = boss.take_damage(b.damage)
                                b.alive = False
                                if killed:
                                    for _ in range(5):
                                        powerups.append(PowerUp(boss.x + random.randint(-30, 30), 
                                                                boss.y + random.randint(-30, 30)))
                                    score += 2000
                                    toast.show("🎉 BOSS DEFEATED! +2000 POINTS! 🎉", GOLD)
                                    play_sfx(sfx_boom, 1.5)
                                    create_explosion(boss.x, boss.y, particles, NEON_ORANGE, 3.0)
                                    boss = None







                # Collisions: enemy bullets -> player
                if player.alive:
                    for b in bullets[:]:
                        if not b.is_player and b.alive:
                            if player.get_rect().colliderect(b.get_rect()):
                                died = player.take_damage(8, combo)
                                b.alive = False
                                shake.trigger(intensity=4, frames=6)
                                play_sfx(sfx_hit, 0.75)
                                if died:
                                    create_explosion(player.x, player.y, particles, CYAN, 1.5)
                                    respawn_timer = 90

                # Collisions: enemies -> player
                if player.alive:
                    for enemy in enemies[:]:
                        if enemy.alive:
                            if player.get_rect().colliderect(enemy.get_rect()):
                                died = player.take_damage(25, combo)
                                enemy.alive = False
                                create_explosion(enemy.x, enemy.y, particles,
                                                 enemy.colour, scale=1.2)
                                shake.trigger(intensity=10, frames=14)
                                play_sfx(sfx_boom, 0.70, pan_x=enemy.x)
                                if died:
                                    create_explosion(player.x, player.y, particles, CYAN, 1.5)
                                    respawn_timer = 90

                # Collisions: player -> power-ups
                if player.alive:
                    for p in powerups[:]:
                        if p.alive and player.get_rect().inflate(20,20).colliderect(p.get_rect()):
                            player.collect_power(p.kind)
                            p.alive = False
                            play_sfx(sfx_powerup, 0.80)
                            for _ in range(16):
                                particles.append(Particle(p.x, p.y, p.colour,
                                                          life=random.randint(18,32),
                                                          radius=random.uniform(2,4)))
                            toast.show(POWERUP_TYPES[p.kind]["desc"],
                                       POWERUP_TYPES[p.kind]["colour"])

                # Collision with pet summon icon
                if pet_summon_icon and player.alive:
                    if player.get_rect().colliderect(pet_summon_icon.get_rect()):
                        pet_type = random.choice(["drone", "robot", "mini_jet"])
                        player.summon_pet(pet_type)
                        pet_summon_icon.alive = False
                        pet_summon_icon = None
                        toast.show(f"🎮 PET SUMMONED! {pet_type.upper()} JOINED!", GOLD)
                        play_sfx(sfx_powerup, 0.9)

                # Pet Summon Icon Timer
                pet_summon_timer += 1
                if pet_summon_timer >= pet_summon_interval:
                    pet_summon_timer = 0
                    if pet_summon_icon is None and player.alive:
                        pet_summon_icon = PetSummonIcon(random.randint(50, SCREEN_W - 50), -40)

                # Update pet summon icon
                if pet_summon_icon:
                    pet_summon_icon.update()
                    if not pet_summon_icon.alive:
                        pet_summon_icon = None

                # Cleanup
                bullets   = [b for b in bullets   if b.alive]
                enemies   = [e for e in enemies   if e.alive]
                powerups  = [p for p in powerups  if p.alive]
                particles = [p for p in particles if p.alive]

                # Timer + passive score
                sec_timer += 1
                if sec_timer >= FPS:
                    sec_timer = 0
                    elapsed_secs += 1
                    score += 1
                    hud.notify_score(score)

                # ==========================================
                # DRAWING SECTION
                # ==========================================
                for e in enemies:
                    e.draw(game_surf)
                for p in powerups:
                    p.draw(game_surf, font_sm)

                # Draw boss
                if boss and boss.alive:
                    boss.draw(game_surf)


                # Draw time bomb
                if player and player.time_bomb_active:
                    bx = int(player.time_bomb_active["x"])
                    by = int(player.time_bomb_active["y"])
                    timer_left = player.time_bomb_active["timer"] // FPS + 1
                    
                    # Draw bomb
                    pygame.draw.circle(game_surf, (50, 50, 50), (bx, by), 15)
                    pygame.draw.circle(game_surf, (255, 100, 0), (bx, by), 12)
                    pygame.draw.circle(game_surf, (255, 0, 0), (bx, by), 8)
                    
                    # Timer text
                    font_big = pygame.font.Font(None, 36)
                    text = font_big.render(str(timer_left), True, WHITE)
                    game_surf.blit(text, text.get_rect(center=(bx, by)))
                    
                    # Draw warning circle
                    draw_glow(game_surf, RED, (bx, by), 60, alpha=100)


                # Draw pet summon icon (GAME RUNNING)
                if pet_summon_icon:
                    pet_summon_icon.draw(game_surf)
                
                for b in bullets:
                    b.draw(game_surf)
                for p in particles:
                    p.draw(game_surf)
                if player.alive:
                    player.draw(game_surf)

                # Red hit flash
                if player._hit_flash > 0:
                    alpha = int(player._hit_flash / 20 * 80)
                    flash_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    flash_surf.fill((220, 30, 30, alpha))
                    game_surf.blit(flash_surf, (0, 0))

                hud.draw(game_surf, player, score, elapsed_secs, high_score, combo)
                combo.draw(game_surf, font_lg, font_sm)
                toast.draw(game_surf, font_md)

        elif state == "gameover":
            draw_game_over(game_surf, font_xl, font_lg, font_sm,
                           score, high_score, stars, frame)

        ox, oy = shake.get_offset()
        screen.fill(DARK_BG)
        screen.blit(game_surf, (ox, oy))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
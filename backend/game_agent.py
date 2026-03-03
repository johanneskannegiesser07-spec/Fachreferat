import random
import math

class GameSession:
    def __init__(self):
        # Constants
        self.WIDTH = 800
        self.HEIGHT = 600
        self.GRAVITY = 0.2
        self.THRUST_POWER = 0.5
        self.ROTATE_SPEED = 5
        self.FRICTION = 0.99
        self.ALIEN_SPEED = 2
        self.BULLET_SPEED = 7
        self.WIN_SCORE = 10
        
        # Game State
        self.rocket = {
            "x": 400,
            "y": 300,
            "vx": 0,
            "vy": 0,
            "angle": 20,
            "width": 20,
            "height": 30,
            "dead": False
        }
        self.aliens = []
        self.bullets = []
        self.platform = None
        self.score = 0
        self.game_over = False
        self.game_won = False
        
        # Input State
        self.inputs = {
            "UP": False,
            "LEFT": False,
            "RIGHT": False,
            "SPACE": False
        }
        
        self.spawn_timer = 0
        self.shoot_cooldown = 0

    def apply_input(self, key, is_pressed):
        if key in self.inputs:
            self.inputs[key] = is_pressed
            
    def reset(self):
        self.__init__()

    def update(self):
        if self.game_over or self.game_won:
            return

        # --- Rocket Physics ---
        # Gravity
        self.rocket["vy"] += self.GRAVITY

        # Thrust (Upwards)
        if self.inputs["UP"]:
            self.rocket["vy"] -= self.THRUST_POWER
            
        # Horizontal Movement
        if self.inputs["LEFT"]:
            self.rocket["vx"] -= self.THRUST_POWER
        if self.inputs["RIGHT"]:
            self.rocket["vx"] += self.THRUST_POWER
            
        # Lock angle to 0 for this control scheme
        self.rocket["angle"] = 0
            
        # Apply velocity & Friction
        self.rocket["vx"] *= self.FRICTION
        self.rocket["vy"] *= self.FRICTION
        self.rocket["x"] += self.rocket["vx"]
        self.rocket["y"] += self.rocket["vy"]
        
        # Screen Check (Rocket)
        if self.rocket["x"] < 0: self.rocket["x"] = 0; self.rocket["vx"] *= -0.5
        if self.rocket["x"] > self.WIDTH: self.rocket["x"] = self.WIDTH; self.rocket["vx"] *= -0.5
        if self.rocket["y"] < 0: self.rocket["y"] = 0; self.rocket["vy"] *= -0.5
        if self.rocket["y"] > self.HEIGHT: 
            self.rocket["dead"] = True
            self.game_over = True

        # --- Bullets ---
        if self.inputs["SPACE"] and self.shoot_cooldown <= 0:
            rad = math.radians(self.rocket["angle"])
            self.bullets.append({
                "x": self.rocket["x"],
                "y": self.rocket["y"],
                "vx": math.sin(rad) * self.BULLET_SPEED,
                "vy": -math.cos(rad) * self.BULLET_SPEED
            })
            self.shoot_cooldown = 15 # frames
            
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        for b in self.bullets[:]:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            if not (0 <= b["x"] <= self.WIDTH and 0 <= b["y"] <= self.HEIGHT):
                self.bullets.remove(b)

        # --- Aliens ---
        self.spawn_timer += 1
        if self.spawn_timer > 60: # Spawn every ~2 seconds
            self.spawn_timer = 0
            self.aliens.append({
                "x": random.randint(50, self.WIDTH - 50),
                "y": -30,
                "width": 30,
                "height": 30
            })
            
        for a in self.aliens[:]:
            a["y"] += self.ALIEN_SPEED
            if a["y"] > self.HEIGHT:
                self.aliens.remove(a)
                
            # Alien vs Rocket Collision (Simple AABB)
            # Rocket treated as a box for simplicity
            rx, ry, rw, rh = self.rocket["x"], self.rocket["y"], self.rocket["width"], self.rocket["height"]
            ax, ay, aw, ah = a["x"], a["y"], a["width"], a["height"]
            
            if (abs(rx - ax) * 2 < (rw + aw)) and (abs(ry - ay) * 2 < (rh + ah)):
                 self.game_over = True
                 self.rocket["dead"] = True

        # Bullet vs Alien
        for b in self.bullets[:]:
            hit = False
            for a in self.aliens[:]:
                if (b["x"] > a["x"] - a["width"]/2 and b["x"] < a["x"] + a["width"]/2 and
                    b["y"] > a["y"] - a["height"]/2 and b["y"] < a["y"] + a["height"]/2):
                    self.aliens.remove(a)
                    self.bullets.remove(b)
                    self.score += 1
                    hit = True
                    break
            if hit: break

        # --- Rescue Platform ---
        if self.score >= self.WIN_SCORE:
            if not self.platform:
                self.platform = {
                    "x": self.WIDTH + 100,
                    "y": self.HEIGHT - 50,
                    "width": 100,
                    "height": 20,
                    "target_x": self.WIDTH / 2
                }
            
            # Move platform in
            if self.platform["x"] > self.platform["target_x"]:
                self.platform["x"] -= 2
                
            # Check Landing
            # Must be within platform bounds, low speed, and contacting top
            px, py, pw, ph = self.platform["x"], self.platform["y"], self.platform["width"], self.platform["height"]
            rx, ry = self.rocket["x"], self.rocket["y"]
            
            if (abs(rx - px) * 2 < pw) and (abs(ry - (py - ph/2 - self.rocket["height"]/2)) < 10):
                 if abs(self.rocket["vy"]) < 4 and abs(self.rocket["vx"]) < 4:
                     self.game_won = True
                     self.rocket["vx"] = 0
                     self.rocket["vy"] = 0
                 else:
                     self.game_over = True # Crashed
                     self.rocket["dead"] = True

    def get_state(self):
        return {
            "rocket": self.rocket,
            "aliens": self.aliens,
            "bullets": self.bullets,
            "platform": self.platform,
            "score": self.score,
            "game_over": self.game_over,
            "game_won": self.game_won
        }

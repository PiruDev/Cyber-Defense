"""Simulação da arena: regras e estado sem Pygame."""

from math import cos, hypot, isfinite, pi, sin
from random import Random

from .combat import (
    DAMAGE_COOLDOWN,
    apply_damage, apply_enemy_hit, in_cone, in_thrust, touching,
)
from .archer import Archer
from .balance import (BalanceConfig, WEAPON_CONFIGS, LONGBOW_MAX_HITS, SPEAR_PICKUP_RADIUS,
                      SPEAR_SPIN_DURATION, SPEAR_SPIN_REACH, SPEAR_RETURN_DURATION)
from .boss import Rootkit
from .cards import apply_card
from .weapon_cards import WeaponCard, offer_level_cards
from .auto_combat import nearest_target
from .returning_spear import ReturningSpear
from .drops import collect_drop, roll_drop
from .effects import EffectSystem
from .enemies import Drop, Enemy
from .feel_config import LEVEL_UP_PUSH_DISTANCE, LEVEL_UP_PUSH_DURATION, ease_out_cubic
from .levelup import LevelUpState
from .modes import GameMode
from .physics import SeparationSystem
from .player import Player
from .progression import Progressao
from .projectiles import Projectile
from .swordsman import Swordsman
from .waves import WaveManager
from .weapons import TrainingTarget, WeaponSystem, AttackPulse, WEAPON_CHOICES, LAB_WEAPON_CHOICES
from .worm import Worm
from .camera import Camera
from .visual_config import WORLD_ARENA, ARENA_VIEWPORT


class GameWorld:
    def __init__(self, arena=WORLD_ARENA, rng=None, mode="defense", config=None, *, auto_attack=True):
        self.arena = tuple(arena)
        self.rng = rng if rng is not None else Random()
        self.config = config if config is not None else BalanceConfig()
        self.mode = GameMode(mode)
        self.auto_attack = auto_attack
        self.restart()

    def restart(self, mode=None) -> None:
        selected_mode = self.mode if mode is None else GameMode(mode)
        if hasattr(self, "effects"):
            self.effects.reset()
        else:
            self.effects = EffectSystem()
        left, top, width, height = self.arena
        self.player = Player(x=left + width / 2, y=top + height / 2)
        self.player_moving = False
        self.camera = Camera(self.arena)
        self.camera.update(self.player.x, self.player.y, 0, snap=True)
        self.player.overclock_multiplier = self.config.overclock_multiplier
        self.player.progression = Progressao(automatic_bonuses=False, max_level=36)
        self.mode = selected_mode
        self.phase = "waves"
        self.weapons = WeaponSystem()
        self.enemies = []
        self.enemy_motion = {}
        self.drops = []
        self.projectiles = []
        self.waves = WaveManager(mode=self.mode)
        self.practice_remaining = 0.0
        self.practice_kills = 0
        self._practice_buckets = {}
        self.kills = 0
        self.score = 0
        self.pending_levelups = 0
        self.card_choices = []
        self.level_up = LevelUpState()
        self.physics = SeparationSystem()
        self._level_up_push = []
        self.regen_timer = 0.0
        self.kill_heal_counter = 0
        self.game_over = False
        self.inventory_open = False
        self.victory = False
        self.elapsed = 0.0
        self.attack_timer = 0.0
        self.attack_facing_x = self.player.facing_x
        self.attack_facing_y = self.player.facing_y
        self.shake_timer = 0.0
        self.attack_cooldown = 0.0
        self.damage_cooldown = 0.0
        self.spawn_timer = 0.0
        for _ in range(3):
            self._spawn_enemy()

    @property
    def choosing_card(self) -> bool:
        return self.level_up.active or bool(self.card_choices)

    def world_to_screen(self, x, y):
        return self.camera.project(x, y, self.shake_offset)

    def screen_to_world(self, x, y):
        """Para interações no mundo; botões e cartas continuam em tela."""
        return self.camera.unproject(x, y, self.shake_offset)

    @property
    def choosing_weapon(self) -> bool:
        return self.phase == "weapon_choice"

    @property
    def weapon_id(self):
        return self.weapons.weapon_id

    @property
    def weapon_choices(self):
        return tuple(WEAPON_CONFIGS[weapon_id] for weapon_id in WEAPON_CHOICES)

    @property
    def weapon_elapsed(self):
        return self.weapons.elapsed

    @property
    def attack_timer(self):
        return self.weapons.animation_timer

    @attack_timer.setter
    def attack_timer(self, value):
        self.weapons.animation_timer = value

    @property
    def attack_cooldown(self):
        return self.weapons.cooldown

    @attack_cooldown.setter
    def attack_cooldown(self, value):
        self.weapons.cooldown = value

    @property
    def shake_timer(self):
        return self.effects.shake_timer

    @shake_timer.setter
    def shake_timer(self, value):
        # Compatibilidade para ferramentas que atribuíam o feedback normal.
        self.effects.shake_timer = max(0.0, value)
        self.effects.shake_duration = 0.10
        self.effects.shake_amplitude = 3

    @property
    def shake_offset(self) -> tuple[int, int]:
        if (self.inventory_open or self.game_over or self.choosing_card
                or (self.choosing_weapon and self.effects.finale_timer <= 0) or self.victory):
            return 0, 0
        return self.effects.shake_offset

    def _offer_next_card(self) -> None:
        if self.pending_levelups and not self.card_choices:
            self.card_choices = offer_level_cards(self.player, self.rng, self.weapon_id,
                chance=self.config.weapon_card_chance, evolved_weight=self.config.evolved_weapon_weight)
            self.inventory_open = False
            self.effects.hitstop_timer = 0.0
            self.effects.shake_timer = 0.0
            self.level_up.start()
            self._level_up_push = [
                (enemy, *self.physics.direction_from(enemy, self.player.x, self.player.y))
                for enemy in self.enemies if enemy.hp > 0
            ]
            self.effects.emit("levelup", self.player.x, self.player.y,
                              level=self.player.progression.nivel)

    def advance_presentation(self, dt) -> None:
        """Relógio da UI: apenas introdução e geometria, sem regras de combate."""
        if not isfinite(dt) or dt < 0:
            raise ValueError("O tempo da apresentação deve ser finito e não negativo.")
        if (not self.level_up.active or self.game_over or self.victory
                or self.player.progression.hp <= 0):
            return
        previous_elapsed = self.level_up.elapsed
        cards_shown = self.level_up.advance(dt)
        previous_push = ease_out_cubic(previous_elapsed / LEVEL_UP_PUSH_DURATION)
        current_push = ease_out_cubic(self.level_up.elapsed / LEVEL_UP_PUSH_DURATION)
        distance = LEVEL_UP_PUSH_DISTANCE * (current_push - previous_push)
        if distance > 0:
            for enemy, nx, ny in self._level_up_push:
                if enemy.hp > 0:
                    self.physics.translate(enemy, nx * distance, ny * distance, self.arena)
        movement_dt = (min(self.level_up.elapsed, LEVEL_UP_PUSH_DURATION)
                       - min(previous_elapsed, LEVEL_UP_PUSH_DURATION))
        if movement_dt > 0:
            self.physics.update(self.enemies, self.arena, movement_dt)
        if cards_shown:
            self.effects.emit("cards_show", self.player.x, self.player.y,
                              level=self.player.progression.nivel)

    def grant_xp(self, amount) -> int:
        if self.game_over or self.victory or self.phase != "waves":
            return 0
        gained = self.player.progression.ganhar_xp(amount)
        self.pending_levelups += gained
        self._offer_next_card()
        return gained

    def choose_card(self, index) -> bool:
        if (self.game_over or self.victory or not self.choosing_card
                or not self.level_up.selection_ready
                or self.player.progression.hp <= 0
                or isinstance(index, bool) or not isinstance(index, int)
                or not 0 <= index < len(self.card_choices)):
            return False
        card = self.card_choices[index]
        card_id = card.id
        first_stack = self.player.upgrades.get(card_id, 0) == 0
        if isinstance(card, WeaponCard):
            applied = self.equip_weapon(card.weapon_id)
        else:
            applied = apply_card(self.player, card_id)
        if not applied:
            return False
        if first_stack and card_id == "regen":
            self.regen_timer = 0.0
        if first_stack and card_id == "kill_heal":
            self.kill_heal_counter = 0
        self.pending_levelups -= 1
        self.card_choices = []
        self.level_up.end()
        self._level_up_push = []
        self.effects.emit("card_select", self.player.x, self.player.y,
                          card_id=card_id, name=card.name, index=index)
        self._offer_next_card()
        self._enter_weapon_choice_if_complete()
        return True

    def _enter_weapon_choice_if_complete(self) -> bool:
        if (self.phase == "waves" and self.waves.victory
                and not self.choosing_card and not self.pending_levelups):
            self.phase = "weapon_choice"
            self.inventory_open = False
            self.projectiles.clear()
            self.drops.clear()
            self.weapons.cancel_pending()
            return True
        return False

    @staticmethod
    def _weapon_choice(value):
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return WEAPON_CHOICES[value] if 0 <= value < len(WEAPON_CHOICES) else None
        return value if isinstance(value, str) and value in WEAPON_CHOICES else None

    def _practice_bucket(self, weapon_id):
        weapon_id = self._practice_key(weapon_id)
        if weapon_id not in self._practice_buckets:
            left, top, width, height = self.arena
            targets = []
            for index in range(self.config.training_targets):
                x = left + width * 0.72
                y = top + height * (index + 1) / (self.config.training_targets + 1)
                if width > ARENA_VIEWPORT[2] or height > ARENA_VIEWPORT[3]:
                    side = 1 if self.player.x < left + width - 320 else -1
                    x = max(left + 24, min(left + width - 24, self.player.x + side * 270))
                    y = max(top + 24, min(top + height - 24,
                        self.player.y + (index - (self.config.training_targets - 1) / 2) * 100))
                targets.append(TrainingTarget(x, y, hp=self.config.training_target_hp,
                                              max_hp=self.config.training_target_hp))
                self.physics.register(targets[-1])
            self._practice_buckets[weapon_id] = targets
        return self._practice_buckets[weapon_id]

    @staticmethod
    def _practice_key(weapon_id):
        # Três grupos originais, sem gerar alvos extras ao testar evoluções.
        return {"longbow": "bow", "returning_spear": "spear", "sword": "katana"}.get(weapon_id, weapon_id)

    def equip_weapon(self, weapon_id):
        """Troca atômica: não deixa flechas, giros ou lança da arma anterior."""
        if not self.weapons.switch(weapon_id):
            return False
        self.projectiles = [p for p in self.projectiles if p.team != "player"]
        self.attack_facing_x, self.attack_facing_y = self.player.facing_x, self.player.facing_y
        return True

    def choose_weapon(self, value) -> bool:
        weapon_id = self._weapon_choice(value)
        if (weapon_id is None or not self.choosing_weapon or self.choosing_card
                or self.pending_levelups or self.game_over or self.player.progression.hp <= 0):
            return False
        self.equip_weapon(weapon_id)
        self.phase = "practice"
        self.practice_remaining = (self.config.defense_practice_seconds if self.mode == GameMode.DEFENSE
                                   else self.config.lab_practice_seconds)
        self.projectiles.clear()
        self.drops.clear()
        self.enemies = self._practice_bucket(weapon_id)
        self.effects.emit("card_select", self.player.x, self.player.y,
                          name=self.weapons.config.name, weapon_id=weapon_id)
        return True

    def switch_weapon(self, value) -> bool:
        if isinstance(value, int) and not isinstance(value, bool):
            weapon_id = LAB_WEAPON_CHOICES[value] if 0 <= value < len(LAB_WEAPON_CHOICES) else None
        else:
            weapon_id = value if isinstance(value, str) and value in LAB_WEAPON_CHOICES else None
        if (weapon_id is None or self.mode != GameMode.LABORATORY or self.phase != "practice"
                or self.game_over or self.victory or self.inventory_open or self.choosing_card):
            return False
        if weapon_id == self.weapon_id:
            return True
        self._practice_buckets[self._practice_key(self.weapon_id)] = self.enemies
        self.equip_weapon(weapon_id)
        self.enemies = self._practice_bucket(weapon_id)
        return True

    def _finish_practice(self) -> None:
        self.phase = "victory"
        self.victory = True
        self.projectiles.clear()
        self.weapons.cancel_pending()

    def _spawn_enemy(self) -> None:
        if self.phase != "waves" or len(self.enemies) >= 10 or not self.waves.can_spawn:
            return
        left, top, width, height = self.arena
        position = None
        # Amostras limitadas evitam travamento com RNG controlado ou arena pequena.
        for _ in range(40):
            if width > ARENA_VIEWPORT[2] or height > ARENA_VIEWPORT[3]:
                angle, distance = self.rng.uniform(0, 2 * pi), self.rng.uniform(220, 480)
                x = max(left + 32, min(left + width - 32, self.player.x + cos(angle) * distance))
                y = max(top + 32, min(top + height - 32, self.player.y + sin(angle) * distance))
            else:
                x = self.rng.uniform(left + 32, left + width - 32)
                y = self.rng.uniform(top + 32, top + height - 32)
            if hypot(x - self.player.x, y - self.player.y) >= 220:
                position = x, y
                break
        if position is None:
            corners = (
                (left + 32, top + 32), (left + width - 32, top + 32),
                (left + 32, top + height - 32), (left + width - 32, top + height - 32),
            )
            x, y = max(corners, key=lambda point: hypot(point[0] - self.player.x, point[1] - self.player.y))
            if hypot(x - self.player.x, y - self.player.y) < 220:
                return
            position = x, y
        kind = self.waves.next_kind()
        if kind is None:
            return
        enemy_class = {"swordsman": Swordsman, "archer": Archer,
                       "worm": Worm, "rootkit": Rootkit}.get(kind, Enemy)
        enemy = enemy_class(*position)
        if isinstance(enemy, Rootkit):
            enemy.hp = enemy.max_hp = self.config.rootkit_hp
            enemy.speed = self.config.rootkit_speed
            enemy.damage = self.config.rootkit_damage
            enemy.telegraph_duration = self.config.rootkit_telegraph
            enemy.recovery_duration = self.config.rootkit_recovery
            enemy.attack_range = self.config.rootkit_attack_range
            enemy.attack_angle = self.config.rootkit_attack_angle
            enemy.projectile_speed = self.config.rootkit_projectile_speed
            enemy.projectile_count = self.config.rootkit_projectile_count
            self.effects.emit("boss_spawn", enemy.x, enemy.y, enemy_id=id(enemy))
        elif isinstance(enemy, Worm):
            enemy.damage *= self.waves.damage_scale
            # A cauda nasce atrás da cabeça, afastando-se do jogador.
            dx, dy = enemy.x - self.player.x, enemy.y - self.player.y
            length = hypot(dx, dy) or 1
            for index, segment in enumerate(enemy.segments):
                segment.x = enemy.x + dx / length * index * 32
                segment.y = enemy.y + dy / length * index * 32
            enemy.reset_trail(self.arena)
        else:
            enemy.hp *= self.waves.stat_scale
            enemy.max_hp = enemy.hp
            enemy.damage *= self.waves.damage_scale
        self.enemies.append(enemy)
        self.physics.register(enemy)

    def toggle_inventory(self) -> None:
        if (not self.game_over and not self.victory and not self.choosing_card
                and not self.choosing_weapon):
            self.inventory_open = not self.inventory_open

    def use_potion(self) -> bool:
        if self.game_over or self.victory or self.choosing_card or self.choosing_weapon:
            return False
        return self.player.inventory.use_potion(self.player.progression)

    def _attack(self, direction=None) -> set:
        if not self.weapons.ready or getattr(self.player, "stun_timer", 0) > 0:
            return set()
        self.attack_facing_x, self.attack_facing_y = direction or (self.player.facing_x, self.player.facing_y)
        return self._resolve_pulses(self.weapons.start(self.player,
                                   (self.attack_facing_x, self.attack_facing_y)))

    def _auto_attack(self):
        if not self.weapons.ready:
            return set()
        target = nearest_target(self.player, self.enemies,
                                self.weapons.config.reach * self.player.attack_range / 70)
        if target is None:
            return set()
        part = target[1]
        dx, dy = part.x - self.player.x, part.y - self.player.y
        length = hypot(dx, dy)
        direction = (dx / length, dy / length) if length else (self.player.facing_x, self.player.facing_y)
        return self._attack(direction)

    def _enemy_direction(self, enemy):
        """Orientação visual; não altera a direção capturada pelos ataques."""
        if isinstance(enemy, Worm) and len(enemy.segments) > 1:
            first, second = enemy.segments[:2]
            dx, dy = first.x - second.x, first.y - second.y
        elif hasattr(enemy, "facing_x") and hasattr(enemy, "facing_y"):
            dx, dy = enemy.facing_x, enemy.facing_y
        else:
            previous = self.enemy_motion.get(id(enemy))
            if previous is not None:
                return previous[1:]
            dx, dy = self.player.x - enemy.x, self.player.y - enemy.y
        distance = hypot(dx, dy)
        return (dx / distance, dy / distance) if distance > 1e-12 else (1, 0)

    def _hit_enemy(self, enemy, x, y, damage=None, direction=None) -> bool:
        previous_hp = enemy.hp
        previous_segments = len(enemy.segments) if isinstance(enemy, Worm) else 0
        old_head = (enemy.head.x, enemy.head.y) if isinstance(enemy, Worm) and enemy.head else None
        facing_x, facing_y = self._enemy_direction(enemy)
        if not apply_enemy_hit(self.player, enemy, damage=damage, direction=direction):
            return False
        self.effects.emit("hit", x, y, damage=previous_hp - enemy.hp,
                          strong=isinstance(enemy, (Worm, Rootkit)), enemy_id=id(enemy),
                          enemy_kind=enemy.kind)
        if previous_segments and len(enemy.segments) < previous_segments:
            self.effects.emit("wormrupture", *old_head, enemy_id=id(enemy), strong=True,
                              facing_x=facing_x, facing_y=facing_y, final=not enemy.segments)
            if enemy.head:
                self.effects.emit("newhead", enemy.head.x, enemy.head.y, enemy_id=id(enemy))
        return True

    def _resolve_pulses(self, pulses) -> set:
        hit_ids = set()
        for pulse in pulses:
            if pulse.weapon_id in ("bow", "longbow"):
                if sum(projectile.team == "player" for projectile in self.projectiles) < self.config.max_player_projectiles:
                    speed = WEAPON_CONFIGS[pulse.weapon_id].projectile_speed
                    self.projectiles.append(Projectile(self.player.x, self.player.y,
                        pulse.facing_x * speed, pulse.facing_y * speed, damage=pulse.damage,
                        radius=4, ttl=pulse.reach / speed + 0.1, team="player",
                        range_remaining=pulse.reach,
                        max_hits=LONGBOW_MAX_HITS if pulse.weapon_id == "longbow" else 1,
                        kind="piercing_arrow" if pulse.weapon_id == "longbow" else "arrow"))
                continue
            if pulse.weapon_id == "returning_spear":
                speed = WEAPON_CONFIGS["returning_spear"].projectile_speed
                self.weapons.returning_spear = ReturningSpear(Projectile(self.player.x, self.player.y,
                    pulse.facing_x * speed, pulse.facing_y * speed, damage=pulse.damage,
                    radius=pulse.width / 2, ttl=3, team="player", range_remaining=pulse.reach,
                    kind="returning_spear"))
                continue
            for enemy in self.enemies:
                if enemy.hp <= 0:
                    continue
                targets = enemy.segments if isinstance(enemy, Worm) else (enemy,)
                target = None
                for candidate in targets:
                    if pulse.weapon_id == "spear":
                        hit = in_thrust(self.player.x, self.player.y, pulse.facing_x,
                                        pulse.facing_y, candidate, pulse.reach, pulse.width)
                    else:
                        hit = in_cone(self.player.x, self.player.y, pulse.facing_x, pulse.facing_y,
                                      candidate.x, candidate.y, candidate.radius, pulse.reach, pulse.angle)
                    if hit:
                        target = candidate
                        break
                if target is not None and self._hit_enemy(enemy, target.x, target.y,
                        damage=pulse.damage):
                    hit_ids.add(id(enemy))
        return hit_ids

    def _heal(self, amount) -> None:
        progression = self.player.progression
        if progression.hp > 0:
            progression.hp = min(progression.hp_maximo, progression.hp + amount)

    def _collect_defeated(self) -> None:
        survivors = []
        for enemy in self.enemies:
            if enemy.hp > 0:
                survivors.append(enemy)
                continue
            facing_x, facing_y = self._enemy_direction(enemy)
            self.effects.emit("death", enemy.x, enemy.y, enemy_id=id(enemy),
                              enemy_kind=enemy.kind, strong=isinstance(enemy, (Worm, Rootkit)),
                              facing_x=facing_x, facing_y=facing_y)
            if self.phase == "practice" or isinstance(enemy, TrainingTarget):
                self.practice_kills += 1
                continue
            self.kills += 1
            self.waves.register_defeat()
            self.pending_levelups += self.player.progression.registrar_inimigo_derrotado()
            if self.player.kill_heal > 0:
                self.kill_heal_counter += 1
                if self.kill_heal_counter >= 5:
                    self.kill_heal_counter -= 5
                    self._heal(self.player.kill_heal)
            kind = None if isinstance(enemy, (Rootkit, Worm)) else roll_drop(self.rng, self.config)
            if kind is not None and len(self.drops) < 20:
                self.drops.append(Drop(enemy.x, enemy.y, kind=kind))
        self.enemies = survivors
        live_ids = {id(enemy) for enemy in survivors}
        self.enemy_motion = {key: value for key, value in self.enemy_motion.items() if key in live_ids}
        if self.phase == "practice":
            self._practice_buckets[self._practice_key(self.weapon_id)] = survivors
            target_limit = self.config.training_targets * (3 if self.mode == GameMode.LABORATORY else 1)
            if self.practice_kills >= target_limit:
                self._finish_practice()
            return
        if (not self.enemies and self.waves.spawned >= self.waves.total
                and self.waves.defeated >= self.waves.total):
            self.projectiles.clear()
            if self.waves.number == self.waves.max_waves:
                self.waves.update(0, 0)
        self._offer_next_card()
        self._enter_weapon_choice_if_complete()

    def _damage_player(self, amount) -> bool:
        if (self.game_over or self.victory or self.inventory_open or self.choosing_card
                or self.choosing_weapon or self.damage_cooldown > 0
                or self.player.progression.hp <= 0):
            return False
        apply_damage(self.player.progression, amount * self.player.damage_multiplier)
        self.damage_cooldown = DAMAGE_COOLDOWN
        if self.player.progression.hp <= 0:
            self.game_over = True
        return True

    def _update_enemies(self, dt, hit_ids) -> None:
        damage_intents = []
        self.enemy_motion = {id(enemy): (False, *self._enemy_direction(enemy))
                             for enemy in self.enemies}
        for enemy in self.enemies:
            if id(enemy) in hit_ids and getattr(enemy, "interruptible", True):
                continue
            # O chefe continua sua IA, mas o flash recém-criado conserva .10 s.
            free_time = dt if id(enemy) in hit_ids else enemy.advance_feedback(dt, self.arena)
            if enemy.stun_timer > 0 or enemy.knockback_timer > 0:
                continue
            if isinstance(enemy, TrainingTarget):
                continue
            # Recuo e separação não se tornam animação de caminhada.
            before_x, before_y = enemy.x, enemy.y
            if isinstance(enemy, Rootkit):
                action = enemy.advance_ai(free_time, self.player, self.arena)
                if action is not None:
                    if action.pattern == "cone":
                        damage_intents.append((enemy, action.facing_x, action.facing_y,
                                               enemy.attack_range, enemy.attack_angle))
                    else:
                        available = 40 - sum(projectile.team == "enemy" for projectile in self.projectiles)
                        self.projectiles.extend(action.projectiles[:max(0, available)])
            elif isinstance(enemy, Swordsman):
                if enemy.advance_ai(free_time, self.player, self.arena):
                    damage_intents.append((enemy, enemy.facing_x, enemy.facing_y, 60, 90))
            elif isinstance(enemy, Archer):
                projectile = enemy.advance_ai(free_time, self.player, self.arena)
                if projectile is not None and sum(p.team == "enemy" for p in self.projectiles) < 40:
                    self.projectiles.append(projectile)
                    self.effects.emit("archerfire", projectile.x, projectile.y,
                                      enemy_id=id(enemy), facing_x=enemy.facing_x,
                                      facing_y=enemy.facing_y)
            else:
                enemy.move_towards(self.player, free_time)
                damage_intents.append((enemy, None, None, None, None))
            dx, dy = enemy.x - before_x, enemy.y - before_y
            distance = hypot(dx, dy)
            if distance > 1e-9:
                self.enemy_motion[id(enemy)] = (True, dx / distance, dy / distance)
        self.physics.update(self.enemies, self.arena, dt)
        for enemy, facing_x, facing_y, reach, angle in damage_intents:
            if enemy.hp <= 0 or enemy.stun_timer > 0 or enemy.knockback_timer > 0:
                continue
            if reach is None:
                targets = enemy.segments if isinstance(enemy, Worm) else (enemy,)
                if any(touching(self.player, target) for target in targets):
                    self._damage_player(enemy.damage)
            elif in_cone(enemy.x, enemy.y, facing_x, facing_y, self.player.x,
                         self.player.y, self.player.radius, reach, angle):
                self._damage_player(enemy.damage)
            if self.game_over:
                return

    def _projectile_intersections(self, projectile):
        intersections = []
        for enemy in self.enemies:
            if enemy.hp <= 0 or id(enemy) in projectile.hit_ids:
                continue
            targets = enemy.segments if isinstance(enemy, Worm) else (enemy,)
            for target in targets:
                fraction = projectile.hit_fraction(target)
                if fraction is not None:
                    intersections.append((fraction, enemy))
        return sorted(intersections, key=lambda entry: entry[0])

    def _advance_returning_spear(self, dt, spear):
        hit_ids = set()
        if spear is None or spear is not self.weapons.returning_spear:
            return hit_ids
        was_flying = not spear.landed
        spear.advance(dt, self.arena)
        projectile = spear.projectile
        if was_flying:
            intersections = self._projectile_intersections(projectile)
            if intersections:
                fraction, enemy = intersections[0]
                x = projectile.previous_x + (projectile.x - projectile.previous_x) * fraction
                y = projectile.previous_y + (projectile.y - projectile.previous_y) * fraction
                if self._hit_enemy(enemy, x, y, damage=projectile.damage,
                                   direction=(projectile.vx, projectile.vy)):
                    projectile.hit_ids.add(id(enemy))
                    hit_ids.add(id(enemy))
                spear.land_at(x, y)
        manual = (not spear.expired and spear.landed
                  and hypot(self.player.x - spear.x, self.player.y - spear.y)
                  <= self.player.radius + SPEAR_PICKUP_RADIUS)
        if spear.expired or manual:
            self.weapons.returning_spear = None
            self.weapons.animation_timer = 0
            self.weapons.cooldown = max(self.weapons.cooldown,
                self.weapons.config.cooldown * self.player.attack_interval / .35)
            if manual:
                self.weapons.spin_timer = SPEAR_SPIN_DURATION
                pulse = AttackPulse((-1, 0), "spin", self.player.damage * self.weapons.config.damage_multiplier,
                                    1, 0, SPEAR_SPIN_REACH * self.player.attack_range / 70, 0, 360)
                hit_ids.update(self._resolve_pulses((pulse,)))
                self.effects.emit("attack", self.player.x, self.player.y)
            else:
                self.weapons.return_origin = spear.x, spear.y
                self.weapons.return_timer = SPEAR_RETURN_DURATION
        return hit_ids

    def _update_projectiles(self, dt, previous_projectiles) -> None:
        removed_ids = set()
        active_ids = {id(projectile) for projectile in self.projectiles}
        for projectile in previous_projectiles:
            if id(projectile) not in active_ids:
                continue
            projectile.advance(dt)
            hit = False
            if projectile.team == "player":
                for fraction, enemy in self._projectile_intersections(projectile):
                    if id(enemy) in projectile.hit_ids or enemy.hp <= 0:
                        continue
                    x = projectile.previous_x + (projectile.x - projectile.previous_x) * fraction
                    y = projectile.previous_y + (projectile.y - projectile.previous_y) * fraction
                    if self._hit_enemy(enemy, x, y, damage=projectile.damage,
                                       direction=(projectile.vx, projectile.vy)):
                        projectile.hit_ids.add(id(enemy))
                    hit = len(projectile.hit_ids) >= projectile.max_hits
                    if hit:
                        break
                if (self.phase == "waves" and self.waves.spawned >= self.waves.total
                        and all(candidate.hp <= 0 for candidate in self.enemies)):
                    self.projectiles.clear()
                    break
            elif projectile.hits(self.player):
                self._damage_player(projectile.damage)
                hit = True
            if hit:
                removed_ids.add(id(projectile))
            elif (projectile.ttl <= 0 or projectile.outside(self.arena)
                  or (projectile.range_remaining is not None and projectile.range_remaining <= 0)):
                removed_ids.add(id(projectile))
            if self.game_over:
                break
        self.projectiles = [projectile for projectile in self.projectiles
                            if id(projectile) not in removed_ids]

    def update(self, dt, move_x=0, move_y=0, attack=False) -> None:
        if not isfinite(dt) or dt < 0:
            raise ValueError("O tempo decorrido deve ser finito e não negativo.")
        if (self.game_over or self.victory or self.inventory_open
                or self.choosing_card or self.choosing_weapon):
            return
        if self.player.progression.hp <= 0:
            self.game_over = True
            return
        self._collect_defeated()
        if self.choosing_card or self.choosing_weapon or self.victory:
            return
        if self.phase == "practice":
            if self.practice_remaining <= 0:
                self._finish_practice()
                return
            dt = min(dt, self.practice_remaining)
        self.elapsed += dt
        previous_projectiles = list(self.projectiles)
        previous_spear = self.weapons.returning_spear
        delayed_pulses = self.weapons.update(dt)
        self.damage_cooldown = max(0.0, self.damage_cooldown - dt)
        previous_player = self.player.x, self.player.y
        self.player.move(move_x, move_y, dt, self.arena)
        self.player_moving = hypot(self.player.x - previous_player[0], self.player.y - previous_player[1]) > 1e-9
        self.camera.update(self.player.x, self.player.y, dt)
        self.player.overclock_timer = max(0.0, self.player.overclock_timer - dt)
        hit_ids = self._resolve_pulses(delayed_pulses)
        hit_ids.update(self._advance_returning_spear(dt, previous_spear))
        if self.auto_attack:
            hit_ids.update(self._auto_attack())
        elif attack:
            hit_ids.update(self._attack())
        self._collect_defeated()
        if self.choosing_card or self.choosing_weapon or self.victory:
            return
        self._update_enemies(dt, hit_ids)
        if self.game_over:
            return
        self._update_projectiles(dt, previous_projectiles)
        if self.game_over:
            return
        self._collect_defeated()
        if self.choosing_card or self.choosing_weapon or self.victory:
            return

        remaining_drops = []
        for drop in self.drops:
            if touching(self.player, drop):
                result = collect_drop(self.player, drop.kind, self.config)
                self.score += result.score
                self.effects.emit("pickup", drop.x, drop.y,
                                  healed=result.healed, potions=result.potions,
                                  overclock=result.overclock, drop_kind=drop.kind)
                if result.score:
                    self.effects.emit("score", drop.x, drop.y, amount=result.score)
            else:
                remaining_drops.append(drop)
        self.drops = remaining_drops

        if self.player.regen_heal > 0:
            self.regen_timer += dt
            while self.regen_timer >= 5:
                self.regen_timer -= 5
                self._heal(self.player.regen_heal)

        if self.phase == "practice":
            self.practice_remaining = max(0.0, self.practice_remaining - dt)
            if self.practice_remaining <= 1e-12:
                self._finish_practice()
            return

        previous_wave = self.waves.number
        self.waves.update(dt, len(self.enemies))
        if self._enter_weapon_choice_if_complete():
            return
        if self.waves.number != previous_wave:
            self.spawn_timer = 0.0
            for _ in range(3):
                self._spawn_enemy()
        elif self.waves.can_spawn:
            self.spawn_timer += dt
            while self.spawn_timer >= 1.0:
                self.spawn_timer -= 1.0
                self._spawn_enemy()
        else:
            self.spawn_timer = 0.0

"""Escolha visual de estados: observa a simulação, sem alterar combate."""

from math import floor, isfinite, pi

from .combat import ATTACK_DURATION, HIT_FLASH_DURATION


def direction_quantized(angle):
    """Oito orientações estáveis; ângulo de tela em radianos, leste = zero."""
    return floor(angle / (pi / 4) + .5) % 8


def choose_state(enemy, moving=None):
    if enemy.hp <= 0:
        return "death"
    winding = getattr(enemy, "telegraph_timer", 0) > 0
    attacking = getattr(enemy, "attack_timer", 0) > 0
    # ROOTKIT continua antecipando e atacando mesmo ao receber um acerto.
    if getattr(enemy, "kind", "basic") == "rootkit":
        if winding:
            return "windup"
        if attacking:
            return "attack"
    if enemy.hit_flash_timer > 0:
        return "hurt"
    if winding:
        return "windup"
    if attacking:
        return "attack"
    if enemy.stun_timer > 0 or enemy.knockback_timer > 0:
        return "idle"
    if moving is None:
        moving = enemy.speed > 0 and getattr(enemy, "state", "chase") == "chase"
    return "move" if moving else "idle"


def state_progress(enemy, state, animation_time, duration_ms):
    """Converte timers lógicos em posição no sheet; nunca avança um timer."""
    if state == "windup":
        total = getattr(enemy, "telegraph_duration", None)
        if total is None:
            total = .45 if getattr(enemy, "kind", "") == "archer" else .35
        remaining = getattr(enemy, "telegraph_timer", 0)
    elif state == "attack":
        total = .20 if getattr(enemy, "kind", "") == "rootkit" else ATTACK_DURATION
        remaining = getattr(enemy, "attack_timer", 0)
    elif state == "hurt":
        total, remaining = HIT_FLASH_DURATION, enemy.hit_flash_timer
    else:
        return max(0.0, animation_time * 1000)
    progress = max(0.0, min(1.0, 1 - remaining / total)) if total > 0 else 1.0
    return duration_ms * progress


def frame_index(phase_ms, durations_ms, loop):
    """Índice limitado ou cíclico, com suporte a durações diferentes por frame."""
    if not durations_ms:
        return 0
    if not isfinite(phase_ms):
        return 0
    phase = max(0.0, phase_ms)
    total = sum(durations_ms)
    if loop:
        phase %= total
    for index, duration in enumerate(durations_ms):
        if phase < duration:
            return index
        phase -= duration
    return len(durations_ms) - 1

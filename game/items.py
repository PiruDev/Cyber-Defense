"""Resolução de coleta de poções; XP e pontuação permanecem independentes."""


def collect_potion(player) -> int:
    """Consome uma coleta e retorna somente os pontos concedidos."""
    if player.progression.hp <= 0:
        return 0
    if player.inventory.add_potion():
        return 0
    progression = player.progression
    if progression.hp < progression.hp_maximo:
        progression.hp = min(progression.hp_maximo, progression.hp + 35)
        return 0
    return 10

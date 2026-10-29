"""Catálogo e seleção de melhorias; independente da apresentação e do Pygame."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    id: str
    name: str
    description: str
    max_stacks: int


CARDS = (
    Card("damage", "Lâmina afiada", "+20% de dano por escolha (multiplicativo).", 8),
    Card("max_hp", "Vitalidade", "+25 HP atual e máximo.", 8),
    Card("speed", "Passos leves", "+12% da velocidade-base por escolha.", 5),
    Card("cooldown", "Golpe veloz", "-10% do intervalo de ataque (multiplicativo).", 8),
    Card("range", "Lâmina longa", "+15% do alcance-base por escolha.", 6),
    Card("regen", "Regeneração", "+1 HP a cada 5 segundos ativos.", 5),
    Card("kill_heal", "Fôlego de batalha", "+2 HP a cada 5 abates.", 5),
    Card("reduction", "Armadura", "-10% do dano recebido (multiplicativo).", 7),
)

_BY_ID = {card.id: card for card in CARDS}


def offer_cards(stacks: dict, rng) -> list[Card]:
    """Sorteia três melhorias distintas que ainda podem ser adquiridas.

    Até 35 escolhas o teto de níveis da partida garante três elegíveis:
    os seis menores limites somam 36. Fora desse contrato, falha explicitamente.
    """
    eligible = [card for card in CARDS
                if stacks.get(card.id, 0) < card.max_stacks]
    if len(eligible) < 3:
        raise ValueError("São necessárias pelo menos três cartas elegíveis.")
    return rng.sample(eligible, 3)


def apply_card(player, card_id: str) -> bool:
    """Aplica uma escolha válida uma vez; atributos derivados ficam no Player."""
    card = _BY_ID.get(card_id)
    if card is None:
        return False
    count = player.upgrades.get(card_id, 0)
    if count >= card.max_stacks:
        return False
    player.upgrades[card_id] = count + 1
    if card_id == "max_hp":
        progression = player.progression
        progression.hp_maximo += 25
        progression.hp = min(progression.hp_maximo, progression.hp + 25)
    return True

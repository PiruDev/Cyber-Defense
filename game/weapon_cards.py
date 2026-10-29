"""Uma carta de arma opcional por apresentação, sem duplicar upgrades gerais."""

from dataclasses import dataclass

from .balance import WEAPON_CONFIGS
from .cards import offer_cards

WEAPON_REPLACEMENT_WARNING = "ATENÇÃO: VOCÊ PERDERÁ SUA ARMA ATUAL."
EVOLVED = frozenset(("longbow", "returning_spear"))
FAMILIES = {"sword": "blade", "katana": "blade", "bow": "bow", "longbow": "bow",
            "spear": "spear", "returning_spear": "spear"}


@dataclass(frozen=True)
class WeaponCard:
    weapon_id: str
    max_stacks: int = 1

    @property
    def id(self):
        return "weapon:" + self.weapon_id

    @property
    def name(self):
        return WEAPON_CONFIGS[self.weapon_id].name

    @property
    def description(self):
        return {"sword": "Um corte automático por ciclo.", "katana": "Dois cortes rápidos por ciclo.",
                "bow": "Flechas automáticas direcionais.", "spear": "Estocada automática estreita.",
                "longbow": "Flechas perfurantes: até 3 inimigos distintos.",
                "returning_spear": "Arremesse, recupere e execute um giro de 360 graus."}[self.weapon_id]


def eligible_weapons(current_weapon):
    return [weapon for weapon in WEAPON_CONFIGS if weapon != current_weapon
            and not (current_weapon in EVOLVED and weapon not in EVOLVED
                     and FAMILIES[weapon] == FAMILIES[current_weapon])]


def offer_level_cards(player, rng, current_weapon, *, chance=.08, evolved_weight=.25):
    cards = offer_cards(player.upgrades, rng)
    if chance <= 0 or rng.random() >= chance:
        return cards
    eligible = eligible_weapons(current_weapon)
    weighted = [(weapon, evolved_weight if weapon in EVOLVED else 1) for weapon in eligible]
    weighted = [(weapon, weight) for weapon, weight in weighted if weight > 0]
    total = sum(weight for _, weight in weighted)
    if not total:
        return cards
    draw = rng.random() * total
    selected = weighted[-1][0]
    for weapon, weight in weighted:
        draw -= weight
        if draw < 0:
            selected = weapon
            break
    cards[rng.randrange(3)] = WeaponCard(selected)
    return cards

"""Regras de experiência e níveis, independentes da interface gráfica."""

from dataclasses import dataclass


XP_POR_INIMIGO = 25


@dataclass
class Progressao:
    nivel: int = 1
    xp: int = 0
    hp_maximo: int = 100
    hp: int = 100
    dano: int = 1
    automatic_bonuses: bool = True
    max_level: int | None = None

    @property
    def xp_necessario(self) -> int:
        """XP necessário para avançar a partir do nível atual."""
        return 100 + 50 * (self.nivel - 1)

    def ganhar_xp(self, quantidade: int) -> int:
        """Acumula XP e devolve quantos níveis foram ganhos."""
        if isinstance(quantidade, bool) or not isinstance(quantidade, int):
            raise TypeError("A quantidade de XP deve ser um número inteiro.")
        if quantidade < 0:
            raise ValueError("A quantidade de XP não pode ser negativa.")

        self.xp += quantidade
        niveis_ganhos = 0
        while (self.xp >= self.xp_necessario
               and (self.max_level is None or self.nivel < self.max_level)):
            self.xp -= self.xp_necessario
            self.nivel += 1
            if self.automatic_bonuses:
                self.hp_maximo += 20
                self.dano += 1
                self.hp = self.hp_maximo
            niveis_ganhos += 1
        return niveis_ganhos

    def registrar_inimigo_derrotado(self) -> int:
        """Ponto de integração para uma futura confirmação de derrota."""
        return self.ganhar_xp(XP_POR_INIMIGO)

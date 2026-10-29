# Missão 012 — sprites de armas evoluídas

Dois desenhos originais produzidos localmente pelo subagente `pixel_artist`, com
primitivas de Pygame e a paleta cibernética do AgentOS. Nenhuma API paga,
dependência nova, referência externa ou imagem de terceiros foi utilizada.
Os sprites anteriores não foram substituídos.

| Arquivo em `assets/sprites/weapons/` | Tamanho | Pivô | Orientação |
|---|---|---|---|
| `longbow.png` | 54×54 | (27,27) | leste |
| `returning_spear.png` | 112×22 | (56,11) | leste |

Um frame por recurso. RGBA com alfa binário 0/255, margens transparentes e
paleta de até 12 cores. O Arco Longo reutiliza a linguagem visual do arco
procedural, com membros luminosos, terminais roxos e cabo de dados. A Lança de
Retorno combina haste ciano, lâmina segmentada e transmissor roxo na base.

As animações devem reutilizar a rotação/disparo e arremesso/retorno do runtime.
Os PNGs não definem dano, colisão, alcance ou temporizadores. Carregar depois
da inicialização gráfica, preservar o pivô e usar `pygame.transform.scale`
para nearest-neighbor. Os detalhes maiores de brilho e rastro pertencem a
camadas de efeitos separadas.

Reproduzir a partir da raiz:

```powershell
.\.venv\Scripts\python.exe assets/references/mission012/build_evolved_weapons.py
```

O script grava somente os dois PNGs novos, o manifesto e a prévia desta pasta.
Valida dimensões, margens, alfa, paleta e recarregamento dos PNGs. A prévia
`evolved_weapons_preview.png` mostra tamanho nativo e ampliação nearest-neighbor
4×; a avaliação final durante o combate depende de inspeção do jogo em movimento.

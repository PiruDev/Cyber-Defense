# Missão 011 — jogador e piso digital

Produção original e local pelo subagente `pixel_artist`, usando Pygame já
disponível na `.venv`. Nenhuma API paga, imagem de terceiros ou dependência nova.

O arquivo `assets/sprites/player/sentinel_idle.png` foi inspecionado e preservado
byte a byte. Os novos sheets derivam desse piloto, cuja origem permanece em
`assets/references/sentinel_idle_source.md`. A integração do piloto e a criação
das animações foram solicitadas expressamente na Missão 011.

| Recurso novo | Canvas | Frames | Tempo | Pivô |
|---|---|---|---|---|
| `sentinel_idle_sheet.png` | 192×48 | 4 células de 48×48 | 150 ms por frame | (24,24) |
| `sentinel_move_sheet.png` | 288×48 | 6 células de 48×48 | 100 ms por frame | (24,24) |
| `digital_grid_tile.png` | 40×40 | 1 | estático | canto superior esquerdo |
| `digital_circuit_tile.png` | 40×40 | 1 | estático | canto superior esquerdo |
| `digital_panel_tile.png` | 40×40 | 1 | estático | canto superior esquerdo |

Os sheets estão em `assets/sprites/player/`, com orientação base sul e leitura
horizontal. A identidade do corpo e a paleta do original foram mantidas. O idle
possui pequenos brilhos eletrônicos; a caminhada usa passos de um pixel e um
deslocamento discreto do torso. Todos os frames usam a mesma âncora; a hitbox
continua sendo definida pela lógica do jogo. O ataque é uma camada de arma e
slash independente, sem eventos de dano definidos no sheet.

Os três tiles ficam em `assets/sprites/environment/`; foram desenhados pelo
script desta pasta, com navy e circuitos de baixo contraste. São opacos e não
animados, para que o renderer possa compor um piso fixo em coordenadas de mundo.
Não contêm iluminação pulsante nem ruído dependente do tempo.

Reprodução, a partir da raiz do projeto:

```powershell
.\.venv\Scripts\python.exe assets/references/mission011/build_player_floor.py
```

O script só regrava os cinco arquivos novos, os metadados e a prévia desta missão.
Ele verifica o hash do piloto antes e depois. Não modifica os inimigos aprovados.
`asset_manifest.json` registra caminhos, durações e pivôs. A prévia em
`player_floor_preview.png` usa nearest-neighbor; não representa validação humana
da movimentação durante uma partida. São microanimações derivadas do piloto,
não um redesenho de oito direções.

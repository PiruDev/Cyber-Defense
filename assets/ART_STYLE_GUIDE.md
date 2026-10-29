# Cyber Defense — direção de arte

## Armas evoluídas — Missão 012

Arco Longo (`assets/sprites/weapons/longbow.png`, 54×54, pivô 27,27) e Lança de
Retorno (`returning_spear.png`, 112×22, pivô 56,11) foram produzidos em pixel art
original pelo `pixel_artist`, base leste, RGBA com alfa binário e até doze cores.
A integração usa nearest-neighbor e animação procedural, com energia ciano/roxa.
As quatro armas anteriores reutilizam seus sprites procedurais existentes.
Script, manifesto, autoria e prévia: `assets/references/mission012/`.

## Atualização de produção — Missão 011

Esta atualização prevalece sobre as propostas futuras abaixo. O piloto existente
foi integrado por solicitação explícita do usuário, sem sobrescrever o original.
`sentinel_idle_sheet.png` tem 4×150 ms e `sentinel_move_sheet.png` tem 6×100 ms,
ambos em `assets/sprites/player/`, células 48×48, pivô (24,24), base sul. O runtime
usa oito rotações discretas em cache, não oito direções redesenhadas.

Escalas deliberadas em `game/visual_config.py`: jogador 1,25×; básico e arqueiro
1,5×; espadachim 1,25×; partes da minhoca 1×; ROOTKIT 1,15×. Os fatores fracionários
também usam nearest-neighbor, mantendo alfa binário e sem suavização. A minhoca
permanece em 1× porque seus corpos já medem 44 pixels opacos para espaçamento
de 32 unidades de trajetória. Canvas ampliado não altera a hitbox.

Três tiles 40×40, opacos e estáticos, foram produzidos em
`assets/sprites/environment/`: grid, circuito e placa. O piso é composto uma vez
em coordenadas de mundo; não é uma imagem fixa na janela. O slash é procedural,
com oito poses curtas, arco aberto e rastro, sem cunha triangular. Ciano no aliado,
magenta no espadachim; animações próprias do arco e da lança foram preservadas.

Autoria, script reproduzível, hash do original e metadados:
`assets/references/mission011/PROVENANCE.md` e `asset_manifest.json`.
Inspeção de capturas não equivale à aprovação humana do jogo em movimento.

SENTINEL-01 é um antivírus que defende o núcleo do sistema operacional. A arte
representa programas, circuitos e corrupção digital em pixel art 2D top-down.
Este guia organiza a produção; os recursos marcados como planejados ainda não
existem. A MISSÃO 010 integrou os inimigos em PNG; a MISSÃO 011 integra o piloto
SENTINEL-01 com animações derivadas e piso digital, conforme solicitação do usuário.

## Linguagem visual

- Silhuetas compactas, contorno escuro de 1 px e grupos de pixels bem definidos.
- Armadura em azul profundo, núcleo e sinais aliados em ciano; roxo nos circuitos.
- Inimigos em coral/magenta e semiboss em dourado, mantendo contraste com o aliado.
- Luz por blocos de cor, no máximo três níveis por material. Sem antialiasing,
  borrão ou glow semitransparente embutido no sprite. Os efeitos de luz do jogo
  podem continuar em camadas separadas.
- Fundo transparente; nada de sombra retangular, piso, texto ou arma fundida no
  sprite base do jogador. A direção inicial do idle é sul, para baixo na tela.
- Inspecionar em tamanho nativo, em fundo claro/escuro e junto do grid da arena.
  O protagonista está integrado; a avaliação durante uma partida continua humana.

## Paleta-base do protagonista

| Nome | Hex | Uso |
|---|---|---|
| Outline | `#07101F` | Contorno e divisões |
| Navy | `#10233B` | Armadura em sombra |
| Deep blue | `#142C46` | Placas e fundo de circuitos |
| Armor blue | `#1E3D5A` | Armadura principal |
| Steel | `#365B7D` | Luz do metal |
| Blue | `#3D73B8` | Placas iluminadas |
| Cyan | `#49E9F5` | Núcleo, visor e trilhas |
| Ice | `#ACF7FF` | Luz forte do núcleo |
| White | `#E2F7FF` | Pequenos brilhos |
| Dark purple | `#34234F` | Sombra dos circuitos |
| Purple | `#7045A6` | Conectores e detalhes |
| Violet | `#AC72DB` | Acentos de energia |

PNG final: RGBA, alfa 0 ou 255, até 12 cores opacas do conjunto acima. A geração
por IA pode fornecer uma imagem de origem maior; o PNG de produção precisa ser
validado novamente após adequação à grade, dimensões e paleta. A transparência
não conta como uma cor opaca. Não pintar o quadriculado no arquivo final.

As cores de contexto existentes continuam válidas: arena `#050916`/`#081121`,
painéis `#0E192B`, vírus `#F35691`, alerta dourado `#F3CA75`, texto `#E2F7FF`.

As famílias inimigas possuem suas próprias paletas de até doze cores no
`assets/sprites/enemies/manifest.json`: coral/magenta no vírus, vermelho e metal
roxo no espadachim, âmbar/magenta no arqueiro, dourado na minhoca e violeta/magenta
no ROOTKIT. Não aplicar a paleta azul/ciano do aliado a todas as classes.

## Escala e resoluções

Hoje o jogador tem raio lógico de 16 px, corpo gráfico de aproximadamente 40 px
e indicador de direção a 24 px do centro. O piloto usa **48×48 px**, centro/pivô
**(24, 24)**, corpo de aproximadamente 36–40 px e margem transparente. Para uma
futura integração, apresentar em 48×48 na escala 1× e manter a hitbox atual até
uma avaliação específica; o desenho não redefine colisões automaticamente.

Inimigos comuns têm raio de 17 px; segmentos da minhoca, 22 px; ROOTKIT, 32 px.
O plano abaixo considera esses tamanhos. Armas, halos e avisos de ataque usam
camadas separadas para conservar a leitura das hitboxes.

Ampliações de sprites devem usar nearest-neighbor e fatores inteiros: 1× para o
jogo atual, 2×/4×/8× para inspeção ou mudança deliberada da escala de toda a cena.
Não esticar um eixo isolado. Em Pygame, usar `pygame.transform.scale` para ampliar,
sem `smoothscale`/`rotozoom` no novo pixel art. A rotação futura exige revisão
visual de pixelização; variantes direcionais desenhadas são preferíveis.

Exemplo para futura integração, fora desta missão:

```python
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parents[1]
# Após pygame.display.set_mode; nunca carregar assets ao importar módulos.
sprite = pygame.image.load(str(ROOT / "assets/sprites/player/sentinel_idle.png")).convert_alpha()
preview = pygame.transform.scale(sprite, (sprite.get_width() * 8, sprite.get_height() * 8))
```

Os caminhos de catálogo são relativos à raiz `AgentOS`, com `/` nos documentos;
`pathlib.Path` resolve os separadores do Windows. Não depender do diretório de
trabalho para localizar um recurso durante a futura integração.

## Nomes e spritesheets

- Arquivos em minúsculas `snake_case`: `<entidade>_<acao>[_<direcao>].png`.
- Direções: `south`, `west`, `east`, `north`; não misturar sufixos PT/EN.
- Piloto de um frame: `sentinel_idle.png`, orientação sul, duração estática.
- Sheets futuros: `assets/animations/<entidade>_<acao>_sheet.png` e metadados JSON
  homônimos. Não gerar JSON apontando para frames ainda inexistentes.
- Células de dimensão constante; mesma âncora em todos os frames; alinhamento
  pelo centro do corpo, não pelo brilho ou pela ponta de uma arma.
- Ordem da leitura: esquerda para direita. Sheets com quatro direções usam
  linhas na ordem south, west, east, north e colunas de tempo.
- Sem recorte automático por frame, sem packing/rotação de células e sem espaço
  extra entre células. Registrar `frame_size`, `pivot`, `directions`,
  `durations_ms`, `loop` e marcadores de impacto quando a animação existir.
- Idle futuro: 4 frames de 150 ms; caminhada: 6 frames de 100 ms. São propostas
  de produção, não animações já implementadas. Os impactos das armas continuam
  definidos pelo sistema lógico do jogo, nunca pela frequência de renderização.

## Biblioteca e fila de produção

As linhas marcadas como **planejadas** ainda não foram produzidas. Não criar
PNGs vazios ou arquivos com extensão de imagem para representar planejamento.

| Categoria | Caminho relativo | Canvas por frame | Estado |
|---|---|---|---|
| Jogador | `assets/sprites/player/sentinel_idle.png` | 48×48 | Original preservado, integrado pela Missão 011 |
| Vírus básico | `assets/sprites/enemies/virus_basic/*.png` | 48×48 | Produzido, 4 estados / 17 frames |
| Espadachim | `assets/sprites/enemies/swordsman/*.png` | 64×64 | Produzido, 6 estados / 23 frames |
| Arqueiro | `assets/sprites/enemies/archer/*.png` | 48×48 | Produzido, 6 estados / 23 frames |
| Minhoca/cabeça | `assets/sprites/enemies/segmented_worm/head_*.png` | 64×64 | Produzido, 6 estados / 23 frames |
| Minhoca/corpo | `assets/sprites/enemies/segmented_worm/body_*.png` | 64×64 | Produzido, 4 estados / 14 frames |
| Minhoca/cauda | `assets/sprites/enemies/segmented_worm/tail_*.png` | 64×64 | Produzido, 4 estados / 14 frames |
| ROOTKIT | `assets/sprites/enemies/rootkit_boss/*.png` | 96×96 | Produzido, 6 estados / 25 frames |
| Espada inicial | `assets/sprites/weapons/sword_idle.png` | 72×24 | Planejado |
| Katana | `assets/sprites/weapons/katana_idle.png` | 72×24 | Planejado |
| Arco | `assets/sprites/weapons/bow_idle.png` | 48×48 | Planejado |
| Lança | `assets/sprites/weapons/spear_idle.png` | 112×24 | Planejado |
| Reparo | `assets/sprites/items/repair_pack.png` | 32×32 | Planejado |
| Overclock | `assets/sprites/items/overclock.png` | 32×32 | Planejado |
| Carta/frame | `assets/sprites/ui/upgrade_card_frame.png` | 48×64 | Planejado, montagem por bordas |
| Carta/ícones | `assets/sprites/ui/upgrade_<id>_icon.png` | 32×32 | Planejado, um arquivo por upgrade atual |
| Moldura | `assets/sprites/ui/panel_frame.png` | 24×24 | Planejado, nine-slice de 8 px |
| Ícones HP/XP | `assets/sprites/ui/hp_icon.png`, `xp_icon.png` no mesmo diretório | 16×16 | Planejado |
| Barras HP/XP | `assets/sprites/ui/hp_bar_frame.png`, `xp_bar_frame.png` no mesmo diretório | 48×12 | Planejado, preenchimento separado |
| Impacto | `assets/animations/hit_spark_sheet.png` | 32×32 | Planejado |
| Partícula digital | `assets/sprites/effects/digital_particle.png` | 8×8 | Planejado |
| Onda | `assets/animations/energy_wave_sheet.png` | 64×64 | Planejado; avaliar preservar a onda procedural |
| Level up | `assets/animations/level_up_sheet.png` | 64×64 | Planejado; texto continua separado |
| Morte/vírus | `assets/sprites/enemies/virus_basic/death.png` | 48×48 | Produzido, 5 frames |
| Morte/boss | `assets/sprites/enemies/rootkit_boss/death.png` | 96×96 | Produzido, 6 frames |
| Chão/grid | `assets/sprites/environment/digital_grid_tile.png` | 40×40 | Produzido, com variantes circuito e placa |
| Núcleo | `assets/sprites/environment/system_core.png` | 160×160 | Planejado |

Na biblioteca inimiga da MISSÃO 010, cada estado é um sheet horizontal de uma
linha, base leste e escala 1×. O runtime mantém oito rotações discretas em cache;
os telegraphs continuam no ângulo lógico exato. É uma adaptação documentada à
arquitetura atual, sem alterar o plano de direções desenhadas do jogador futuro.
Os 36 PNGs e 139 frames estão relacionados em `assets/sprites/enemies/README.md`.

Próxima produção após avaliação do protagonista: caminhada/idle direcional do
SENTINEL-01, reparo e overclock, armas, cartas e FX. Reutilizar os sistemas atuais
em vez de substituí-los por figuras estáticas. Os oito IDs de upgrade existentes
permanecem inalterados.

## Áudio, referências e autoria

- `assets/audio/music/`: biblioteca futura de músicas autorais.
- `assets/audio/sfx/`: biblioteca futura de efeitos de som.
- **Preservar** a procura atual de `assets/audio/theme.ogg` ou `theme.mp3` e o
  arquivo `assets/audio/README.md`; nada foi movido nem substituído nesta missão.
- `assets/references/`: prévias, fontes reproduzíveis e registro de origem.
  Referência visual não concede licença para incorporar arte de terceiros.
- O piloto precisa registrar ferramenta, processo, paleta e limitações em
  `assets/references/sentinel_idle_source.md`. Não utilizar API paga.
- Aprovação visual é uma etapa humana futura. Não registrar um sprite como
  aprovado somente porque passa na validação de PNG.

Referências técnicas, sem incorporar imagens de terceiros:
[Aseprite SpriteSize](https://www.aseprite.org/api/command/SpriteSize/) e
[Sprite/frames](https://www.aseprite.org/docs/sprite/).

## Checklist de entrega

PNG real com dimensões corretas, canal alfa e margens transparentes; paleta curta;
preview ampliado por nearest-neighbor; teste de carga com Pygame; inspeção em
tamanho nativo e ampliado; origem documentada; jogo e testes preservados. O piloto
do jogador aguarda avaliação antes de integração; a integração dos inimigos é
parte expressamente autorizada da MISSÃO 010.

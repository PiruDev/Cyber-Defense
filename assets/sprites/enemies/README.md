# Inimigos de Cyber Defense — sprites da MISSÃO 010

Os arquivos PNG deste diretório são recursos reais de produção. O manifesto
`manifest.json`, versão 1, é a fonte de caminhos, células, pivôs e tempos.
Todos os sheets têm uma linha, orientação-base **leste**, frames da esquerda
para a direita, escala nativa 1× e transparência binária 0/255.

| Tipo no manifesto | Diretório | Célula / pivô | Estados e frames |
|---|---|---|---|
| `basic` | `virus_basic/` | 48×48 / 24,24 | idle 4; move 6; hurt 2; death 5 |
| `swordsman` | `swordsman/` | 64×64 / 32,32 | idle 4; move 6; hurt 2; death 5; windup 3; attack 3 |
| `archer` | `archer/` | 48×48 / 24,24 | idle 4; move 6; hurt 2; death 5; windup 3; attack 3 |
| `worm_head` | `segmented_worm/head_*.png` | 64×64 / 32,32 | idle 4; move 4; hurt 2; rupture 4; new_head 3; death 6 |
| `worm_body` | `segmented_worm/body_*.png` | 64×64 / 32,32 | idle 4; move 4; hurt 2; rupture 4 |
| `worm_tail` | `segmented_worm/tail_*.png` | 64×64 / 32,32 | idle 4; move 4; hurt 2; rupture 4 |
| `rootkit` | `rootkit_boss/` | 96×96 / 48,48 | idle 4; move 6; hurt 2; death 6; windup 3; attack 4 |

São **36 PNGs**, **139 frames** e sete tipos visuais para cinco tipos lógicos.
Cada caminho de estado é relativo a este diretório. Um sheet de cinco frames
48×48, por exemplo, mede 240×48. Não há padding entre células nem recorte por frame.

## Direção e leitura

- Vírus: casco coral/vermelho, espinhos mecânicos e núcleo claro.
- Espadachim: armadura quadrada de robô corrompido, visor vermelho e lâmina de
  energia. Foi desenhado diretamente na grade top-down para conservar a leitura
  vista de cima. Seu canvas maior acomoda a espada; a hitbox lógica continua igual.
- Arqueiro: corpo triangular magenta escuro, aletas e arco/emissor âmbar.
- Minhoca: cabeça com mandíbulas, anéis mecânicos e cauda dourados. A cauda aponta
  para trás; o leste representa sua frente de conexão com o segmento anterior.
  O sprite não muda o espaçamento lógico de 32 px entre centros.
- ROOTKIT: armadura violeta, núcleo magenta e porta de ataque lateral. A diferença
  de tamanho vem da arte; HP, velocidade, raio e ataques continuam no jogo.

As paletas de até doze cores opacas por família constam de `manifest.json`.
O jogador mantém a paleta ciano/azul e não é substituído por esta biblioteca.

## Tempos e responsabilidade do runtime

Idle dura 600 ms; movimento, 600 ms nos robôs e 400 ms na minhoca. Hurt dura
100 ms. Morte comum dura 300 ms; ROOTKIT e cabeça final da minhoca, 450 ms.
Rupture dura 300 ms e new_head, 150 ms. A transformação começa como um segmento,
abre as mandíbulas e termina como cabeça; não cria outro inimigo ou recompensa.

Windup acompanha os timers lógicos existentes: 350 ms espadachim, 450 ms arqueiro,
650 ms ROOTKIT. Attack dura 140 ms nos comuns e 200 ms no boss. O impacto ocorre
quando a lógica termina a preparação e inicia o estado de ataque; os PNGs não
disparam dano, flechas, XP ou drops. Os campos de duração só descrevem a pose.
ROOTKIT mantém o aviso de ataque durante hit flash, pois não pode ser interrompido.

Ampliações usam nearest-neighbor. O runtime pode armazenar oito rotações discretas
em cache com `pygame.transform.rotate`, sem `smoothscale` nem `rotozoom` para estas
imagens. O aviso geométrico continua mostrando o ângulo lógico exato entre poses.

## Origem e inspeção

Atlas e pipeline ficam em `assets/references/mission010/`:

- `enemy_atlas.png`: amostras nativas e ampliadas para inspeção.
- `build_enemy_sheets.py`: preparação reproduzível com Pygame já instalado.
- `generation_prompts.json`: prompts exatos das cinco gerações integradas.
- `*_source.png`: fontes originais preservadas, sem arte de terceiros.
- `PROVENANCE.md`: decisões, limites e verificações.

Os sprites têm perspectiva top-down estilizada e detalhes simplificados na grade
de jogo. O atlas é uma inspeção estática; ritmo, orientação e legibilidade em
combate precisam ser avaliados também nas capturas e no jogo em movimento.

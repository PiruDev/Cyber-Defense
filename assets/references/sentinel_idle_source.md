# SENTINEL-01 — proveniência do primeiro sprite

Produção original para Cyber Defense na MISSÃO 009. O personagem em execução
permanece o desenho procedural anterior: este PNG aguarda avaliação artística.

## Arquivos

- Entrega: `assets/sprites/player/sentinel_idle.png` — PNG RGBA, **48×48**.
- Prévia: `assets/references/sentinel_idle_preview.png` — PNG RGBA,
  **384×384**, ampliação **nearest-neighbor 8×** do arquivo final.
- Fonte preservada: `assets/references/sentinel_idle_generated.png` — saída
  original da ferramenta integrada, PNG RGBA **1280×1280**.
- Preparação reproduzível: `assets/references/prepare_sentinel.py` — usa Pygame
  2.6.1 já instalado no projeto; não acessa rede nem inicializa janela.

O subagente real `/root/pixel_artist` executou a produção com executor `default`,
seguindo `.codex/agents/pixel_artist.toml`. A sessão atual não disponibilizou o
tipo nativo `pixel_artist`; essa limitação não foi tratada como ativação nativa.

## Direção visual e escala

Pequeno robô de segurança, armadura azul, ombreiras angulares, capacete com faixa
ciano, núcleo luminoso e circuitos roxos. Idle voltado para o sul, com leitura
estilizada de personagem para câmera top-down. Sem arma embutida, texto ou chão.
A geração apresentou leve leitura frontal/superior de armadura, em vez de uma
projeção ortográfica estritamente vertical. É uma limitação artística do piloto
para avaliação, não uma direção já aprovada para animações ou integração.

O jogo possui hitbox circular de raio 16 px e corpo procedural com diâmetro
visual aproximado de 40 px. O novo canvas de 48 px reserva margem transparente;
a silhueta final ocupa o retângulo **(6, 4, 36, 40)**. O pivô previsto é **(24,24)**,
em escala **1×**, sem alteração da hitbox. Não há integração em código nesta missão.

## Ferramenta e preparação

Foi usada **`image_gen` integrada**, com `transparent_background=true`, sem CLI,
sem chave de API e sem chamada a API paga externa. Nenhum asset de terceiro foi
copiado ou usado como referência de imagem. A imagem-fonte original continua
preservada tanto no destino padrão da ferramenta quanto na biblioteca do projeto.

A ferramenta retornou arte maior que a resolução de jogo. A preparação técnica
autorizada fez:

1. Recorte da área com alfa ≥128.
2. Redução por nearest-neighbor, preservando proporção, para caber em 36×40.
3. Centralização em 48×48 e quantização para a paleta definida no guia de arte.
4. Alfa binário **0 ou 255**, sem bordas semitransparentes ou antialiasing.
5. Exportação da prévia por nearest-neighbor 8×, sem modificar o PNG final.

O resultado usa **11 das 12 cores** da paleta fornecida. Luminosidade é representada
por pixels de ciano e ciano claro dentro da silhueta, sem halo de fundo.

Para reproduzir se os destinos ainda não existirem:

```powershell
.\.venv\Scripts\python.exe assets/references/prepare_sentinel.py
```

O script se recusa a sobrescrever destinos existentes. `--overwrite` é uma opção
explícita para regeneração futura a partir da mesma fonte, após autorização.

## Prompt exato da geração integrada

```text
Use case: stylized-concept. Asset type: original production pixel-art sprite for the 2D top-down Pygame roguelite Cyber Defense. Create ONE SENTINEL-01 antivirus security robot idle sprite, centered, facing south, viewed from directly overhead/top-down: visible helmet crown, angular shoulder armor and plated back/torso, small limb assemblies, recognizable compact security silhouette, bright cyan hexagonal energy core, sparse one-pixel cyan/purple circuit details. Technical art direction: a true clean 48 by 48 LOGICAL PIXEL grid, native pixel-art design with a 1-pixel dark outline and deliberate solid pixel clusters. If larger output is required, show the 48x48 logical grid enlarged as uniform hard-edged square pixels with nearest-neighbor only. Occupied silhouette about 36x38 logical pixels, 5–6 logical pixels of genuinely TRANSPARENT margin, centered anchor at (24,24). No ground shadow or glow outside silhouette; luminosity is represented by 2–3 solid color steps inside core. Limited palette: dark outline #07101F, navy #10233B, #1E3D5A, #142C46, steel #365B7D, blue #3D73B8, cyan #49E9F5, pale cyan #ACF7FF, near white #E2F7FF, purple #7045A6, lilac #AC72DB, dark purple #34234F. Futuristic cybernetic robot design, sharp readable shapes, moderate neon, high contrast against dark arena. IMPORTANT: single isolated sprite only, real alpha transparency not a checkerboard, no text, no logo, no UI frame, no reference art, no multiple views, no sprite sheet, no photorealism, no smoothing, no antialiasing, no 3D render, no front-facing portrait. Original character only, do not imitate any existing game character.
```

## Referências técnicas consultadas

- [Aseprite: SpriteSize](https://www.aseprite.org/api/command/SpriteSize), para
  ampliação sem interpolação suave.
- [Aseprite: estrutura de sprites](https://www.aseprite.org/docs/sprite/), para
  convenções de dimensões, transparência e frames.

São referências técnicas; nenhuma imagem ou paleta de terceiros foi baixada.
A identidade visual e as cores vêm do projeto e da direção artística da missão.

# AgentOS — Cyber Defense

Roguelite 2D de hordas em Python e Pygame, com jogador e inimigos em pixel art
animada, arena digital de 2400×1600 e câmera suave. SENTINEL-01
é um antivírus que protege o núcleo do sistema operacional contra vírus,
malwares e processos corrompidos. XP são dados recuperados, cartas são
atualizações e poções são pacotes de reparo.

Execute na raiz do projeto, usando o ambiente já disponível:

```powershell
.\.venv\Scripts\python.exe -m game.main
```

Também é possível executar `python -m game.main` em um ambiente com Pygame instalado.

## Como jogar

A janela continua em 1100×770. O mundo mede 2400×1600, com piso fixo e câmera
suave limitada às paredes. HUD, menus e cartas permanecem na tela. As colisões
continuam em coordenadas de mundo. Os inimigos surgem a 220–480 unidades do
jogador para manter o ritmo na arena maior; quotas e atributos não mudaram.

O SENTINEL-01 utiliza o PNG original, com idle e caminhada derivados, pivô central
e oito rotações em cache. Slashes ciano/magenta são somente efeitos visuais dos
timers de ataque; não aplicam dano por frame. A minhoca segue a trajetória da
cabeça a cada 32 unidades percorridas, inclusive em cruzamentos do próprio corpo;
a cauda é desenhada por cima da cabeça nesses encontros.

Parâmetros visuais ficam em `game/visual_config.py`. Animações e tiles novos são
documentados em `assets/references/mission011/PROVENANCE.md`. A ampliação usa
nearest-neighbor; as hitboxes e os atributos das armas permanecem inalterados.

| Tecla | Ação |
|---|---|
| WASD ou setas | Mover e orientar o personagem |
| Ataque automático | A arma mira o inimigo vivo mais próximo no alcance; Espaço não é necessário |
| H | Aplicar pacote de reparo: recupera 35 HP, sem gastar com HP cheio |
| I | Abrir/fechar inventário e pausar a arena; H continua disponível |
| 1, 2, 3 ou clique na carta | Selecionar melhoria ao subir de nível |
| 1, 2, 3 na seleção de armas | Escolher Katana, Arco ou Lança |
| 1–6 no treino do Laboratório | Katana, Arco, Lança, Arco Longo, Lança de Retorno, Espada |
| Setas / A-D e Enter nas cartas | Destacar e confirmar uma melhoria |
| F2 | Alternar shake: normal, reduzido, desligado |
| F3 | Alternar partículas: normal, reduzido, desligado |
| R na tela Game Over ou Vitória | Reiniciar a partida |
| M | Voltar ao menu e escolher outro modo |
| Esc | Sair |

O menu apresenta dois modos. **Defesa:** complete as hordas 1–5, enfrente ROOTKIT
na sexta, escolha uma arma e teste por até 15 segundos ou três alvos. **Laboratório:**
complete as hordas 1–5, sem ROOTKIT, e escolha uma arma para abrir um treino de até
45 segundos. Nele, 1–6 alternam equipamentos; há nove alvos em três grupos,
sem reposição. Arco Longo compartilha os alvos do Arco, Lança de Retorno os da
Lança, e Espada os da Katana. Eliminar os nove também encerra o treino.
Ambos os modos terminam em um resultado; não há spawn infinito no laboratório.
O treino não concede XP, drops ou abates de campanha. Reinício remove os upgrades.

A quinta horda inclui uma minhoca semiboss, distinta de ROOTKIT.
As cinco hordas iniciais têm quotas de 6, 8, 10, 12 e 15 inimigos, com até dez vivos.
Os corpos independentes se separam suavemente por círculos, considerando o tamanho
e as paredes da arena. A correção é determinística, inclusive em centros idênticos,
e não altera dano, stun ou recuo. A cadeia da minhoca se desloca como um grupo;
seus segmentos não recebem separação interna. Sobreposições graves se desfazem
ao longo de alguns quadros para evitar teleporte.
Uma preparação de três segundos separa as hordas; HP e dano inimigos aumentam.
HP zero encerra a partida. O sprite e a arma indicam a orientação do personagem. A
espada aparece por 0,14 segundo, com um slash ciano animado na direção fixada no início do
golpe; seu rastro mostra o movimento. Cada ataque tem intervalo de 0,35 segundo. O contato com
inimigos causa 10 de dano, seguido por 0,8 segundo de invulnerabilidade.

Um acerto faz o inimigo recuar até 20 pixels em 0,10 segundo e o deixa atordoado
por 0,20 segundo, sem perseguir ou causar dano por contato. Nas bordas, o recuo é
limitado pela arena. O inimigo recebe um breve brilho e pontos dourados indicam o
stun. Acertos comuns deslocam a arena em até 3 pixels por 0,10 segundo e geram
hitstop de 0,04 segundo. Na minhoca, os valores são 6 pixels / 0,16 segundo e
0,07 segundo de hitstop. Atacar no vazio não inicia esses efeitos. Durante o
hitstop, a interface e os efeitos continuam; movimento, IA e cooldowns aguardam
somente o tempo restante, sem acumular delta time. HUD e inventário ficam fixos.

O impacto produz flash de aproximadamente 0,10 segundo, partículas e o dano
efetivamente causado em números flutuantes por 0,65 segundo. Barras pequenas de
HP aparecem brevemente após dano. Mortes deixam dispersão, e cada ruptura da
minhoca destaca a nova cabeça sem conceder recompensa intermediária.

Cada inimigo da campanha concede 25 XP. Inimigos comuns têm 20% de chance de
deixar um drop: 50% pacote de reparo e 50% overclock. Chefes não fazem esse sorteio.
Encoste no pacote para coletá-lo. Você começa com dois reparos e carrega até cinco.
Com estoque cheio, a coleta cura até 35 HP imediatamente. Se o HP também estiver
cheio, a poção vira dez pontos. Cada frasco é coletado uma única vez; pontos não
concedem XP. Coletas geram partículas; a conversão mostra `+10 pontos` flutuante.
O inventário apresenta um card com o mesmo sprite de frasco dos drops, nome,
quantidade e efeito de cura.

**Overclock** aumenta somente a velocidade de movimento em 25% por cinco segundos
ativos. Nova coleta renova o contador para cinco segundos, sem somar multiplicadores
ou durações. Combina com as cartas de agilidade: `220 × (1 + 0,12 × escolhas) × 1,25`.
Pausa de inventário, escolhas e hitstop não gastam o tempo do bônus.

## Cartas e progressão

O próximo nível custa `100 + 50 * (nível atual - 1)` XP; excedentes são preservados.
Não há bônus automáticos nem cura total ao subir de nível na partida. Em vez
disso, escolha uma de três cartas aleatórias distintas. Toda a simulação pausa
durante a escolha, incluindo inimigos, flechas, recuo e regeneração. Ganhos de
múltiplos níveis geram escolhas sequenciais. Não é possível usar poções nessa tela.
Ao subir de nível, a sequência `GAMEPLAY → LEVEL_UP_INTRO → LEVEL_UP_CARDS`
congela as regras imediatamente. Durante os primeiros 0,5 segundo, uma onda ciano
desloca os inimigos em até 64 px sem IA, dano ou recompensas; paredes podem limitar
o movimento. O título `LEVEL UP!` desce com easing, brilho leve e partículas digitais.
Em seguida, as cartas entram com 0,20 segundo de animação e 0,04 segundo de intervalo
entre elas (0,28 segundo no total). Só depois de todas terminarem é possível selecionar.
Entradas anteriores são descartadas. A entrada emite um som eletrônico curto, sem
reiniciar a música. Hover ou foco de teclado destacam uma carta; confirmar exibe
um aviso curto. Cada nível pendente repete a sequência, sem retomar combate entre
escolhas. Os relógios de interface, efeitos e simulação são independentes: não há
acúmulo de delta time ao continuar.

| Carta | Efeito por escolha | Limite |
|---|---|---|
| Lâmina afiada | Dano × 1,20 | 8 |
| Vitalidade | +25 HP atual e máximo | 8 |
| Passos leves | +12% da velocidade-base | 5 |
| Golpe veloz | Intervalo de ataque × 0,90 | 8 |
| Lâmina longa | +15% do alcance-base | 6 |
| Regeneração | +1 HP por pulso de 5 segundos ativos | 5 |
| Fôlego de batalha | +2 HP por cinco abates após adquirir a carta | 5 |
| Armadura | Dano recebido × 0,90 | 7 |

As melhorias duram até o fim da partida. Sem overclock, a velocidade chega a 352 px/s.
Na espada inicial, o intervalo mínimo é aproximadamente 0,151 s e o alcance máximo
é 133 px; outras armas aplicam os mesmos upgrades às suas próprias bases. O teto
de segurança é nível 36, garantindo três melhorias elegíveis em cada seleção;
o XP adicional permanece acumulado. São 51 inimigos nas cinco primeiras hordas e
52 na Defesa, incluindo ROOTKIT.

## Armas desbloqueadas

O jogador controla o movimento. O sistema escolhe o inimigo vivo mais próximo
no alcance específico da arma e captura sua direção no início de cada ciclo.
Sem alvo, a arma permanece equipada em repouso. Pausas, hitstop e cooldowns
continuam valendo. Espada, katana e lança ficam visíveis ao lado do jogador.

| Arma | Impacto relativo ao atributo de dano | Intervalo-base | Alcance-base |
|---|---|---|---|
| Katana | Dois cortes de 0,6×, em 0 e 0,10 s | 0,40 s | 70 px, cone de 100° |
| Arco | Uma flecha de 1,4×, velocidade de 400 px/s | 0,50 s | 500 px |
| Lança | Uma estocada de 1,2×, impacto em 0,08 s | 0,42 s | 105 px, largura de 14 px |
| Arco Longo | Flecha de 1,4× perfura até três inimigos distintos | 0,50 s | 500 px, velocidade 400 px/s |
| Lança de Retorno | Arremesso de 1,2×; recuperação manual causa giro de 1,2× | 0,42 s após recuperar | Arremesso 240 px; giro 105 px |

A Defesa permite escolher uma única arma após o chefe. O Laboratório permite trocar
durante o treino. Trocar cancela golpes pendentes e preserva o cooldown. Cada impacto
atinge uma vez por alvo; flechas comuns param no primeiro alvo e não atingem SENTINEL-01.
Flechas do Arco Longo registram até três inimigos distintos; os segmentos de uma
mesma minhoca contam como uma criatura, sem perder várias cabeças pela mesma flecha.

A Lança de Retorno para no primeiro impacto, na parede ou no limite do arremesso.
Enquanto estiver no mundo, não é possível arremessar outra. Encostar nela parada
antes de três segundos recupera a arma e aplica um giro de 360 graus uma única
vez por inimigo. Aos três segundos ativos desde o lançamento ela retorna
automaticamente, com animação e sem giro. Inventário, cartas e demais pausas não
consomem esse tempo. Recuperar inicia novamente o cooldown; trocar de arma limpa
a lança, giros, golpes pendentes e projéteis do jogador, preservando seus upgrades.

Cada seleção de level up possui chance configurável de **8%** de incluir uma carta
de arma no lugar de uma das três cartas. As escolhas continuam distintas. O aviso
**ATENÇÃO: VOCÊ PERDERÁ SUA ARMA ATUAL.** aparece na carta, junto do sprite e tipo.
O peso de cada evolução é 0,25 contra 1 de cada arma comum elegível. A arma atual
não aparece; Arco comum não é oferecido para quem usa Arco Longo, nem Lança comum
para quem usa Lança de Retorno. Trocas entre famílias continuam voluntárias.
Chance e peso ficam em `BalanceConfig`, em `game/balance.py`.

## Inimigos

- Espadachim: antecipa um golpe frontal; saia do cone ou interrompa com um acerto.
- Arqueiro: procura distância e sinaliza a direção antes de disparar. Desvie das flechas.
- Minhoca: seis segmentos de 10 HP. Acertar qualquer segmento causa um impacto na
  cabeça atual; ao esgotar seu HP, o próximo vira cabeça. O excesso de dano não
  destrói outra cabeça no mesmo impacto. Só o último segmento concede XP e abate.
- ROOTKIT: processo protegido exclusivo da sexta horda da Defesa, com 48 HP e
  padrões alternados de cone e rajada radial. Possui antecipação de 0,65 s e resiste
  a stun, recuo e interrupção; continua recebendo dano, flash e efeitos de impacto.

## Sprites e animações dos inimigos

A biblioteca em `assets/sprites/enemies/` contém 36 PNGs com 139 frames: vírus
básico, espadachim, arqueiro, cabeça/corpo/cauda da minhoca e ROOTKIT. O manifesto
relaciona estados, dimensões, pivôs e durações. Os arquivos usam transparência
binária e orientação-base leste; oito rotações nítidas são guardadas em cache.
O atlas de inspeção fica em `assets/references/mission010/enemy_atlas.png`.

Idle e movimento acompanham o tempo de gameplay. Preparação, golpe e dano
observam os timers existentes, sem disparar dano ou projéteis pela animação.
Morte e ruptura usam registros visuais depois da remoção lógica do inimigo;
não repetem XP ou drops. A promoção de segmento da minhoca troca o sprite por
cabeça e anima sua transformação. ROOTKIT mantém seus avisos de ataque durante
o flash de dano, além da barra de HP e dos padrões existentes.

Colisões, alcance, HP e balanceamento continuam definidos pela lógica. Ponta de
arma, espinhos e brilho decorativo não ampliam a hitbox. Se o manifesto ou um
PNG estiver indisponível, o jogo usa o desenho geométrico de fallback. A procura
dos arquivos independe do diretório de trabalho e não há leitura de PNG por frame.

O PNG original do jogador foi integrado na Missão 011 por meio dos sheets idle e
caminhada derivados, sem substituir o arquivo original. A direção do corpo usa
rotações nearest-neighbor em cache e o centro visual mantém a hitbox anterior.
As referências, prompts e preparação reproduzível da arte inimiga estão em
`assets/references/mission010/PROVENANCE.md`; os detalhes de todos os sheets,
em `assets/sprites/enemies/README.md`.

## Calibrar efeitos e áudio

F2 alterna shake entre 100%, 50% e desligado. F3 faz o mesmo com partículas.
As opções ficam visíveis no inventário e são mantidas ao reiniciar a partida.
Números de dano e avisos de ataque continuam visíveis mesmo com partículas desligadas.

Os valores iniciais ficam em `game/settings.py`: `shake_scale`, `particle_scale`,
`max_particles` (160), `max_texts` (32), `audio_enabled` e `volume` (0,18).
Intensidades são limitadas a 0–1; os tetos absolutos são 320 partículas e 64 textos.
Para jogar sem som, defina `audio_enabled=False`. Sons curtos são gerados em
memória; falha ou ausência do dispositivo desativa somente o áudio.

Para a **música autoral**, coloque seu arquivo em `assets/audio/theme.ogg` ou
`assets/audio/theme.mp3` e inicie o jogo. Nenhuma faixa substituta é gerada.
`music_volume` e `music_enabled` em `game/settings.py` controlam a reprodução.
A música toca em loop e não reinicia ao mudar de horda. Se não houver arquivo ou
dispositivo, o menu mostra uma informação discreta e o jogo continua normalmente.
O diretório já contém instruções em `assets/audio/README.md`.

Chance de drops, overclock, parâmetros de ROOTKIT, armas e duração dos treinos ficam
centralizados em `game/balance.py`.
Os valores da separação e da sequência de level up ficam em `game/feel_config.py`.

A meta é manter a atualização em 60 FPS, com limites de efeitos e reutilização de
superfícies e fontes. Isso não constitui medição de desempenho em hardware comum.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes gráficos usam SDL `dummy`, processos isolados e saída controlada.
Isso não substitui jogar com uma janela real. Para validar visualmente: caminhe
até as bordas, ataque de frente, colete um frasco, abra o inventário, cure com H,
alcance quatro abates para escolher uma carta por tecla ou mouse. Confirme a pausa
dos inimigos durante a introdução e a escolha. Antes das cartas aparecerem, tente
1/2/3 ou clique: nada deve ser selecionado. Confira o texto descendo, a onda, a
entrada escalonada e um único som; selecione após a animação e confira a retomada
sem salto. Aproxime um grupo de uma parede para observar a separação suave; stun
e knockback devem continuar funcionando. Teste os dois resultados de coleta com cinco
poções (cura ou pontos), avance hordas, encontre a minhoca na quinta, deixe o HP
zerar e reinicie com R. Na Defesa, enfrente ROOTKIT na sexta e escolha uma arma.
No Laboratório, teste 1–6 após a quinta; confira golpes automáticos, perfuração,
estocada, arremesso, recuperação manual com giro e retorno automático sem giro.
Após o treino, R reinicia no mesmo modo; M volta ao menu.

## Organização

- `game/main.py`: entrada, eventos e tempo dos quadros.
- `game/world.py`: simulação, spawn, recompensas e estado da partida.
- `game/cards.py`, `game/waves.py`: melhorias e quotas de hordas.
- `game/swordsman.py`, `game/archer.py`, `game/worm.py`: comportamentos inimigos.
- `game/projectiles.py`, `game/items.py`: colisão de flechas e coleta.
- `game/player.py`, `game/enemies.py`: entidades e movimentação.
- `game/combat.py`, `game/inventory.py`: alcance, dano e consumíveis.
- `game/progression.py`: XP e níveis, sem dependência gráfica.
- `game/interface.py`: arena, personagens, efeitos e painéis.
- `game/card_ui.py`, `game/enemy_render.py`: escolhas e apresentação dos inimigos.
- `game/enemy_assets.py`, `game/enemy_animation.py`: cache de PNGs e seleção pura de frames.
- `game/effects.py`, `game/effect_render.py`: relógio visual, eventos e renderização de FX.
- `game/settings.py`, `game/audio.py`: intensidade dos efeitos e sons opcionais.
- `game/balance.py`, `game/modes.py`: parâmetros e modos de campanha.
- `game/weapons.py`, `game/weapon_render.py`: impactos, equipamentos e animações.
- `game/boss.py`: ROOTKIT e seus padrões de ataque.
- `game/drops.py`: sorteio e coleta de reparos e overclock.
- `game/music.py`, `game/cyber_ui.py`: música autoral opcional, menu e seleção de armas.
- `game/physics.py`: separação determinística e deslocamentos limitados pela arena.
- `game/levelup.py`, `game/levelup_render.py`: máquina de estados, onda e introdução.
- `game/feel_config.py`: durações, intensidades e easing do polimento.

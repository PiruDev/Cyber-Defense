# MISSÃO 010 — proveniência da biblioteca inimiga

Produção pelo subagente **nativo `pixel_artist`**, `/root/pixel_artist_native`.
Foram lidos AGENTS.md, a missão, ART_STYLE_GUIDE.md, as entidades e os estados
reais antes de criar recursos. A execução anterior por executor genérico não
produziu os arquivos desta entrega; a produção documentada aqui ocorreu após a
retomada e ativação do papel nativo.

## Ferramentas e autoria

Cinco fontes originais foram geradas com a ferramenta **image_gen integrada**,
uma por família: vírus básico, espadachim, arqueiro, minhoca e ROOTKIT. Não houve
CLI de geração, chave de API, API externa paga ou cópia de sprite de outro jogo.
Cada prompt completo está em `generation_prompts.json`; as imagens-fonte ficam
preservadas como `basic_source.png`, `swordsman_source.png`, `archer_source.png`,
`worm_source.png` e `rootkit_source.png`.

A ferramenta produziu fontes maiores que os canvases do jogo. A etapa técnica
autorizada, reproduzível em `build_enemy_sheets.py`, usa apenas Pygame 2.6.1 já
instalado. Recorta a silhueta, reduz por nearest-neighbor, aplica paleta curta e
alfa binário e gera poses por deslocamentos inteiros de aletas, placas, luzes,
corpos e fragmentos. Não modifica a fonte nem abre janela ou acessa rede.

**Adaptação artística deliberada:** a fonte do espadachim saiu com aparência
frontal/oblíqua. Seus pixels não foram usados na produção. A armadura, coroa do
capacete, visor leste, ombros, esteiras, circuitos e lâmina foram redesenhados na
grade de 64×64 com formas de pixels originais, seguindo apenas a identidade
corrompida planejada. Assim evitou-se rotacionar um retrato frontal como se fosse
um sprite visto de cima. A fonte permanece como registro do conceito.

## Preparação e animações

Os 36 sheets contêm 139 frames reais. As células são estáveis, com pivôs centrais;
a frente-base é leste. Cada família possui até doze cores registradas no
manifesto. As bordas de todas as células ficam transparentes; alfa é somente
0 ou 255, sem antialiasing no arquivo final.

O idle pulsa somente luzes já presentes no núcleo, preservando materiais e
contornos. Move desloca aletas, esteiras ou anéis por pixels inteiros. Windup
carrega o emissor ou levanta a espada; attack mostra a liberação/golpe e retorno.
Hurt oferece dois frames de feedback. Death e rupture separam a silhueta em
fragmentos digitais, com frames finais ainda não vazios; o runtime encerra a
representação ao terminar a duração. New_head faz a transição corpo→cabeça.

O ataque é visual: a aplicação de dano continua exclusivamente na lógica atual.
O runtime deve conservar telegraphs, timers, hitstop, stun e flash. Apenas os
inimigos são candidatos à integração; a arte do SENTINEL-01 continua preservada.

Para reproduzir em uma cópia com destinos ainda ausentes:

```powershell
.\.venv\Scripts\python.exe assets/references/mission010/build_enemy_sheets.py
```

O script recusa arquivos de destino existentes. `--overwrite` é uma opção
explícita de reconstrução das próprias saídas, após autorização. Não usá-la para
substituir arte futuramente aprovada sem revisão.

## Verificações executadas pelo artista

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_enemy_assets.py -v
```

**Quatro testes passaram** após a exportação final (0,356 s). Confirmam esquema,
sete tipos, estados, arquivos, dimensões das células, PNG RGBA, alfa binário,
margens, frames preenchidos e diversidade, além do hash do jogador preservado.
O QA independente fará o gate antes da integração do desenvolvedor.

O atlas `enemy_atlas.png` foi inspecionado durante a produção. Um primeiro teste
de pulsação preenchia o núcleo com hachura; foi corrigido antes da entrega. A
transformação da minhoca também foi refeita para mostrar corpo e mandíbulas em
vez de um disco luminoso opaco. O espadachim atual foi desenhado na grade, conforme
descrito acima. Os PNGs finais aguardam avaliação de leitura na arena.

## Limitações honestas

São animações compactas e estilizadas, com deformações de pixels e poses de arma;
não são animações esqueléticas ou desenhos independentes em oito direções.
O runtime rotaciona a base leste em passos de 45° por nearest-neighbor, mantendo
telegraphs no ângulo lógico real. A resolução pequena simplifica circuitos e
detalhes. A ortografia é estilizada; bordas e apêndices são decorativos e não
redefinem hitboxes. O atlas não equivale a um playtest humano prolongado.

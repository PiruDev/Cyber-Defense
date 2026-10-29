# Cyber Defense no navegador

O jogo continua em Python/Pygame. Pygbag empacota o mesmo runtime para WebAssembly; o launcher em `web/` incorpora o jogo real em `game/index.html`. O loop `main_async` cede controle ao navegador a cada quadro. A execução desktop continua por `python -m game.main`.

## Gerar o pacote

Use Python 3.12 ou 3.13 e um ambiente virtual (validado localmente em 3.13;
o workflow usa 3.12). Na raiz do projeto:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-web.txt
.venv/Scripts/python.exe scripts/build_web.py
```

No Linux/macOS use `python` do ambiente virtual. O template oficial Pygbag 0.9.3 está versionado em `web/pygbag.tmpl` ([origem](https://pygame-web.github.io/cdn/0.9.3/default.tmpl)), permitindo empacotar sem rede após instalar as dependências. A adaptação usa paleta AgentOS, mensagens em português, proporção nativa e permissões mínimas para o iframe auxiliar. A licença MIT upstream acompanha o ZIP em `PYGBAG_LICENSE.txt`. O navegador precisa alcançar o CDN do runtime Pygbag; este pacote não é uma distribuição offline completa. Não usa API paga, chave nem o script antigo de API.

Saídas: `build/web-src/` (staging descartável), `dist/web/` (site estático) e `dist/cyber-defense-web.zip` (conteúdo do site na raiz do ZIP). `--stage-only` permite auditar os arquivos antes do build. O script recria somente seus diretórios gerados.

O staging contém exclusivamente `game/*.py`, PNGs de `assets/sprites/{enemies,player,weapons,environment}`, o manifesto de inimigos e, quando presente, `assets/audio/theme.ogg` (preferido) ou `theme.wav` como alternativa PCM. Apenas uma versão da música é incluída. Referências de arte, testes, ambientes virtuais, arquivos `.env`, chaves e `agentos_api_antigo.py` ficam fora. Não são seguidos links simbólicos. Música é opcional e não é baixada pelo build. O otimizador Pygbag fica desativado para preservar os sprites aprovados.

## Testar localmente

```powershell
.venv/Scripts/python.exe -m http.server 8000 --directory dist/web
```

Abra `http://localhost:8000/`, clique em **Iniciar sistema**, confirme o início no runtime e clique no jogo para focar o teclado. O primeiro carregamento pode demorar enquanto o navegador baixa Python/Pygame. Não abra pelo protocolo `file://`.

O launcher preserva a proporção 1100×770 e oferece tela cheia. Todos os caminhos do site são relativos, inclusive o iframe, para funcionar em `/nome-do-repositorio/`. Jogue em computador com teclado: WASD/setas movem; combate automático; 1–6 selecionam; Enter confirma; I abre inventário; H usa poção; M abre menu; R reinicia ao terminar; F2/F3 ajustam efeitos. Mobile exibe o site, mas requer teclado físico. Áudio depende de interação e das políticas do navegador.

Servidor de desenvolvimento fornecido pelo Pygbag, após gerar o staging:

```powershell
.venv/Scripts/python.exe -m pygbag --no_opt --disable-sound-format-error --template web/pygbag.tmpl --icon assets/sprites/player/sentinel_idle.png build/web-src
```

O servidor padrão usa a porta 8000; se ela estiver ocupada, finalize o servidor
anterior ou utilize a opção de porta do Pygbag. Para a página completa, use o
servidor HTTP de `dist/web` acima. O ponto de entrada exigido pelo Pygbag é
`build/web-src/main.py`, gerado a partir de `web/entry.py`.

## Música fornecida e validação local

`Firewall_8bit.wav` foi integrado como `theme.ogg`, mantendo o original intacto.
O loop usa velocidade fixa de 0,8×, com emenda por crossfade.
A altura acompanha a redução de velocidade; não há processamento de áudio
durante gameplay. Consulte `assets/audio/README.md` para reproduzir a preparação.

Validação executada: 221 testes passaram, smokes SDL dummy desktop/async,
decodificação OGG e reprodução pelo mixer, recursos HTTP em subdiretório e
integridade do ZIP. A automação do Edge foi interrompida pela proteção da
ferramenta, que não conseguiu identificar a URL atual com confiança. Não houve
playtest WebAssembly em navegador real. Teclado, tela cheia, autoplay e fluidez
no navegador ainda precisam de conferência manual; os testes CPython/SDL não
comprovam esses comportamentos no WebAssembly.

## GitHub Pages — publicação manual

Nenhuma publicação foi executada ao preparar estes arquivos. Envie o código a um repositório GitHub quando desejar. Em **Settings → Pages**, selecione **GitHub Actions** como fonte. Em **Actions → Cyber Defense — build e Pages manual → Run workflow**:

- Deixe `publish` desligado para somente gerar e baixar o ZIP como artefato.
- Ligue `publish` para solicitar build e deploy no Pages. Se o ambiente `github-pages` exigir aprovação, conclua-a no GitHub.

O workflow responde apenas a `workflow_dispatch`; push e pull request não disparam deploy. Em hospedagem estática alternativa, descompacte o ZIP e sirva a pasta por HTTP(S), mantendo a estrutura. O runtime Pygbag é carregado por HTTPS, inclusive em subdiretórios.

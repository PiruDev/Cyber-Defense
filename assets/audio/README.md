# Música autoral de Cyber Defense

`theme.ogg` e `theme.wav` foram preparados a partir de `Firewall_8bit.wav`,
fornecido pelo usuário. O original em Downloads não foi alterado. O loop final
usa velocidade fixa de 0,8× em todas as repetições. A emenda usa crossfade de
0,75 s. A redução de velocidade também reduz a altura, como no efeito slowed
tradicional, sem alternância de velocidade.

O processamento acontece offline: o jogo apenas reproduz uma faixa em loop,
sem DSP por frame ou reinício entre hordas. OGG (~2,38 MB) é distribuído no build
web; WAV PCM16 é mantido para reprocessamento/verificação. `theme.json` registra
o hash da fonte e os parâmetros. Não há música de terceiros ou substituta.

Para repetir a preparação, na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m pip install imageio-ffmpeg==0.7.0
.\.venv\Scripts\python.exe scripts/prepare_theme.py "C:\Users\gillo\Downloads\Firewall_8bit.wav" --ogg
```

O conversor é somente uma ferramenta de desenvolvimento; não entra no jogo
nem no pacote web. Para gerar apenas WAV, omita `--ogg` e não instale o conversor.

Uma faixa alternativa pode usar `theme.ogg`, `theme.mp3` ou `theme.wav`.
`theme.ogg` tem prioridade. A faixa é carregada uma vez e
reproduzida em loop durante a sessão.

A ausência do arquivo mantém o jogo funcionando sem música. Nenhuma faixa
substituta, gerada ou de terceiros é incluída. O volume e a ativação são
controlados por `music_enabled` e `music_volume` em `game/settings.py`. No
navegador, reprodução só é solicitada após interação no jogo. Ausência de
dispositivo de áudio desativa somente o som.

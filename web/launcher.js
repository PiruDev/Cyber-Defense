"use strict";
const start = document.getElementById("start");
const game = document.getElementById("game");
const status = document.getElementById("status");
const fullscreen = document.getElementById("fullscreen");
start.addEventListener("click", () => {
  document.getElementById("gate").hidden = true;
  game.hidden = false;
  const target = new URL(game.dataset.src, window.location.href);
  const buffer = new URLSearchParams(window.location.search).get("audio_buffer");
  if (["512", "1024", "2048"].includes(buffer)) target.searchParams.set("audio_buffer", buffer);
  game.src = target.href;
  fullscreen.disabled = false;
  status.textContent = "Carregando Python e Pygame… confirme o início dentro do jogo e clique para focar o teclado.";
  game.focus();
});
game.addEventListener("load", () => {
  if (!game.src) return;
  status.textContent = "Página do jogo carregada • aguardando runtime • confirme o início dentro do jogo e clique para focar";
  game.focus();
});
fullscreen.addEventListener("click", async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.getElementById("viewport").requestFullscreen();
    game.focus();
  } catch (_) {
    status.textContent = "Tela cheia indisponível neste navegador. Use o link para abrir o jogo diretamente.";
  }
});

"""Ponto de entrada WebAssembly; o loop cooperativo pertence ao jogo."""
import asyncio
import pygame  # Declara ao preloader Pygbag a dependência WebAssembly.

from game.main import main_async

asyncio.run(main_async())

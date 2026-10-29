"""Build Pygbag isolado: somente runtime permitido entra no pacote público."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile

PYGBAG_VERSION = "0.9.3"
SPRITE_GROUPS = ("enemies", "player", "weapons", "environment")


def _regular_file(path: Path, root: Path) -> bool:
    """Recusa links inclusive em diretórios ancestrais."""
    return (path.is_file() and path.resolve().is_relative_to(root.resolve())
            and not any(part.is_symlink() for part in (path, *path.parents)))


def _reset_generated(path: Path, project_root: Path) -> None:
    if not path.resolve().is_relative_to(project_root.resolve()):
        raise ValueError(f"Diretório gerado fora do projeto: {path}")
    allowed = (project_root / "build" / "web-src", project_root / "dist" / "web")
    if path.resolve() not in tuple(item.resolve() for item in allowed):
        raise ValueError(f"Diretório gerado não autorizado: {path}")
    ancestors = (path, *path.parents)
    if any(part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction())
           for part in ancestors if part != project_root and part.is_relative_to(project_root)):
        raise ValueError(f"Não substituímos links: {path}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def stage_project(project_root: Path, staging: Path) -> list[str]:
    project_root = project_root.resolve()
    _reset_generated(staging, project_root)
    sources = list((project_root / "game").glob("*.py"))
    for group in SPRITE_GROUPS:
        sources.extend((project_root / "assets" / "sprites" / group).rglob("*.png"))
    sources.append(project_root / "assets/sprites/enemies/manifest.json")
    audio = project_root / "assets/audio"
    # OGG menor tem prioridade: nunca distribuir duas cópias da mesma música.
    sources.append(audio / ("theme.ogg" if (audio / "theme.ogg").is_file() else "theme.wav"))
    copied = []
    for source in sorted(sources):
        if not _regular_file(source, project_root):
            continue
        relative = source.relative_to(project_root)
        target = staging / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied.append(relative.as_posix())
    if "game/main.py" not in copied:
        raise RuntimeError("game/main.py ausente no staging")
    # Pacote explícito também funciona no importador WebAssembly.
    (staging / "game/__init__.py").touch()
    shutil.copyfile(project_root / "web/entry.py", staging / "main.py")
    return copied


def validate_export(export_dir: Path) -> None:
    for required in ("index.html", "style.css", "launcher.js", "game/index.html"):
        if not (export_dir / required).is_file():
            raise RuntimeError(f"Exportação incompleta: {required}")
    if not list((export_dir / "game").glob("*.apk")):
        raise RuntimeError("Pacote real do jogo Pygbag ausente")
    for path in export_dir.rglob("*"):
        if path.is_file() and (path.is_symlink() or path.name.startswith(".env")
                              or path.suffix.lower() in (".pem", ".key")):
            raise RuntimeError(f"Arquivo proibido na exportação: {path.name}")


def build(project_root: Path) -> Path:
    project_root = project_root.resolve()
    version = importlib.metadata.version("pygbag")
    if version != PYGBAG_VERSION:
        raise RuntimeError(f"Instale requirements-web.txt (Pygbag {PYGBAG_VERSION}; encontrado {version})")
    staging = project_root / "build/web-src"
    copied = stage_project(project_root, staging)
    subprocess.run([sys.executable, "-m", "pygbag", "--build", "--no_opt",
                    "--disable-sound-format-error", "--app_name", "cyber-defense",
                    "--title", "Cyber Defense", "--width", "1100", "--height", "770",
                    "--template", str(project_root / "web/pygbag.tmpl"),
                    "--icon", str(project_root / "assets/sprites/player/sentinel_idle.png"),
                    str(staging)],
                   cwd=project_root, check=True)
    generated = staging / "build/web"
    if not (generated / "index.html").is_file():
        raise RuntimeError("Pygbag não gerou build/web/index.html")
    destination = project_root / "dist/web"
    _reset_generated(destination, project_root)
    shutil.copytree(generated, destination / "game")
    for name in ("index.html", "style.css", "launcher.js", "PYGBAG_LICENSE.txt"):
        shutil.copyfile(project_root / "web" / name, destination / name)
    (destination / ".nojekyll").touch()
    (destination / "build-manifest.json").write_text(
        json.dumps({"pygbag": version, "runtime_files": copied}, indent=2), encoding="utf-8")
    validate_export(destination)
    archive = project_root / "dist/cyber-defense-web.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as package:
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                package.write(path, path.relative_to(destination).as_posix())
    print(f"Site: {destination}\nZIP: {archive}\nRuntime: {len(copied)} arquivos permitidos")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage-only", action="store_true", help="Valida e prepara somente fontes runtime")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.stage_only:
        print("\n".join(stage_project(root, root / "build/web-src")))
    else:
        build(root)


if __name__ == "__main__":
    main()

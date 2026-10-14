"""Gera o ícone do aplicativo (assets/icon.ico) usando Pillow."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


def make_icon(out: Path) -> None:
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # fundo arredondado
    d.rounded_rectangle([8, 8, size - 8, size - 8], radius=52, fill=(47, 107, 255, 255))
    # mala / pasta de trabalho (briefcase)
    d.rounded_rectangle([56, 104, size - 56, 196], radius=18, fill=(255, 255, 255, 255))
    d.rounded_rectangle([104, 76, size - 104, 112], radius=12, fill=(230, 234, 242, 255))
    d.rectangle([56, 140, size - 56, 150], fill=(47, 107, 255, 255))
    d.rounded_rectangle([118, 132, 138, 158], radius=6, fill=(47, 107, 255, 255))
    # lupa
    d.ellipse([150, 150, 210, 210], outline=(255, 255, 255, 255), width=14)
    d.line([200, 200, 224, 224], fill=(255, 255, 255, 255), width=16)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, sizes=[(16, 16), (32, 32), (48, 48), (64, 64),
                         (128, 128), (256, 256)])
    print(f"Ícone gerado: {out}")


if __name__ == "__main__":
    make_icon(Path(__file__).resolve().parent.parent / "assets" / "icon.ico")

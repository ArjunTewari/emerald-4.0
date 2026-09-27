from __future__ import annotations

import math
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "images"
ASSETS.mkdir(parents=True, exist_ok=True)

SOURCE = Path(r"C:\Users\hp\Downloads\Starline Tech.png")
SOURCE_SQUARE = Path(r"C:\Users\hp\Downloads\Starline Tech Logo.png")

INK = np.array([29, 29, 27], dtype=np.float32)
GRAPHITE = np.array([45, 45, 42], dtype=np.float32)
SILVER = np.array([213, 212, 209], dtype=np.float32)
PAPER = np.array([244, 243, 241], dtype=np.float32)
RED = np.array([227, 34, 25], dtype=np.float32)


def alpha_from_logo(image: Image.Image, crop: tuple[int, int, int, int]) -> Image.Image:
    region = image.crop(crop).convert("RGB")
    arr = np.asarray(region, dtype=np.float32)
    luminance = arr.mean(axis=2)
    border = np.concatenate((arr[0], arr[-1], arr[:, 0], arr[:, -1]), axis=0)
    background_luminance = float(np.median(border.mean(axis=1)))
    if background_luminance < 128:
        alpha = np.clip((luminance - background_luminance - 18) / max(1, 232 - background_luminance) * 255, 0, 255)
    else:
        alpha = np.clip((background_luminance - luminance - 18) / max(1, background_luminance - 24) * 255, 0, 255)
    alpha = alpha.astype(np.uint8)
    bbox = Image.fromarray(alpha).getbbox()
    if not bbox:
        raise RuntimeError("No logo pixels found")
    return Image.fromarray(alpha).crop(bbox)


def colored_mark(alpha: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    out = Image.new("RGBA", alpha.size, (*color, 0))
    out.putalpha(alpha)
    return out


def build_brand_assets() -> dict[str, Path]:
    source = Image.open(SOURCE).convert("RGB")

    # Keep the supplied custom STARLINE letterforms and textured half-sun intact.
    if source.width > 2500:
        lockup_crop = (1020, 380, 2780, 1360)
        mark_crop = (1450, 400, 2310, 890)
    else:
        lockup_crop = (560, 34, 1030, 285)
        mark_crop = (690, 42, 890, 182)
    lockup_alpha = alpha_from_logo(source, lockup_crop)
    lockup_dark = colored_mark(lockup_alpha, tuple(INK.astype(np.uint8)))
    lockup_light = colored_mark(lockup_alpha, tuple(PAPER.astype(np.uint8)))

    dark_path = ASSETS / "starline-lockup-dark.png"
    light_path = ASSETS / "starline-lockup-light.png"
    lockup_dark.save(dark_path, optimize=True)
    lockup_light.save(light_path, optimize=True)

    # Separate semicircle for small marks and motion references.
    mark_alpha = alpha_from_logo(source, mark_crop)
    mark_dark = colored_mark(mark_alpha, tuple(INK.astype(np.uint8)))
    mark_light = colored_mark(mark_alpha, tuple(PAPER.astype(np.uint8)))
    mark_red = colored_mark(mark_alpha, tuple(RED.astype(np.uint8)))
    mark_dark.save(ASSETS / "starline-mark-dark.png", optimize=True)
    mark_light.save(ASSETS / "starline-mark-light.png", optimize=True)
    mark_red.save(ASSETS / "starline-mark-red.png", optimize=True)

    # Compact light-background brand asset matching the red-accent system.
    square = Image.new("RGBA", (512, 512), tuple(PAPER.astype(np.uint8)) + (255,))
    square_lockup = lockup_dark.copy()
    square_lockup.thumbnail((420, 310), Image.Resampling.LANCZOS)
    square.alpha_composite(square_lockup, ((512 - square_lockup.width) // 2, (512 - square_lockup.height) // 2 - 8))
    square.convert("RGB").save(ASSETS / "starline-logo-source.png", optimize=True)
    square.convert("RGB").save(ASSETS / "starline-social.png", optimize=True)
    square.resize((180, 180), Image.Resampling.LANCZOS).convert("RGB").save(ASSETS / "apple-touch-icon-starline.png", optimize=True)

    favicon = Image.new("RGBA", (96, 96), tuple(PAPER.astype(np.uint8)) + (255,))
    red_favicon_mark = mark_red.copy()
    red_favicon_mark.thumbnail((72, 48), Image.Resampling.LANCZOS)
    favicon.alpha_composite(red_favicon_mark, ((96 - red_favicon_mark.width) // 2, (96 - red_favicon_mark.height) // 2))
    favicon.save(ASSETS / "favicon-starline.png", optimize=True)

    return {"dark": dark_path, "light": light_path}


def noise_field(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    field = np.zeros((height, width), dtype=np.float32)
    weights = ((48, 0.46), (104, 0.34), (220, 0.20))
    for size, weight in weights:
        small_w = max(2, math.ceil(width / size))
        small_h = max(2, math.ceil(height / size))
        small = Image.fromarray((rng.random((small_h, small_w)) * 255).astype(np.uint8))
        large = small.resize((width, height), Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(size / 18))
        field += np.asarray(large, dtype=np.float32) / 255 * weight
    fine = rng.random((height, width), dtype=np.float32)
    field = field * 0.82 + fine * 0.18
    field = (field - field.min()) / max(1e-6, field.max() - field.min())
    return field


def make_motion_frame(
    field: np.ndarray,
    sparkle: np.ndarray,
    phase: float,
    width: int,
    height: int,
) -> np.ndarray:
    yy, xx = np.mgrid[0:height, 0:width]
    cx, cy, radius = int(width * 0.64), int(height * 0.75), int(height * 0.45)
    circle = ((xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2) & (yy <= cy)

    # Smoothly reveal and withdraw bright granular islands for a seamless loop.
    reveal = 0.5 - 0.5 * math.cos(phase * math.tau)
    directional = ((xx - (cx - radius)) / (2 * radius) - (yy - (cy - radius)) / radius) * 0.09
    threshold = 0.985 - reveal * 0.66 + directional
    softness = np.clip((field - threshold) / 0.095, 0, 1)
    specks = (sparkle > (0.9992 - reveal * 0.065)).astype(np.float32)
    white_amount = np.clip(softness * 0.88 + specks * 0.65, 0, 1) * circle

    base = np.zeros((height, width, 3), dtype=np.float32)
    vertical = np.linspace(0, 1, height, dtype=np.float32)[:, None, None]
    horizontal = np.linspace(0, 1, width, dtype=np.float32)[None, :, None]
    base[:] = INK
    base += vertical * 3 + horizontal * 2

    # Quiet architectural grid, only just visible.
    grid = ((xx % 120 == 0) | (yy % 120 == 0)).astype(np.float32)[..., None]
    base = base * (1 - grid * 0.035) + SILVER * grid * 0.035

    texture = (field - 0.5)[..., None] * 20
    circle_color = np.clip(GRAPHITE + texture, 24, 72)
    mask3 = circle[..., None]
    base = np.where(mask3, circle_color, base)
    white3 = white_amount[..., None]
    base = base * (1 - white3) + SILVER * white3

    # Red horizon line breathes with the emergence but remains restrained.
    line_y = cy + 7
    half = int(radius * (0.28 + reveal * 0.65))
    left, right = max(0, cx - half), min(width, cx + half)
    base[line_y : line_y + 4, left:right] = RED

    vignette = 1 - 0.20 * np.clip(((xx - width / 2) / (width * 0.72)) ** 2 + ((yy - height / 2) / (height * 0.72)) ** 2, 0, 1)
    base *= vignette[..., None]
    return np.clip(base, 0, 255).astype(np.uint8)


def build_motion_video(lockup_light: Path) -> None:
    width, height = 1280, 800
    fps, seconds = 24, 6
    frame_count = fps * seconds
    rng = np.random.default_rng(20240927)
    field = noise_field(width, height, rng)
    sparkle = rng.random((height, width), dtype=np.float32)

    mp4_path = ASSETS / "starline-hero-motion.mp4"
    webm_path = ASSETS / "starline-hero-motion.webm"
    poster_path = ASSETS / "starline-hero-poster.webp"
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "-",
        "-an",
        "-vcodec", "libx264",
        "-preset", "slow",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(mp4_path),
    ]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    poster = None
    assert process.stdin is not None
    for index in range(frame_count):
        phase = index / frame_count
        frame = make_motion_frame(field, sparkle, phase, width, height)
        if index == frame_count // 2:
            poster = Image.fromarray(frame)
        process.stdin.write(frame.tobytes())
    process.stdin.close()
    stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    if process.wait() != 0:
        raise RuntimeError(stderr)

    subprocess.run(
        [
            ffmpeg, "-y", "-i", str(mp4_path), "-an", "-c:v", "libvpx-vp9",
            "-crf", "35", "-b:v", "0", "-row-mt", "1", str(webm_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert poster is not None
    poster.save(poster_path, "WEBP", quality=90, method=6)

    # Social preview combines the live visual language with the exact wordmark.
    og = poster.resize((1200, 750), Image.Resampling.LANCZOS).crop((0, 60, 1200, 690)).convert("RGBA")
    shade = Image.new("RGBA", og.size, (0, 0, 0, 66))
    og.alpha_composite(shade)
    lockup = Image.open(lockup_light).convert("RGBA")
    lockup.thumbnail((430, 265), Image.Resampling.LANCZOS)
    og.alpha_composite(lockup, (70, (630 - lockup.height) // 2))
    accent = ImageDraw.Draw(og)
    accent.rectangle((0, 0, 12, 630), fill=tuple(RED.astype(np.uint8)) + (255,))
    og.convert("RGB").save(ASSETS / "og-starline.jpg", quality=92, optimize=True)


if __name__ == "__main__":
    assets = build_brand_assets()
    build_motion_video(assets["light"])
    print("Built Starline brand assets and hero motion video.")

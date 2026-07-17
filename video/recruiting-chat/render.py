#!/usr/bin/env python3
"""Render a vertical recruiting-chat comedy video.

The project intentionally avoids nicknames/IDs. The male avatar is the user's
provided WeChat avatar. The female avatar is a casual floral-photo style image.
The soundtrack is original: procedural beat + synthetic TTS.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import math
import os
import random
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
AUDIO_DIR = BUILD / "audio"
ASSETS = ROOT / "assets"

W, H = 1080, 1920
FPS = 30
SR = 44100
FONT_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


@dataclass
class Line:
    speaker: str  # f / m
    text: str
    rate: str = "+32%"
    gap_after: float = 0.11
    emphasis: bool = False
    start: float = 0.0
    duration: float = 0.0


LINES: list[Line] = [
    Line("f", "不好意思，加错人了", "+36%", 0.12),
    Line("m", "没事", "+25%", 0.10),
    Line("f", "这么巧，认识一下？", "+35%", 0.12),
    Line("m", "行", "+22%", 0.10),
    Line("f", "你是做什么工作的", "+35%", 0.10),
    Line("m", "我是做招聘的", "+28%", 0.08),
    Line("m", "你找工作吗", "+32%", 0.06),
    Line("m", "可以先把简历发来看看", "+38%", 0.12, True),
    Line("f", "不找，我在我爸公司上班", "+40%", 0.11),
    Line("m", "什么岗位？具体负责什么", "+38%", 0.09),
    Line("f", "行政吧，反正什么都做", "+39%", 0.10),
    Line("m", "那经历不少，简历发来", "+40%", 0.11, True),
    Line("f", "其实我喜欢摄影", "+34%", 0.07),
    Line("f", "我爸说我不务正业", "+36%", 0.10),
    Line("m", "拍过什么？给谁拍？接过单吗", "+42%", 0.09),
    Line("f", "你怎么又开始面试了", "+39%", 0.08),
    Line("m", "职业习惯，简历发来", "+39%", 0.12, True),
    Line("f", "我刚和我爸吵了一架", "+38%", 0.10),
    Line("m", "先别裸辞，简历发来", "+38%", 0.12, True),
    Line("f", "我想回老家陪爷爷奶奶", "+40%", 0.10),
    Line("m", "老家有什么产业", "+34%", 0.08),
    Line("f", "我爷爷种茶", "+28%", 0.08),
    Line("m", "多大规模？一年卖多少", "+38%", 0.08),
    Line("f", "你问这个干嘛", "+34%", 0.08),
    Line("m", "看看能不能写成项目经历", "+38%", 0.06),
    Line("m", "让爷爷也发份简历", "+36%", 0.15, True),
    Line("f", "？？？", "+10%", 0.12),
    Line("f", "你是不是有病", "+31%", 0.08),
    Line("m", "别生气，简历先发来", "+38%", 0.10, True),
    Line("f", "去你的简历", "+32%", 0.08),
    Line("m", "这句话冲突感挺强", "+34%", 0.05),
    Line("m", "适合短视频运营", "+33%", 0.05),
    Line("m", "简历发来", "+25%", 0.20, True),
]


VOICE = {
    "f": ("zh-CN-XiaoxiaoNeural", "+4Hz"),
    "m": ("zh-CN-YunxiNeural", "-5Hz"),
}


def run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def ffprobe_duration(path: Path) -> float:
    p = run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1", str(path),
        ], capture=True
    )
    return float((p.stdout or "0").strip())


def ensure_dirs() -> None:
    BUILD.mkdir(exist_ok=True)
    AUDIO_DIR.mkdir(exist_ok=True)


async def edge_tts_one(line: Line, out: Path) -> None:
    import edge_tts
    voice, pitch = VOICE[line.speaker]
    communicate = edge_tts.Communicate(
        line.text,
        voice=voice,
        rate=line.rate,
        pitch=pitch,
        volume="+0%",
    )
    await communicate.save(str(out))


def espeak_one(line: Line, out: Path) -> None:
    wav = out.with_suffix(".wav")
    speed = "230" if line.speaker == "f" else "215"
    pitch = "68" if line.speaker == "f" else "46"
    run(["espeak", "-v", "zh", "-s", speed, "-p", pitch, "-a", "190", "-w", str(wav), line.text])
    filt = (
        "aresample=44100,highpass=f=110,lowpass=f=9500,"
        "acompressor=threshold=-20dB:ratio=3.5:attack=6:release=80,"
        "equalizer=f=2600:t=q:w=1.2:g=2"
    )
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav), "-af", filt, str(out)])
    wav.unlink(missing_ok=True)


async def generate_tts(backend: str) -> None:
    tasks = []
    for i, line in enumerate(LINES):
        out = AUDIO_DIR / f"line_{i:02d}.mp3"
        if out.exists() and out.stat().st_size > 500:
            continue
        if backend == "edge":
            tasks.append(edge_tts_one(line, out))
        else:
            espeak_one(line, out)
    if tasks:
        try:
            for task in tasks:
                await task
        except Exception as exc:
            print(f"Edge TTS failed ({exc}); using espeak fallback.", file=sys.stderr)
            for i, line in enumerate(LINES):
                out = AUDIO_DIR / f"line_{i:02d}.mp3"
                if not out.exists() or out.stat().st_size < 500:
                    espeak_one(line, out)

    cursor = 0.55
    for i, line in enumerate(LINES):
        out = AUDIO_DIR / f"line_{i:02d}.mp3"
        line.duration = ffprobe_duration(out)
        line.start = cursor
        cursor += line.duration + line.gap_after
    (BUILD / "timeline.json").write_text(
        json.dumps([asdict(x) for x in LINES], ensure_ascii=False, indent=2), encoding="utf-8"
    )


def ease_out_back(x: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_out_cubic(x: float) -> float:
    return 1 - (1 - x) ** 3


def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return max(a, min(b, x))


def load_fonts() -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    regular = ImageFont.truetype(FONT_REGULAR, 52)
    bold = ImageFont.truetype(FONT_BOLD, 54)
    small = ImageFont.truetype(FONT_REGULAR, 36)
    return regular, bold, small


def decode_user_avatar() -> Image.Image:
    raw = base64.b64decode((ASSETS / "user_avatar.jpg.b64").read_text().strip())
    path = BUILD / "user_avatar.jpg"
    path.write_bytes(raw)
    im = Image.open(path).convert("RGB")
    s = min(im.size)
    left = (im.width - s) // 2
    top = (im.height - s) // 2
    return im.crop((left, top, left + s, top + s)).resize((112, 112), Image.Resampling.LANCZOS)


def make_female_avatar() -> Image.Image:
    rng = np.random.default_rng(417)
    size = 512
    yy, xx = np.mgrid[0:size, 0:size]
    base = np.zeros((size, size, 3), dtype=np.float32)
    base[..., 0] = 205 + 28 * (1 - yy / size) + 10 * np.sin(xx / 90)
    base[..., 1] = 188 + 30 * (1 - xx / size)
    base[..., 2] = 154 + 35 * (yy / size)
    base += rng.normal(0, 7, base.shape)
    base = np.clip(base, 0, 255).astype(np.uint8)
    im = Image.fromarray(base, "RGB").filter(ImageFilter.GaussianBlur(2.2))
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse((-120, 40, 210, 520), fill=(36, 28, 26, 155))
    for _ in range(38):
        x = int(rng.normal(365, 90))
        y = int(rng.normal(360, 95))
        r = int(rng.integers(16, 42))
        color = random.choice([(242, 125, 55, 210), (232, 91, 35, 205), (255, 174, 86, 205)])
        d.ellipse((x-r, y-r, x+r, y+r), fill=color)
        d.ellipse((x-r//3, y-r//3, x+r//3, y+r//3), fill=(245, 210, 100, 180))
    for _ in range(17):
        x = int(rng.integers(260, 500))
        d.line((x, 510, x + int(rng.integers(-80, 50)), int(rng.integers(250, 440))), fill=(53, 91, 51, 145), width=5)
    im = im.filter(ImageFilter.GaussianBlur(1.0))
    arr = np.asarray(im).astype(np.float32)
    arr += rng.normal(0, 4, arr.shape)
    rdist = np.sqrt(((xx-size/2)/(size/2))**2 + ((yy-size/2)/(size/2))**2)
    arr *= (1 - 0.16 * np.clip(rdist, 0, 1))[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((112,112), Image.Resampling.LANCZOS)


def rounded_avatar(im: Image.Image, size: int = 94) -> Image.Image:
    im = im.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size-1, size-1), radius=16, fill=255)
    im.putalpha(mask)
    return im


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        test = current + ch
        if font.getlength(test) <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def create_bubble(line: Line, user_avatar: Image.Image, female_avatar: Image.Image) -> np.ndarray:
    regular, bold, _ = load_fonts()
    font = bold if line.emphasis else regular
    max_text_w = 730
    lines = wrap_text(line.text, font, max_text_w)
    text_w = int(max(font.getlength(x) for x in lines))
    line_h = int(font.size * 1.28)
    text_h = line_h * len(lines)
    pad_x, pad_y = 28, 22
    bubble_w = text_w + pad_x * 2
    bubble_h = text_h + pad_y * 2
    avatar_size = 94
    gap = 20
    canvas_w = avatar_size + gap + bubble_w + 36
    canvas_h = max(avatar_size, bubble_h) + 28

    shadow = Image.new("RGBA", (canvas_w, canvas_h), (0,0,0,0))
    d = ImageDraw.Draw(shadow)
    if line.speaker == "f":
        avatar_x = 8
        bubble_x = avatar_size + gap + 8
        fill = (247, 247, 247, 255)
        txt = (18, 18, 18, 255)
    else:
        bubble_x = 8
        avatar_x = bubble_x + bubble_w + gap
        fill = (149, 239, 109, 255)
        txt = (10, 28, 12, 255)
    bubble_y = (canvas_h - bubble_h) // 2
    avatar_y = (canvas_h - avatar_size) // 2

    d.rounded_rectangle((bubble_x+6, bubble_y+8, bubble_x+bubble_w+6, bubble_y+bubble_h+8), radius=18, fill=(0,0,0,75))
    if line.speaker == "f":
        d.polygon([(bubble_x+7, bubble_y+38), (bubble_x-4, bubble_y+51), (bubble_x+7, bubble_y+63)], fill=(0,0,0,65))
    else:
        bx2 = bubble_x + bubble_w
        d.polygon([(bx2-1, bubble_y+38), (bx2+17, bubble_y+51), (bx2-1, bubble_y+63)], fill=(0,0,0,65))
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))

    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0,0,0,0))
    canvas.alpha_composite(shadow)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((bubble_x, bubble_y, bubble_x+bubble_w, bubble_y+bubble_h), radius=18, fill=fill)
    if line.speaker == "f":
        d.polygon([(bubble_x+4, bubble_y+30), (bubble_x-14, bubble_y+43), (bubble_x+4, bubble_y+55)], fill=fill)
        avatar = rounded_avatar(female_avatar, avatar_size)
    else:
        bx2 = bubble_x + bubble_w
        d.polygon([(bx2-4, bubble_y+30), (bx2+14, bubble_y+43), (bx2-4, bubble_y+55)], fill=fill)
        avatar = rounded_avatar(user_avatar, avatar_size)
    canvas.alpha_composite(avatar, (avatar_x, avatar_y))
    y = bubble_y + pad_y - 4
    for row in lines:
        d.text((bubble_x+pad_x, y), row, font=font, fill=txt)
        y += line_h

    if line.emphasis:
        border = Image.new("RGBA", canvas.size, (0,0,0,0))
        bd = ImageDraw.Draw(border)
        bd.rounded_rectangle((bubble_x-4, bubble_y-4, bubble_x+bubble_w+4, bubble_y+bubble_h+4), radius=22, outline=(167,255,112,180), width=4)
        canvas.alpha_composite(border)
    return np.array(canvas)


def alpha_blend(dst: np.ndarray, src_rgba: np.ndarray, x: int, y: int) -> None:
    h, w = src_rgba.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(dst.shape[1], x+w), min(dst.shape[0], y+h)
    if x1 >= x2 or y1 >= y2:
        return
    sx1, sy1 = x1-x, y1-y
    sx2, sy2 = sx1+(x2-x1), sy1+(y2-y1)
    src = src_rgba[sy1:sy2, sx1:sx2]
    alpha = src[..., 3:4].astype(np.float32) / 255.0
    dst_region = dst[y1:y2, x1:x2].astype(np.float32)
    dst[y1:y2, x1:x2] = (src[..., :3].astype(np.float32)*alpha + dst_region*(1-alpha)).astype(np.uint8)


def transform_rgba(img: np.ndarray, scale: float, angle: float) -> np.ndarray:
    h, w = img.shape[:2]
    nw, nh = max(2, int(w*scale)), max(2, int(h*scale))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    center = (nw/2, nh/2)
    mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(mat[0,0]); sin = abs(mat[0,1])
    bw = int(nh*sin + nw*cos); bh = int(nh*cos + nw*sin)
    mat[0,2] += bw/2 - center[0]
    mat[1,2] += bh/2 - center[1]
    return cv2.warpAffine(resized, mat, (bw, bh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))


def build_bubbles() -> tuple[list[np.ndarray], Image.Image, Image.Image]:
    user = decode_user_avatar()
    female = make_female_avatar()
    user.save(BUILD / "avatar_user.png")
    female.save(BUILD / "avatar_other.png")
    bubbles = [create_bubble(line, user, female) for line in LINES]
    return bubbles, user, female


def create_system_card(user_avatar: Image.Image) -> np.ndarray:
    regular, bold, small = load_fonts()
    canvas = Image.new("RGBA", (920, 320), (0,0,0,0))
    sh = Image.new("RGBA", canvas.size, (0,0,0,0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle((20,25,900,300), radius=24, fill=(0,0,0,100))
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    canvas.alpha_composite(sh)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((12,12,888,288), radius=24, fill=(248,248,248,255))
    av = rounded_avatar(user_avatar, 76)
    canvas.alpha_composite(av, (42,42))
    d.text((142, 45), "简历发来", font=bold, fill=(20,20,20,255))
    d.ellipse((48,156,94,202), fill=(244,72,64,255))
    d.text((71,178), "!", font=bold, fill=(255,255,255,255), anchor="mm")
    d.text((118,157), "消息已发出，但被对方拒收了。", font=small, fill=(130,130,130,255))
    d.text((118,213), "请先发送朋友验证请求。", font=small, fill=(165,165,165,255))
    return np.array(canvas)


def draw_background(frame: np.ndarray, t: float, beat: float, width: int, height: int) -> None:
    frame[:] = (4, 4, 6)
    s = width / W
    cx = int(width/2 + math.sin(t*0.23)*90*s)
    cy = int(height/2 + math.cos(t*0.19)*130*s)
    for i in range(8):
        radius = int((((t*85 + i*230) % 1800) + 80)*s)
        c = int(12 + 14*beat)
        cv2.circle(frame, (cx,cy), radius, (c,c,c+2), 2, cv2.LINE_AA)
    for i in range(5):
        y = int(((t*130 + i*420) % (H+400) - 200)*s)
        xoff = int(120*s*math.sin(t*0.6+i))
        cv2.line(frame, (int(-100*s)+xoff,y), (width+int(100*s)+xoff,y-int(280*s)), (14,14,16), max(2,int(12*s)), cv2.LINE_AA)
    overlay = np.zeros_like(frame)
    r = int((120 + 40*beat)*s)
    cv2.circle(overlay, (width//2,height//2), r, (18,22,20), -1, cv2.LINE_AA)
    frame[:] = cv2.addWeighted(frame, 1.0, overlay, 0.45, 0)


def render_video(bubbles: list[np.ndarray], user_avatar: Image.Image, duration: float, out: Path, preview: bool = False) -> None:
    width, height, fps = (540, 960, 24) if preview else (720, 1280, FPS)
    scale_out = width / W
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
        "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264",
        "-preset", "medium" if not preview else "veryfast", "-crf", "18" if not preview else "25",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    total_frames = int(math.ceil(duration*fps))
    y_positions = [315, 700, 1090, 500, 890, 1280, 390, 820, 1180]
    angles = [-2.7, 1.8, -1.0, 3.0, -4.2, 1.2, 2.5, -2.0]
    system_card = create_system_card(user_avatar)
    block_start = duration - 4.5

    for fi in range(total_frames):
        t = fi/fps
        bpm = 132
        phase = (t * bpm / 60.0) % 1.0
        beat = math.exp(-phase*8.0)
        frame = np.empty((height,width,3), dtype=np.uint8)
        draw_background(frame, t, beat, width, height)

        active: list[tuple[int, Line]] = []
        for idx, line in enumerate(LINES):
            vis_start = line.start - 0.14
            vis_end = line.start + line.duration + 0.48
            if vis_start <= t <= vis_end:
                active.append((idx, line))
        active = active[-3:]

        for stack_i, (idx, line) in enumerate(active):
            age = t - (line.start - 0.14)
            intro = clamp(age/0.28)
            outro = clamp(((line.start+line.duration+0.48)-t)/0.25)
            vis = min(intro, outro)
            if vis <= 0:
                continue
            base = bubbles[idx]
            in_ease = ease_out_back(intro)
            base_scale = 1.03 if line.emphasis else 0.94
            pulse = (0.035*math.sin(age*14)) if line.emphasis else (0.012*math.sin(age*9))
            sc = ((0.58 + 0.42*in_ease)*base_scale + pulse) * scale_out
            if stack_i < len(active)-1:
                sc *= 0.88
            ang = angles[idx % len(angles)]*(1-intro) + 0.35*math.sin(age*2.5+idx)
            if line.emphasis:
                ang += 1.2*math.sin(age*10)*math.exp(-age*1.4)
            transformed = transform_rgba(base, sc, ang)
            bw, bh = transformed.shape[1], transformed.shape[0]
            target_y = int(y_positions[idx % len(y_positions)] * scale_out)
            if len(active) > 1:
                target_y += int((stack_i-(len(active)-1))*150*scale_out)
            if line.speaker == "f":
                target_x = int((60 + (idx%3)*35)*scale_out)
                start_x = -bw-int(100*scale_out)
            else:
                target_x = width-bw-int((55+(idx%3)*30)*scale_out)
                start_x = width+int(100*scale_out)
            x = int(start_x + (target_x-start_x)*ease_out_cubic(intro))
            y = int(target_y + 70*scale_out*(1-intro)*math.sin(idx*1.7))
            if outro < 1:
                x += int((1-outro)*scale_out*(90 if line.speaker=="m" else -90))
            alpha = vis
            if alpha < 0.999:
                transformed = transformed.copy()
                transformed[...,3] = (transformed[...,3].astype(np.float32)*alpha).astype(np.uint8)
            alpha_blend(frame, transformed, x, y)

            if line.emphasis and 0 <= t-line.start <= 0.24:
                flash = clamp(1-(t-line.start)/0.24)
                cv2.rectangle(frame, (0,0), (width-1,height-1), (int(35*flash), int(70*flash), int(25*flash)), int(10*flash)+1)

        for i in range(28):
            amp = 10 + int(42*(0.2+0.8*beat)*abs(math.sin(t*4.4+i*0.71)))
            x = int((135 + i*30)*scale_out)
            amp = max(2, int(amp*scale_out))
            cv2.rectangle(frame, (x,height-int(92*scale_out)-amp), (x+max(3,int(10*scale_out)),height-int(92*scale_out)+amp), (75,82,78), -1)

        if t >= block_start:
            p = clamp((t-block_start)/0.42)
            card = transform_rgba(system_card, (0.72+0.28*ease_out_back(p))*scale_out, -1.5*(1-p))
            alpha_blend(frame, card, (width-card.shape[1])//2, int(560*scale_out))
            fail_texts = ["简历发来", "简历先发来", "我帮你看看"]
            regular, bold, small = load_fonts()
            for j, txt in enumerate(fail_texts):
                appear = block_start + 0.75 + j*0.62
                if t < appear:
                    continue
                q = clamp((t-appear)/0.22)
                tile = Image.new("RGBA", (600,115), (0,0,0,0))
                td = ImageDraw.Draw(tile)
                td.rounded_rectangle((30,10,510,105), radius=18, fill=(149,239,109,255))
                td.text((60,28), txt, font=regular, fill=(12,28,14,255))
                td.ellipse((530,36,574,80), fill=(244,72,64,255))
                td.text((552,58), "!", font=bold, fill=(255,255,255,255), anchor="mm")
                arr = transform_rgba(np.array(tile), (0.8+0.2*ease_out_back(q))*scale_out, (j-1)*1.2)
                alpha_blend(frame, arr, int((300-j*42)*scale_out), int((940+j*145)*scale_out))

        if not preview:
            grain = np.random.default_rng(fi).integers(-3,4,frame.shape,dtype=np.int16)
            frame = np.clip(frame.astype(np.int16)+grain,0,255).astype(np.uint8)
        if beat > 0.6:
            s = 1.0 + 0.006*beat
            nw, nh = int(width*s), int(height*s)
            z = cv2.resize(frame,(nw,nh),interpolation=cv2.INTER_LINEAR)
            frame = z[(nh-height)//2:(nh-height)//2+height,(nw-width)//2:(nw-width)//2+width]

        proc.stdin.write(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).tobytes())
        if fi % (fps*5) == 0:
            print(f"render {fi}/{total_frames} ({t:.1f}s)", flush=True)

    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg video encoder exited {rc}")


def add_tone(buf: np.ndarray, start_s: float, wave: np.ndarray, gain: float = 1.0) -> None:
    start = int(start_s*SR)
    end = min(len(buf), start+len(wave))
    if start < 0 or start >= len(buf) or end <= start:
        return
    buf[start:end] += wave[:end-start]*gain


def generate_beat(duration: float, out: Path) -> None:
    n = int(duration*SR)
    rng = np.random.default_rng(20260717)
    audio = np.zeros(n, dtype=np.float32)
    bpm = 132
    beat_s = 60/bpm
    tk = np.arange(int(0.32*SR))/SR
    kick = np.sin(2*np.pi*(72*np.exp(-tk*7)+38)*tk)*np.exp(-tk*13)
    kick += 0.35*rng.normal(0,1,len(tk))*np.exp(-tk*35)
    ts = np.arange(int(0.23*SR))/SR
    snare = rng.normal(0,1,len(ts))*np.exp(-ts*17)
    snare += 0.25*np.sin(2*np.pi*190*ts)*np.exp(-ts*15)
    th = np.arange(int(0.08*SR))/SR
    hat = rng.normal(0,1,len(th))*np.exp(-th*55)
    hat = np.concatenate([[0], np.diff(hat)])

    beats = int(duration/beat_s)+3
    for b in range(beats):
        t = b*beat_s
        add_tone(audio,t,kick,0.55 if b%4==0 else 0.40)
        if b%4 in (1,3):
            add_tone(audio,t,snare,0.20)
        add_tone(audio,t,hat,0.055)
        add_tone(audio,t+beat_s/2,hat,0.042)

    notes = [55.0,55.0,65.41,73.42,49.0,55.0,82.41,73.42]
    for b in range(beats):
        t0=b*beat_s
        tt=np.arange(int(beat_s*0.9*SR))/SR
        f=notes[b%len(notes)]
        bass=(np.sin(2*np.pi*f*tt)+0.28*np.sin(2*np.pi*2*f*tt))*np.exp(-tt*3.4)
        add_tone(audio,t0,bass,0.11)

    for line in LINES:
        tp=np.arange(int(0.11*SR))/SR
        pop=np.sin(2*np.pi*(680+90*np.sin(2*np.pi*7*tp))*tp)*np.exp(-tp*30)
        add_tone(audio,line.start-0.05,pop,0.11)
        if line.emphasis:
            tr=np.arange(int(0.35*SR))/SR
            riser=rng.normal(0,1,len(tr))*np.linspace(0,1,len(tr))*0.035
            add_tone(audio,line.start-0.22,riser,1.0)

    block_start = duration-4.5
    for j in range(3):
        te=np.arange(int(0.22*SR))/SR
        err=(np.sin(2*np.pi*420*te)+0.6*np.sin(2*np.pi*320*te))*np.exp(-te*13)
        add_tone(audio,block_start+0.75+j*0.62,err,0.12)

    fade = int(0.6*SR)
    audio[:fade] *= np.linspace(0,1,fade)
    audio[-fade:] *= np.linspace(1,0,fade)
    audio = np.tanh(audio*1.25)
    stereo=np.stack([audio,audio],axis=1)
    import wave
    with wave.open(str(out),"wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(stereo,-1,1)*32767).astype(np.int16).tobytes())


def mix_audio(duration: float, out: Path) -> None:
    beat = BUILD/"beat.wav"
    generate_beat(duration, beat)
    cmd=["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(beat)]
    for i in range(len(LINES)):
        cmd += ["-i", str(AUDIO_DIR/f"line_{i:02d}.mp3")]
    filters=[]
    labels=["[beat]"]
    filters.append("[0:a]volume=0.38[beat]")
    for i,line in enumerate(LINES, start=1):
        delay=max(0,int(line.start*1000))
        vol="1.28" if line.speaker=="m" else "1.18"
        if line.emphasis:
            filt=f"[{i}:a]adelay={delay}|{delay},volume={vol},aecho=0.8:0.62:70:0.16[a{i}]"
        else:
            filt=f"[{i}:a]adelay={delay}|{delay},volume={vol}[a{i}]"
        filters.append(filt); labels.append(f"[a{i}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0,alimiter=limit=0.92,loudnorm=I=-14:LRA=7:TP=-1.2[mix]")
    cmd += ["-filter_complex",";".join(filters),"-map","[mix]","-t",f"{duration:.3f}","-c:a","aac","-b:a","192k",str(out)]
    run(cmd)


def mux(video: Path, audio: Path, out: Path, upscale: bool = False) -> None:
    cmd=["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(video),"-i",str(audio)]
    if upscale:
        cmd += ["-vf","scale=1080:1920:flags=lanczos","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p"]
    else:
        cmd += ["-c:v","copy"]
    cmd += ["-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(out)]
    run(cmd)


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--tts", choices=["edge","espeak"], default=os.environ.get("TTS_BACKEND","edge"))
    parser.add_argument("--preview", action="store_true")
    args=parser.parse_args()
    ensure_dirs()
    asyncio.run(generate_tts(args.tts))
    bubbles,user,_ = build_bubbles()
    duration = LINES[-1].start + LINES[-1].duration + 5.0
    silent=BUILD/("preview_silent.mp4" if args.preview else "final_silent.mp4")
    audio=BUILD/("preview_audio.m4a" if args.preview else "final_audio.m4a")
    final=BUILD/("preview.mp4" if args.preview else "final.mp4")
    render_video(bubbles,user,duration,silent,preview=args.preview)
    mix_audio(duration,audio)
    mux(silent,audio,final,upscale=not args.preview)
    print(f"DONE: {final} ({ffprobe_duration(final):.2f}s)")


if __name__ == "__main__":
    main()

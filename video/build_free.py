"""30초 학과 홍보영상 무료 초안 생성기 (AI 생성 없음, 크레딧 0)

학과 홈페이지 사진에 줌·패닝 효과를 주고 한글 자막과 합격 실적 그래픽을 얹어
1080x1920(9:16) 30fps MP4를 만듭니다. 내레이션·배경음악은 넣지 않습니다.

사용법:
    pip install pillow imageio-ffmpeg
    python video/build_free.py
결과: video/output/promo_30s_free.mp4

한글 폰트 Noto Sans KR(Google Fonts)이 ~/.fonts 또는 시스템에 설치되어 있어야 합니다.
"""
import glob
import os
import subprocess

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, 'assets')
OUT = os.path.join(HERE, 'output', 'promo_30s_free.mp4')

# 카드뉴스와 같은 브랜드 색상
NAVY = (11, 42, 91)
NAVY_DEEP = (7, 28, 63)
YELLOW = (255, 200, 61)
MINT = (53, 195, 176)
WHITE = (255, 255, 255)

HANDLE = '@cwnu_department_of_accounting'


def font(weight):
    names = {900: 'NotoSansKR-900', 700: 'NotoSansKR-700', 500: 'NotoSansKR-500', 400: 'NotoSansKR-400'}
    hits = glob.glob(os.path.expanduser(f'~/.fonts/{names[weight]}.ttf')) + glob.glob(
        f'/usr/share/fonts/**/{names[weight]}*.ttf', recursive=True)
    if not hits:
        raise SystemExit('Noto Sans KR 폰트를 찾을 수 없습니다.')
    return hits[0]


F900, F700, F500 = font(900), font(700), font(500)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def cover(im, scale=1.0):
    """im을 W x H*scale 이상으로 덮도록 확대."""
    r = max(W * scale / im.width, H * scale / im.height)
    return im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)


def kenburns(im, t, z0=1.0, z1=1.1, dx=0.0):
    """t(0~1)에 따라 천천히 확대·이동한 W x H 프레임 (비율 유지)."""
    z = z0 + (z1 - z0) * ease(t)
    k = min(im.width / W, im.height / H) / 1.06
    cw, ch = W * k / z, H * k / z
    cx = im.width / 2 + dx * im.width * (ease(t) - 0.5)
    cx = max(cw / 2, min(im.width - cw / 2, cx))
    cy = im.height / 2
    return im.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))


def text_layer(lines, size, weight, color=WHITE, y=None, align='center', box=None, lh=1.25, x=None):
    """투명 레이어에 여러 줄 텍스트. box=(fill, pad)면 뒤에 반투명 박스."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(weight, size)
    widths = [d.textlength(s, font=f) for s in lines]
    total_h = int(size * lh * len(lines))
    top = (H - total_h) // 2 if y is None else y
    if box:
        fill, pad = box
        bw = max(widths)
        bx = (W - bw) / 2 if align == 'center' else x
        d.rounded_rectangle((bx - pad, top - pad * 0.6, bx + bw + pad, top + total_h + pad * 0.4), 28, fill=fill)
    for i, s in enumerate(lines):
        tx = (W - widths[i]) / 2 if align == 'center' else x
        d.text((tx, top + i * size * lh), s, font=f, fill=color)
    return layer


def with_alpha(layer, a):
    if a >= 1:
        return layer
    r, g, b, al = layer.split()
    al = al.point(lambda v: int(v * max(0.0, a)))
    return Image.merge('RGBA', (r, g, b, al))


def grid_bg(color=NAVY):
    im = Image.new('RGB', (W, H), color)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 60):
        d.line((x, 0, x, H), fill=tuple(min(255, c + 10) for c in color))
    for y in range(0, H, 60):
        d.line((0, y, W, y), fill=tuple(min(255, c + 10) for c in color))
    return im


def darken(im, k=0.45):
    return Image.blend(im, Image.new('RGB', im.size, (0, 0, 0)), k)


def load(name):
    return Image.open(os.path.join(ASSETS, name)).convert('RGB')


# ---------- 장면 정의: (길이(초), 프레임 함수(t_local, 초)) ----------

def scene_hook():
    bg = cover(grid_bg(), 1.12)
    t1 = text_layer(['회계학과,'], 130, F900, y=700)
    t2 = text_layer(['계산만', '한다고요?'], 150, F900, color=YELLOW, y=880)

    def f(s):
        fr = kenburns(bg, s / 4, 1.0, 1.06).convert('RGBA')
        fr.alpha_composite(with_alpha(t1, ease(s / 0.6)))
        fr.alpha_composite(with_alpha(t2, ease((s - 0.8) / 0.6)))
        return fr
    return 4, f


def framed_photo_scene(photo, dur, caption, sub=None, dx=0.12):
    """가로로 긴 사진: 흐린 배경 + 가운데 사진이 천천히 패닝."""
    bg = cover(darken(photo.filter(ImageFilter.GaussianBlur(30)), 0.35), 1.12)
    ph_h = 760
    ph = photo.resize((int(photo.width * ph_h / photo.height * 1.25), int(ph_h * 1.25)), Image.LANCZOS)
    cap = text_layer(caption, 84, F900, y=1320)
    sub_l = text_layer([sub], 46, F900, color=NAVY_DEEP, y=330, box=(YELLOW, 28)) if sub else None

    def f(s):
        t = s / dur
        fr = kenburns(bg, t, 1.0, 1.05).convert('RGBA')
        # 사진 패닝: 넓은 사진에서 가로 1080 폭 창을 천천히 이동
        z = 1.0 + 0.06 * ease(t)
        k = ph.height / ph_h
        win_w, win_h = W * k / z, ph_h * k / z
        cx = ph.width * (0.5 - dx / 2 + dx * ease(t))
        cx = max(win_w / 2, min(ph.width - win_w / 2, cx))
        box = (cx - win_w / 2, (ph.height - win_h) / 2, cx + win_w / 2, (ph.height + win_h) / 2)
        crop = ph.resize((W, ph_h), Image.BILINEAR, box=box)
        fr.paste(crop, (0, (H - ph_h) // 2 - 60))
        if sub_l:
            fr.alpha_composite(with_alpha(sub_l, ease((s - 0.2) / 0.5)))
        fr.alpha_composite(with_alpha(cap, ease((s - 0.5) / 0.6)))
        return fr
    return dur, f


def full_photo_scene(photo, dur, caption, z0=1.0, z1=1.12, dx=0.0, tag=None):
    base = cover(photo, 1.12)
    shade = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shade).rectangle((0, H - 760, W, H), fill=(7, 28, 63, 170))
    cap = text_layer(caption, 80, F900, y=H - 600)
    tag_l = text_layer([tag], 44, F900, color=NAVY_DEEP, y=H - 740, box=(YELLOW, 26)) if tag else None

    def f(s):
        fr = kenburns(base, s / dur, z0, z1, dx).convert('RGBA')
        fr.alpha_composite(shade)
        if tag_l:
            fr.alpha_composite(with_alpha(tag_l, ease((s - 0.2) / 0.4)))
        fr.alpha_composite(with_alpha(cap, ease((s - 0.4) / 0.6)))
        return fr
    return dur, f


def scene_ai():
    bg = cover(grid_bg(NAVY_DEEP), 1.12)
    tag = text_layer(['2026 교육과정 개편'], 48, F900, color=NAVY_DEEP, y=560, box=(YELLOW, 28))
    title = text_layer(['AI와', '회계데이터분석'], 120, F900, y=700)
    sub = text_layer(['반복 업무는 AI에게,', '판단은 회계 전문가에게'], 54, F500, color=(220, 228, 240), y=1060)
    bars = [0.35, 0.55, 0.45, 0.75, 0.62, 0.9]

    def f(s):
        fr = kenburns(bg, s / 5, 1.0, 1.04).convert('RGBA')
        d = ImageDraw.Draw(fr)
        for i, v in enumerate(bars):  # 막대그래프가 차오르는 연출
            hgt = int(360 * v * ease((s - 0.3 - i * 0.12) / 0.8))
            x = 190 + i * 125
            d.rounded_rectangle((x, 1640 - hgt, x + 80, 1640), 10, fill=MINT if i == len(bars) - 1 else (60, 100, 160))
        fr.alpha_composite(with_alpha(tag, ease(s / 0.4)))
        fr.alpha_composite(with_alpha(title, ease((s - 0.3) / 0.6)))
        fr.alpha_composite(with_alpha(sub, ease((s - 1.0) / 0.6)))
        return fr
    return 5, f


def scene_results():
    bg = cover(grid_bg(), 1.12)
    head = text_layer(['선배들이 먼저', '증명했습니다'], 96, F900, y=380)
    rows = [('공인회계사 · 세무사', '4명'), ('공무원 (7급 2명 포함)', '19명'), ('공기업 · 금융 · 기업', '14명')]
    fl = ImageFont.truetype(F700, 52)
    fn = ImageFont.truetype(F900, 110)
    note = text_layer(['2021~2024 학과 홈페이지 공개 명단, 합격 건수 기준'], 32, F500, color=(200, 210, 230), y=1700)

    def row_layer(i, label, num, shown):
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        y = 760 + i * 300
        d.rounded_rectangle((90, y, W - 90, y + 250), 32, fill=(255, 255, 255, 235))
        d.text((140, y + 40), label, font=fl, fill=NAVY)
        txt = f'{shown}명' if num.endswith('명') else num
        d.text((W - 140 - d.textlength(txt, font=fn), y + 90), txt, font=fn, fill=NAVY_DEEP)
        return layer

    def f(s):
        fr = kenburns(bg, s / 7, 1.0, 1.05).convert('RGBA')
        fr.alpha_composite(with_alpha(head, ease(s / 0.5)))
        for i, (label, num) in enumerate(rows):
            st = 0.8 + i * 1.3
            k = ease((s - st) / 0.5)
            if k <= 0:
                continue
            total = int(num[:-1])
            shown = max(1, round(total * ease((s - st) / 1.0)))  # 숫자 카운트업
            fr.alpha_composite(with_alpha(row_layer(i, label, num, shown), k))
        fr.alpha_composite(with_alpha(note, ease((s - 4.5) / 0.5)))
        return fr
    return 7, f


def scene_end(photo):
    bg = cover(darken(photo.filter(ImageFilter.GaussianBlur(24)), 0.5), 1.12)
    t1 = text_layer(['다음 합격자는', '바로 당신입니다'], 104, F900, y=620)
    t2 = text_layer(['국립창원대학교', '회계학과'], 84, F900, color=YELLOW, y=1080)
    t3 = text_layer([HANDLE], 40, F700, color=WHITE, y=1420, box=((255, 255, 255, 40), 30))

    def f(s):
        fr = kenburns(bg, s / 4, 1.0, 1.06).convert('RGBA')
        fr.alpha_composite(with_alpha(t1, ease(s / 0.5)))
        fr.alpha_composite(with_alpha(t2, ease((s - 0.9) / 0.5)))
        fr.alpha_composite(with_alpha(t3, ease((s - 1.5) / 0.5)))
        return fr
    return 4, f


def main():
    scenes = [
        scene_hook(),                                                        # 0~4초
        framed_photo_scene(load('building.jpg'), 5,
                           ['국립창원대학교', '회계학과'], sub='1979년부터'),     # 4~9초
        framed_photo_scene(load('lecture.jpg'), 5,
                           ['재무회계 · 세법', '회계감사'], sub='전공 수업 = 시험 과목', dx=0.25),  # 9~14초
        scene_ai(),                                                          # 14~19초
        scene_results(),                                                     # 19~26초
        scene_end(load('fair.jpg')),                                         # 26~30초
    ]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen(
        [ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
         '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
         '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    fade = 0.35  # 장면 사이 검은 화면 전환(초)
    for dur, fn in scenes:
        n = int(dur * FPS)
        for i in range(n):
            s = i / FPS
            fr = fn(s).convert('RGB')
            edge = min(s, dur - s)
            if edge < fade:
                fr = Image.blend(Image.new('RGB', (W, H)), fr, max(0.15, edge / fade))
            proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    proc.wait()
    print('완료:', OUT)


if __name__ == '__main__':
    main()

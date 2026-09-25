#!/usr/bin/env python3
"""Edición estilo Apple (keynote / reveal de producto).

Receta (sacada del "iPhone 15 Pro Reveal", 35 s):
  - Fondo negro y luz baja: los negros aplastados, casi sin color (el material manda).
  - Pocos planos y largos (2,5-10 s), cámara lenta, siempre un empuje lento (zoom 1.00 → 1.06).
  - Entradas y salidas por negro; los cortes secos solo en los golpes de la música.
  - Barrido de luz: un brillo diagonal que recorre el objeto (el reflejo en el metal).
  - Títulos de una palabra en SF Pro, gris claro, grandes y centrados, que se forman
    desde un desenfoque (como la palabra hecha de partículas) sobre negro.
  - Formato cine: barras 2.39:1 en los planos de detalle.
  - Cierre: negro, marca o nombre, y fundido final de imagen y música.
  - Una idea por pantalla; cifras enormes con una línea que las explica.
  - Movimiento con curva suave (arranca y frena despacio). Ver apple-reference.md.

Uso:  kapple.py plan.json salida.mp4
{
  "music": "tema.mp3", "music_start": 0,
  "shots": [{"path": "a.mp4", "start": 3, "dur": 4, "speed": 0.5, "push": 1.06,
             "sweep": true, "cine": true, "cut": false, "mono": 0.25}, ...],
  "titles": [{"after": 1, "text": "Titanium.", "dur": 2.6, "gradient": [[235,235,240],[120,120,128]]},
             {"after": 2, "text": "2x", "sub": "más rápido", "number": true}],
  "end": {"text": "Zarcillo", "sub": "Se estira hasta tu Mac.", "dur": 3}
}
`after`: el título entra después del plano con ese índice (0 = el primero).
Imágenes fijas: "path": "foto.png" con "still": true.
"""
import json, os, subprocess, sys, tempfile

W, H, FPS = 1920, 1080, 30
FONT = next((f for f in ["/Library/Fonts/SF-Pro-Display-Semibold.otf", "/Library/Fonts/SF-Pro-Display-Medium.otf",
                         "/System/Library/Fonts/SFNS.ttf"] if os.path.exists(f)), "/System/Library/Fonts/SFNS.ttf")
LIGHT = next((f for f in ["/Library/Fonts/SF-Pro-Display-Regular.otf", "/System/Library/Fonts/SFNS.ttf"] if os.path.exists(f)), FONT)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2500:])


def enc(out):
    return ["-r", str(FPS), "-c:v", "libx264", "-crf", "15", "-preset", "medium", "-pix_fmt", "yuv420p", out]


def sweep_png(path):
    """Franja de luz diagonal, suave, transparente alrededor."""
    from PIL import Image, ImageFilter
    img = Image.new("RGBA", (W // 2, H * 2), (0, 0, 0, 0))
    band = Image.new("RGBA", (W // 7, H * 2), (255, 255, 255, 70))
    img.paste(band, ((W // 2 - W // 7) // 2, 0))
    img = img.filter(ImageFilter.GaussianBlur(60)).rotate(-22, expand=True)
    img.save(path)


def text_png(path, text, size, color=(236, 236, 240), blur=0, sub=None, gradient=None):
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    font = ImageFont.truetype(FONT, size)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Letras un poco más juntas, como en los títulos de Apple.
    widths = [d.textlength(ch, font=font) - size * 0.012 for ch in text]
    x = (W - sum(widths)) / 2
    box = d.textbbox((0, 0), text, font=font)
    y = (H - (box[3] - box[1])) / 2 - box[1] - (40 if sub else 0)
    for ch, w in zip(text, widths):
        # Degradado vertical sutil: arriba más claro, como metal.
        d.text((x, y), ch, font=font, fill=color)
        x += w
    if sub:
        f2 = ImageFont.truetype(LIGHT, int(size * 0.3))
        sb = d.textbbox((0, 0), sub, font=f2)
        d.text(((W - (sb[2] - sb[0])) / 2, y + (box[3] - box[1]) + size * 0.35), sub, font=f2, fill=(170, 170, 176))
    if gradient:
        # Titular con degradado vertical (de un color al otro), como los de Apple.
        from PIL import Image as I
        top, bottom = gradient
        grad = I.new("RGBA", (W, H))
        gy0, gy1 = int(y + box[1]), int(y + box[3])
        for yy in range(H):
            k = min(1, max(0, (yy - gy0) / max(1, gy1 - gy0)))
            grad.paste(tuple(int(top[j] + (bottom[j] - top[j]) * k) for j in range(3)) + (255,), (0, yy, W, yy + 1))
        mask = img.split()[3]
        title_only = I.new("L", (W, H), 0)
        title_only.paste(mask.crop((0, 0, W, int(y + box[3] + size * 0.2))), (0, 0))
        img.paste(grad, (0, 0), title_only)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    img.save(path)


def shot(out, s, tmp, i):
    speed = s.get("speed", 0.5)
    dur = s["dur"]
    push = s.get("push", 1.06)
    mono = s.get("mono", 0.25)                    # 0 = blanco y negro, 1 = color original
    fade = 0 if s.get("cut") else 0.5
    fit = s.get("fit", bool(s.get("still")))
    if s.get("still"):
        inp = ["-loop", "1", "-t", str(dur), "-i", s["path"]]
        pre = "null"
    else:
        inp = ["-ss", str(s.get("start", 0)), "-t", str(dur * speed), "-i", s["path"]]
        pre = f"setpts=PTS/{speed},fps={FPS},scale={W * 2}:-2"
    # Empuje lento: la imagen crece de 1.00 a `push` en todo el plano, centrada.
    frames = int(dur * FPS)
    # Las capturas se ven enteras sobre negro (como un producto flotando); el video llena el cuadro.
    frame = ([f"scale={int(W * 1.5)}:{int(H * 1.5)}:force_original_aspect_ratio=decrease",
              f"pad={W * 2}:{H * 2}:(ow-iw)/2:(oh-ih)/2:black"] if fit else
             [f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase", f"crop={W * 2}:{H * 2}"])
    vf = [pre] + frame + [
          f"zoompan=z='1+({push}-1)*(3*pow(on/{frames},2)-2*pow(on/{frames},3))':d=1:x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':s={W}x{H}:fps={FPS}",
          "setsar=1",
          # Negros aplastados, poco color, un poco de contraste y grano fino.
          f"eq=contrast=1.12:saturation={mono}",
          # Solo las sombras más bajas se hunden: lo oscuro sigue legible.
          "curves=all='0/0 0.06/0.02 0.5/0.52 1/1'",
          "noise=alls=5:allf=t", "vignette=PI/4.2"]
    fc = f"[0:v]{','.join(vf)}[b]"
    extra = []
    last = "b"
    if s.get("sweep"):
        sp = f"{tmp}/sweep.png"
        if not os.path.exists(sp):
            sweep_png(sp)
        extra = ["-loop", "1", "-t", str(dur), "-i", sp]
        # El brillo cruza de izquierda a derecha en la mitad central del plano.
        fc += (f";[b][1:v]overlay=x='-w+(W+w)*clip((t-{dur * 0.2})/{dur * 0.6},0,1)':y=-(h-H)/2:eval=frame[s]")
        last = "s"
    if s.get("cine", False):
        bar = int((H - W / 2.39) / 2)
        fc += f";[{last}]drawbox=x=0:y=0:w={W}:h={bar}:color=black:t=fill,drawbox=x=0:y={H - bar}:w={W}:h={bar}:color=black:t=fill[c]"
        last = "c"
    if fade:
        fc += f";[{last}]fade=t=in:st=0:d={fade},fade=t=out:st={dur - fade}:d={fade}[f]"
        last = "f"
    run(["ffmpeg", "-v", "error", "-y"] + inp + extra + ["-filter_complex", fc, "-map", f"[{last}]", "-t", str(dur), "-an"] + enc(out))


def title(out, t, tmp, i):
    """La palabra se forma desde un desenfoque: la borrosa se apaga mientras la nítida aparece."""
    dur = t.get("dur", 2.6)
    size = t.get("size", 330 if t.get("number") else 200)
    soft, sharp = f"{tmp}/t{i}a.png", f"{tmp}/t{i}b.png"
    g = t.get("gradient")
    text_png(soft, t["text"], size, blur=22, sub=t.get("sub"), gradient=g)
    text_png(sharp, t["text"], size, sub=t.get("sub"), gradient=g)
    fc = (f"color=black:s={W}x{H}:r={FPS}:d={dur}[bg];"
          f"[0:v]format=rgba,fade=t=in:st=0:d={dur * 0.25}:alpha=1,fade=t=out:st={dur * 0.35}:d={dur * 0.3}:alpha=1[a];"
          f"[1:v]format=rgba,fade=t=in:st={dur * 0.2}:d={dur * 0.4}:alpha=1,"
          f"scale=w='iw*(1.05-0.05*min(1,t/{dur * 0.7}))':h=-1:eval=frame[s];"
          f"[bg][a]overlay=(W-w)/2:(H-h)/2[x];[x][s]overlay=(W-w)/2:(H-h)/2:eval=frame,"
          f"fade=t=out:st={dur - 0.45}:d=0.45[v]")
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(dur), "-i", soft, "-loop", "1", "-t", str(dur), "-i", sharp,
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur)] + enc(out))


def main():
    plan, dest = json.load(open(sys.argv[1])), sys.argv[2]
    tmp = tempfile.mkdtemp(prefix="kapple-")
    segs = []
    titles = {t["after"]: t for t in plan.get("titles", [])}
    for i, s in enumerate(plan["shots"]):
        p = f"{tmp}/{i:02d}shot.mp4"; shot(p, s, tmp, i); segs.append(p)
        if i in titles:
            p = f"{tmp}/{i:02d}title.mp4"; title(p, titles[i], tmp, i); segs.append(p)
    if plan.get("end"):
        e = plan["end"]
        p = f"{tmp}/99end.mp4"; title(p, {"text": e["text"], "sub": e.get("sub"), "dur": e.get("dur", 3), "size": 170}, tmp, 99)
        segs.append(p)
    lst = f"{tmp}/list.txt"
    open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
    video = f"{tmp}/video.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                                 capture_output=True, text=True).stdout)
    if plan.get("music"):
        run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ss", str(plan.get("music_start", 0)), "-i", plan["music"],
             "-map", "0:v", "-map", "1:a", "-t", f"{total:.2f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
             "-af", f"afade=t=in:st=0:d=1.2,afade=t=out:st={max(0, total - 2):.2f}:d=2", dest])
    else:
        os.replace(video, dest)
    print(dest, f"{total:.1f}s")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Edición estilo "k1yora": frag movie corta de TikTok.

Receta (sacada de un video de referencia de 8 s):
  1. Gancho (~1.2 s): un clip ajeno y muy saturado (p. ej. Geometry Dash) que atrapa.
  2. Clips de jugada, 1-3 s cada uno, pegados sin transición suave; cada uno con su
     grade (cálido, lavado/frío, neón).
  3. Ojo de pez (lente) en el golpe de ratón / giro rápido.
  4. Ráfaga "térmica" o visión nocturna: negativo + grano fuerte + un color por golpe
     de la música (verde, naranja, azul), ~1 s.
  5. Destellos blancos cortos y temblor en los golpes.
  6. Imagen a tirones: 20 fps reales dentro de un video de 60 fps.
  7. 4:3 estirado a 1440x1080.
  8. Cierre (~0.7 s): fondo negro, una imagen meme que crece y un texto corto.

Uso:  kedit.py plan.json salida.mp4
plan.json:
{
  "music": "tema.mp3", "music_start": 0,
  "hook":  {"path": "gd.mp4", "start": 3, "dur": 1.2},
  "clips": [{"path": "a.mp4", "start": 10, "dur": 1.2, "speed": 1.0, "grade": "warm",
             "fisheye": [0.6], "flash": [0.2]}, ...],
  "thermal": {"path": "b.mp4", "start": 5, "dur": 1.0},     (opcional)
  "end": {"image": "meme.png", "text": "крейзи o_0", "dur": 0.7}
}
Grades: warm, cold, neon, none.  fisheye/flash: segundos dentro del clip.
"""
import json, os, subprocess, sys, tempfile

W, H, FPS = 1440, 1080, 60
GRADES = {
    "warm": "eq=contrast=1.12:saturation=1.35:gamma=0.95,colorbalance=rs=0.06:bs=-0.08",
    "cold": "eq=contrast=1.05:saturation=0.55:brightness=0.05,colorbalance=bs=0.10:rs=-0.05",
    "neon": "eq=contrast=1.25:saturation=1.8,colorbalance=gs=0.18:bs=0.14:rs=-0.1",
    "hook": "eq=contrast=1.2:saturation=1.7",
    "none": "null",
}

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:])

def base(i, start, dur, speed=1.0):
    """Recorte, velocidad, 4:3 estirado y tirones a 20 fps."""
    return (["-ss", str(start), "-t", str(dur / speed * speed if speed else dur), "-i", i],
            f"setpts=PTS/{speed},scale={W}:{H},setsar=1,fps=20,fps={FPS}")

def windows(ts, width):
    return "+".join(f"between(t,{t:.3f},{t + width:.3f})" for t in ts) or "0"

def clip(src, out, c, grade):
    speed = c.get("speed", 1.0)
    vf = [f"setpts=PTS/{speed}", f"scale={W}:{H}", "setsar=1", GRADES.get(grade, "null")]
    fe = windows(c.get("fisheye", []), 0.18)
    if c.get("fisheye"):
        vf.append(f"lenscorrection=k1=-0.42:k2=0.12:enable='{fe}'")
    fl = windows(c.get("flash", []), 0.07)
    if c.get("flash"):
        vf.append(f"eq=brightness=0.55:contrast=0.7:enable='{fl}'")
    # Temblor en los mismos golpes: recorte que se mueve y vuelve a escala.
    sh = windows(c.get("fisheye", []) + c.get("flash", []), 0.15)
    vf += [f"crop=iw-48:ih-36:x='24+22*sin(t*90)*({sh})':y='18+16*cos(t*77)*({sh})'", f"scale={W}:{H}",
           "fps=20", f"fps={FPS}", "format=yuv420p"]
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(c["start"]), "-t", str(c["dur"] * speed), "-i", src,
         "-an", "-vf", ",".join(vf), "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "fast", out])

def thermal(src, out, c, beats):
    """Negativo + posterizado + grano; el color cambia en cada golpe."""
    dur = c["dur"]
    # Verde, naranja, azul: el color de cada tramo (la luz alta sigue casi blanca).
    tints = [(0.35, 1.0, 0.25), (1.0, 0.55, 0.12), (0.2, 0.45, 1.0)]
    cuts = [0] + [b for b in beats if 0 < b < dur] + [dur]
    parts = []
    for k in range(len(cuts) - 1):
        a, b = cuts[k], cuts[k + 1]
        r, g, b2 = tints[k % len(tints)]
        parts.append(f"colorchannelmixer=rr={r}:gg={g}:bb={b2}:enable='between(t,{a:.3f},{b:.3f})'")
    vf = [f"scale={W}:{H}", "setsar=1", "format=gray", "negate", "eq=contrast=2.6:brightness=0.1",
          "format=gbrp"] + parts + ["format=yuv420p"] + \
         ["noise=alls=42:allf=t", "vignette=PI/3.2", "fps=20", f"fps={FPS}"]
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(c["start"]), "-t", str(dur), "-i", src, "-an",
         "-vf", ",".join(vf), "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "fast", out])

def text_png(text, path):
    """El texto del cierre como imagen (el ffmpeg de Homebrew no trae drawtext)."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Times New Roman.ttf", 46)
    box = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=font)
    img = Image.new("RGBA", (box[2] - box[0] + 8, box[3] - box[1] + 12), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((4 - box[0], 4 - box[1]), text, font=font, fill="white")
    img.save(path)

def endcard(out, e):
    dur = e.get("dur", 0.7)
    inputs = ["-f", "lavfi", "-t", str(dur), "-i", f"color=black:s={W}x{H}:r={FPS}"]
    fc = "[0:v]null[bg]"
    n = 1
    if e.get("image"):
        inputs += ["-loop", "1", "-t", str(dur), "-i", e["image"]]
        # La imagen crece hasta 220 px de alto, en el centro, un poco arriba.
        fc = (f"[1:v]scale=-2:220,format=rgba[m];"
              f"[m]scale=w='iw*(0.5+0.5*min(1,t/{dur * 0.6}))':h=-2:eval=frame[mz];"
              f"[0:v][mz]overlay=x=(W-w)/2:y=(H-h)/2-60:eval=frame[bg]")
        n = 2
    if e.get("text"):
        tp = out + ".text.png"
        text_png(e["text"], tp)
        inputs += ["-loop", "1", "-t", str(dur), "-i", tp]
        fc += f";[bg][{n}:v]overlay=x=(W-w)/2:y=H/2+80[bg2]"
        fc += ";[bg2]format=yuv420p[v]"
    else:
        fc += ";[bg]format=yuv420p[v]"
    run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", fc, "-map", "[v]", "-r", str(FPS),
         "-c:v", "libx264", "-crf", "16", "-preset", "fast", out])

def beats(music, start, total):
    """Golpes de la música por energía (sin dependencias)."""
    import struct
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(total), "-i", music, "-ac", "1",
                          "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
    n = len(raw) // 2
    if n < 800:
        return []
    a = struct.unpack("<%dh" % n, raw)
    w = 400
    env = [(sum(x * x for x in a[i:i + w]) / w) ** 0.5 for i in range(0, n - w, w)]
    mx = max(env) or 1
    out, last = [], -1
    for i in range(1, len(env)):
        t = i * 0.05
        if env[i] > env[i - 1] * 1.6 and env[i] > mx * 0.3 and t - last > 0.25:
            out.append(t); last = t
    return out

def main():
    plan, dest = json.load(open(sys.argv[1])), sys.argv[2]
    tmp = tempfile.mkdtemp(prefix="kedit-")
    segs, t = [], 0.0
    total = (plan.get("hook", {}).get("dur", 0) + sum(c["dur"] for c in plan["clips"]) +
             plan.get("thermal", {}).get("dur", 0) + plan.get("end", {}).get("dur", 0))
    bts = beats(plan["music"], plan.get("music_start", 0), total) if plan.get("music") else []

    def add(path):
        segs.append(path)

    if "hook" in plan:
        h = plan["hook"]; p = f"{tmp}/0hook.mp4"
        clip(h["path"], p, {**h, "flash": [h["dur"] - 0.08]}, "hook"); add(p); t += h["dur"]
    th = plan.get("thermal")
    for i, c in enumerate(plan["clips"]):
        # La ráfaga térmica entra antes del último clip, como en la referencia.
        if th and i == len(plan["clips"]) - 1:
            p = f"{tmp}/{i}th.mp4"
            thermal(th["path"], p, th, [b - t for b in bts]); add(p); t += th["dur"]
        p = f"{tmp}/{i}c.mp4"
        clip(c["path"], p, c, c.get("grade", "warm")); add(p); t += c["dur"]
    if "end" in plan:
        p = f"{tmp}/zend.mp4"; endcard(p, plan["end"]); add(p)

    lst = f"{tmp}/list.txt"
    open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
    video = f"{tmp}/video.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])
    if plan.get("music"):
        run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ss", str(plan.get("music_start", 0)), "-i", plan["music"],
             "-map", "0:v", "-map", "1:a", "-shortest", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-af", "afade=t=out:st=%.2f:d=0.25" % max(0, total - 0.25), dest])
    else:
        os.replace(video, dest)
    print(dest, "beats:", [round(b, 2) for b in bts])

if __name__ == "__main__":
    main()

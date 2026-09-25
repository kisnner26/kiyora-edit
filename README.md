# kiyora-edit

Editor de video por línea de comandos, hecho con **ffmpeg + Python**, que monta videos cortos en dos estilos a partir de un plan en JSON. Nació como una *skill* para Claude Code, pero funciona solo.

| estilo | script | para qué |
|---|---|---|
| **k1yora** | `kedit.py` | frag movie de TikTok (8-15 s): gancho saturado, grades distintos por clip, ojo de pez en los giros, ráfaga "térmica" que cambia de color con cada golpe de la música, destellos, 20 fps a tirones, 4:3 estirado y cierre con imagen y texto |
| **Apple** | `kapple.py` | reveal de producto: negro, planos largos con empuje suave, barrido de luz sobre el metal, títulos en SF Pro que se forman desde un desenfoque, cifras enormes, barras de cine y cierre con la marca |

## Requisitos
- macOS o Linux con `ffmpeg` (el de Homebrew sirve; **no** necesita `drawtext`: el texto se dibuja con Pillow)
- Python 3.9+ y `pip install pillow`
- Para el estilo Apple, la fuente **SF Pro Display** en `/Library/Fonts` (si no está, usa SFNS del sistema)

## Uso
```bash
python3 kedit.py  ejemplos/k1yora.json salida.mp4
python3 kapple.py ejemplos/apple.json  salida.mp4
```
Los ejemplos usan nombres de archivo de muestra: cámbialos por tus clips, capturas y música.

### Plan k1yora (`kedit.py`)
- `hook`: clip gancho (`path`, `start`, `dur`)
- `clips`: jugadas con `grade` (`warm`, `cold`, `neon`, `none`), `speed`, y los segundos (dentro del clip) donde van `fisheye` y `flash`
- `thermal`: la ráfaga térmica, entra antes del último clip; cambia de color en cada golpe de la música (se detectan solos)
- `end`: `image` y `text` del cierre

### Plan Apple (`kapple.py`)
- `shots`: video o imagen (`still: true`) con `speed`, `push` (zoom final), `sweep` (barrido de luz), `cine` (barras 2.39:1), `cut` (corte seco en vez de fundido), `mono` (0 = blanco y negro, 1 = color original)
- `titles`: `after` (índice del plano tras el que entra), `text`, `sub`, `gradient` (dos colores RGB), `number` (cifra enorme), `size`
- `end`: `text` y `sub`

## Música propia
`musica/ambiente.py` genera un pad ambiental de ~31 s sin samples (La menor add9 → Fa maj7 → Do add9 → Sol sus → La menor), con golpes graves en 7,2 s y 26 s:
```bash
python3 musica/ambiente.py musica.wav
ffmpeg -i musica.wav -af "aecho=0.8:0.7:120|240:0.35|0.2,alimiter" musica_rev.wav
```

## Referencias
- `apple-reference.md`: cómo hace Apple sus videos y presentaciones (estructura, luz, movimiento, tipografía, ritmo, sonido) y una lista de comprobación.
- `SKILL.md`: la anatomía de ambos estilos segundo a segundo y notas técnicas.

Los videos de referencia que se analizaron no se incluyen: pertenecen a sus autores.

## Licencia
MIT

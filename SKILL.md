---
name: kiyora-edit
description: Edita videos en dos estilos. (1) "k1yora" (frag movie de TikTok, 8-15 s): gancho saturado, clips con grade distinto, ojo de pez en los giros, ráfaga térmica que cambia de color con la música, destellos, imagen a tirones a 20 fps, 4:3 estirado y cierre con imagen meme y texto. Usar cuando Kisnner pida editar un video "como el de k1yora", "con ese estilo", un edit de CS2/Geometry Dash/gameplay para TikTok, o cuando pase clips y música para montar. (2) "apple": reveal de producto como los de Apple (negro, planos lentos con empuje, barridos de luz, títulos SF Pro que se forman desde un desenfoque, barras de cine, cierre con marca); usar cuando pida "estilo Apple", "como un keynote", "reveal", "anuncio de producto" o un video de presentación de sus apps.
---

# Edición estilo k1yora

Referencia analizada: un TikTok de @k1yora (8,1 s, 1440x1080, 60 fps; no incluido).

## Anatomía de la referencia (segundo a segundo)
| tramo | qué pasa |
|---|---|
| 0,0-1,2 | **Gancho**: clip ajeno muy saturado (Geometry Dash), cortes cada ~0,2 s, destello al salir |
| 1,2-2,4 | Jugada 1 (Dust2, AWP): grade cálido, **ojo de pez** en el giro rápido, temblor en el disparo |
| 2,4-3,5 | Jugada 2 (Mirage): grade frío/lavado, casi sin saturación |
| 3,5-4,5 | **Ráfaga térmica**: negativo + contraste + grano fuerte + viñeta; el color cambia en cada golpe (verde → naranja → azul) |
| 4,5-7,3 | Jugada 3 (Nuke): cálido, ojo de pez, destellos; el último disparo en **neón verde/violeta** |
| 7,4-8,1 | **Cierre**: fondo negro, foto meme pequeña que crece, texto corto en serif ("крейзи o_0") |

Constantes: la imagen cambia cada 3 cuadros (**20 fps reales dentro de 60**), 4:3 estirado, sin transiciones suaves (todo corte seco), la música manda: los efectos caen en los golpes.

## Herramienta
`python3 ~/.claude/skills/kiyora-edit/kedit.py plan.json salida.mp4`

El plan (JSON) lleva música, gancho, clips (con `grade`: warm/cold/neon/none, `speed`, y segundos de `fisheye` y `flash` dentro de cada clip), la ráfaga `thermal` (entra antes del último clip) y el cierre `end` (imagen + texto). Los golpes de la música se detectan solos por energía.

## Cómo trabajar
1. Pedir o localizar: clips de juego, una canción, el clip del gancho y la imagen del cierre.
2. Mirar cada clip (hoja de contacto con `ffmpeg -vf fps=6,scale=300:-1,tile=8x6`) y anotar el segundo del giro y del disparo: ahí van `fisheye` y `flash`.
3. Duraciones: gancho ~1,2 s, jugadas 1-3 s, térmica ~1 s, cierre ~0,7 s. Total 8-15 s.
4. Renderizar y **revisar cuadros** del resultado antes de entregarlo (hoja de contacto de la salida).
5. Salida a 1440x1080 (4:3). Si es para TikTok vertical, preguntar si quiere barras o recorte.

## Notas técnicas
- El ffmpeg de Homebrew no trae `drawtext`: el texto se genera como PNG con Pillow y se superpone.
- `hue`/`colorize` no tiñen bien una imagen en gris: la térmica usa `colorchannelmixer` por tramos.
- No reutilizar contenido de otros creadores en lo que se publique: la referencia solo sirve para estudiar el estilo.


# Estilo Apple (reveal de producto)

Referencia analizada: el video "iPhone 15 Pro Reveal" de Apple (35 s; no incluido).

## Anatomía
| rasgo | cómo es |
|---|---|
| Luz | fondo negro, luz baja y lateral; el material brilla, el resto desaparece |
| Color | casi monocromo (saturación ~0,25), sombras hundidas pero legibles |
| Planos | pocos y largos (2,5-10 s); 7 cortes en 35 s; cámara lenta |
| Movimiento | empuje lento constante (zoom 1,00 → 1,06), nunca cámara en mano |
| Transiciones | entradas/salidas por negro; cortes secos solo en golpes de la música |
| Luz viva | barrido de brillo diagonal que recorre el metal |
| Tipografía | una palabra ("Titanium"), SF Pro, gris claro, grande y centrada, que se forma desde un desenfoque |
| Formato | 16:9 con barras 2.39:1 en los planos de detalle |
| Música | empieza casi en silencio, crece; fundido final de imagen y sonido |

## Herramienta
`python3 ~/.claude/skills/kiyora-edit/kapple.py plan.json salida.mp4` (1920x1080, 30 fps)

Plan: `music`, `shots` (video o `still: true` para capturas; `speed`, `push`, `sweep`, `cine`, `cut`, `mono`), `titles` (`after`: índice del plano tras el que entra, `text`, `sub`, `dur`) y `end` (`text`, `sub`). Las capturas de pantalla se muestran enteras sobre negro, como un producto flotando.

## Opciones nuevas
- `gradient: [[r,g,b],[r,g,b]]` en un título: degradado vertical (metal, o el color de la app).
- `number: true` + `sub`: tarjeta de cifra enorme ("2x" / "más rápido").
- El empuje usa curva suave (arranca y frena despacio).

**Antes de planear un video Apple, leer `apple-reference.md`** (estructura hero → detalles → contexto → cierre, luz, movimiento, tipografía, ritmo, sonido y checklist).

## Consejos
- Para apps (Zarcillo, Girasol…): graba la pantalla del iPhone/Mac, usa planos cortos de la interfaz con `still` o video, una palabra por idea ("Pantalla.", "Cerebro.", "Jardín.") y cierra con el nombre.
- La fuente es la SF Pro instalada en `/Library/Fonts`; si no está, usa SFNS del sistema.
- `crop` no acepta `t` en ancho/alto: el empuje se hace con `zoompan` (d=1).

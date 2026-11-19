# Demo film

The Antibody Guard demo film (3:23, 1920×1080, 30 fps), built from code so it can be re-rendered when the app changes.

| Step | File | What it does |
|---|---|---|
| 1 | `script.json` | The narration, by scene. |
| 2 | `tts.py` | Voices each line with Kokoro-82M, voice `af_heart` → `vo/*.wav`. |
| 3 | `timeline.py` | Lays the lines on a clock → `timeline.json` (scene and line start/end times). |
| 4 | `stage.html` | The compositor. `window.render(t)` draws the frame at time `t`; `window.CUES` is the sound-cue sheet on the same clock. |
| 5 | `cues.cjs` | Exports the cue sheet → `cues.json`. |
| 6 | `audio.py` | Voice polish, music cut to the picture, sound design from the cues, ducking → `mix.wav`. |
| 7 | `render.cjs` | Renders a frame range to an MP4 segment with Playwright (run four in parallel). |
| 8 | `mux.sh` | Joins the segments, masters the audio to −14 LUFS / −1 dBTP, muxes, makes a web copy. |

`preview.cjs` renders stills at given times for review.

Inputs that are not in git: screenshots of the live console in `shots/` (1600×900 at 2×), Mixkit sound effects in `sfx/<id>.wav`, and the two Mixkit music tracks (Silent Descent, Vertigo) as 48 kHz WAV.

Credits: voice by Kokoro-82M (Apache 2.0); music and sound effects from Mixkit (Mixkit free license), layered with synthesised sound design.

"""
Sound for the Antibody Guard demo film: the af_heart voiceover, a score cut to the picture from two Mixkit tracks
(Silent Descent, Vertigo), and sound design from Mixkit samples layered with synthesised sub-bass, risers and pings.
Every cue comes from stage.html (cues.json), on the same clock as the picture. 48 kHz stereo.

  python audio.py <video dir> <music dir>   ->  vo.wav, music.wav, sfx.wav, mix.wav

Samples: <video dir>/sfx/<mixkit id>.wav (48 kHz stereo). Music: <music dir>/{Silent_Descent,Vertigo}.wav.
Mixkit sound effects and music are used under the Mixkit free license.
"""
import json, sys
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly

V, M = sys.argv[1], sys.argv[2]
SR = 48000
TL = json.load(open(f'{V}/timeline.json'))
CUES = json.load(open(f'{V}/cues.json'))
DUR = TL['duration'] + 0.5
N = int(DUR * SR)
rng = np.random.default_rng(42)
S = {s['id']: s for s in TL['scenes']}


def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x, axis=0)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x, axis=0)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x, axis=0)


def st(x):
    return x if x.ndim == 2 else np.stack([x, x], 1)


def fade(x, a=0.005, r=0.08):
    x = x.copy()
    na, nr = min(len(x), int(a * SR)), min(len(x), int(r * SR))
    if na: x[:na] *= np.linspace(0, 1, na)[:, None]
    if nr: x[-nr:] *= np.linspace(1, 0, nr)[:, None] ** 2
    return x


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def pan(x, p):
    a = (p + 1) * np.pi / 4
    x = st(x)
    return np.stack([x[:, 0] * np.cos(a) * 1.414, x[:, 1] * np.sin(a) * 1.414], 1)


def add(buf, x, t0, g=1.0):
    i = int(round(t0 * SR))
    x = st(x)
    if i < 0:
        x, i = x[-i:], 0
    if i >= len(buf) or not len(x):
        return
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i] * g


def make_ir(sec, decay, bright):
    n = int(sec * SR)
    tt = np.arange(n) / SR
    ir = np.stack([rng.standard_normal(n), rng.standard_normal(n)], 1) * np.exp(-decay * tt)[:, None]
    ir = lp(ir, bright)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
    return ir / np.sqrt((ir ** 2).sum(0, keepdims=True))


IR_HALL, IR_ROOM = make_ir(3.0, 2.2, 7000), make_ir(1.0, 6.0, 9000)


def verb(x, ir, wet):
    x = st(x)
    out = np.stack([fftconvolve(x[:, 0], ir[:, 0]), fftconvolve(x[:, 1], ir[:, 1])], 1)
    dry = np.zeros_like(out)
    dry[: len(x)] = x
    return dry + out * wet


# ---------------------------------------------------------------- samples
_cache = {}


def smp(i):
    if i not in _cache:
        x, sr = sf.read(f'{V}/sfx/{i}.wav', always_2d=True)
        assert sr == SR, (i, sr)
        _cache[i] = norm(x, 1.0)
    return _cache[i]


def onset(x):
    m = np.abs(x).max(1)
    return int(np.argmax(m > 0.03))


def peak(x):
    return int(np.argmax(np.abs(x).max(1)))


def take(i, maxlen=None, start=0.0, rel=0.12, at='onset'):
    """A sample trimmed to maxlen seconds after its onset (or from `start`), and the offset (s) of its anchor."""
    x = smp(i)
    s0 = int(start * SR) if start else onset(x)
    a = (peak(x) - s0) / SR if at == 'peak' else 0.0
    x = x[s0:]
    if maxlen:
        x = x[: int(maxlen * SR)]
    return fade(x, 0.003, min(rel, len(x) / SR / 2)), a


# ---------------------------------------------------------------- synthesis
def tt(sec):
    return np.arange(int(sec * SR)) / SR


def sub(sec=1.4, f0=72, f1=36, g=1.0):
    t = tt(sec)
    f = f1 + (f0 - f1) * np.exp(-t * 5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return st(np.sin(ph) * np.exp(-t * 3.2) * np.minimum(1, t / 0.004) * g)


def noise_sweep(sec, f0, f1, up=True):
    t = tt(sec)
    n = rng.standard_normal(len(t))
    k = t / sec
    out = np.zeros_like(n)
    # stepped band-pass sweep (cheap): 24 overlapping segments
    seg = len(t) // 24 + 1
    for s in range(24):
        a, b = s * seg, min(len(t), (s + 1) * seg + seg // 2)
        fc = f0 * (f1 / f0) ** (s / 23)
        y = bp(n[a:b], fc * 0.7, min(fc * 1.4, SR * 0.45))
        w = np.hanning(b - a)
        out[a:b] += y * w
    env = k ** 2.2 if up else (1 - k) ** 1.6
    return st(out * env)


def ping(f=1180, sec=1.8):
    t = tt(sec)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 5) + 0.35 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t * 9)
    x = st(x * np.minimum(1, t / 0.002))
    return verb(x * 0.8, IR_HALL, 0.5)


def bell(f, sec=2.6):
    t = tt(sec)
    mod = 2.2 * np.exp(-t * 3) * np.sin(2 * np.pi * f * 3.5 * t)
    return st(np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 2.2) * np.minimum(1, t / 0.003))


# ---------------------------------------------------------------- kinds
ROT = {}


def rot(kind, opts):
    k = ROT.get(kind, 0)
    ROT[kind] = k + 1
    return opts[k % len(opts)]


def sfx(kind, arg):
    """Returns a list of (stereo audio, offset seconds relative to the cue, gain)."""
    L = []
    if kind == 'boom':
        x, a = take('488', 5.0, at='peak', rel=1.5); L += [(x, -a, 0.9), (sub(2.2, 64, 30), 0, 0.95)]
    elif kind == 'impact':
        x, _ = take('677', 3.6, rel=1.2); L += [(x, 0, 1.0), (sub(1.6), 0, 0.85)]
        y, _ = take('1287', 2.4, at='peak', rel=0.8); L += [(y, 0, 0.35)]
    elif kind == 'hit':
        x, _ = take('784', 1.8, rel=0.6); L += [(x, 0, 0.9), (sub(0.9, 80, 42), 0, 0.6)]
    elif kind == 'whoosh':
        i, ml = rot(kind, [('1491', 1.4), ('2638', 2.0), ('1486', 2.0), ('1484', 1.5)])
        x, a = take(i, ml + 1.2, at='peak', rel=0.5); L += [(x, 0.22 - a, 0.8)]
    elif kind == 'swoosh':
        i = rot(kind, ['2577', '3123', '1484'])
        x, a = take(i, 1.3, rel=0.4); L += [(x, -0.02, 0.75)]
    elif kind == 'zoom':
        i = rot(kind, ['2860', '2521'])
        x, _ = take(i, 1.4, rel=0.4); L += [(x, -0.02, 0.6)]
    elif kind == 'pop':
        i = rot(kind, ['2573', '1113', '2568'])
        x, _ = take(i, 0.7, rel=0.2); L += [(pan(x, rng.uniform(-0.25, 0.25)), 0, 0.55)]
    elif kind == 'blip':
        i = rot(kind, ['2602', '3117'])
        x, _ = take(i, 0.6, rel=0.2); L += [(pan(x, rng.uniform(-0.3, 0.3)), 0, 0.42)]
    elif kind == 'tick':
        x, _ = take('1113', 0.4, rel=0.15); L += [(pan(x, rng.uniform(-0.15, 0.15)), 0, 0.6)]
    elif kind == 'success':
        i = rot(kind, ['2619', '911', '2867'])
        x, _ = take(i, 1.8, rel=0.5); L += [(x, 0, 0.6)]
    elif kind == 'error':
        x, _ = take('2820', 2.2, rel=0.6); L += [(x, 0, 0.75)]
    elif kind == 'deny':
        i = rot(kind, ['2578', '1084'])
        x, _ = take(i, 0.8, rel=0.25); L += [(x, 0, 0.5)]
    elif kind == 'alarm':
        x, _ = take('908', 1.4, rel=0.5); L += [(x, 0, 0.45)]
    elif kind == 'alert':
        x, _ = take('2634', 1.3, rel=0.4); L += [(x, 0, 0.5)]
    elif kind == 'notify':
        x, _ = take('3117', 1.6, rel=0.5); L += [(x, 0, 0.55)]
    elif kind == 'glitch':
        i, ml = rot(kind, [('2951', 1.0), ('1022', 0.8), ('1044', 1.2)])
        x, _ = take(i, ml, rel=0.15); L += [(x, 0, 0.75)]
    elif kind == 'stamp':
        x, _ = take('2851', 1.1, rel=0.3); y, _ = take('784', 1.0, rel=0.4); L += [(x, 0, 0.8), (y, 0, 0.45), (sub(0.6, 90, 50), 0, 0.4)]
    elif kind == 'lock':
        i = rot(kind, ['2850', '2854', '2853'])
        x, _ = take(i, 1.1, rel=0.3); L += [(x, 0, 0.6)]
    elif kind == 'freeze':
        x, _ = take('2950', 3.0, rel=1.2); L += [(x, 0, 0.7), (noise_sweep(1.4, 9000, 2500, up=False), 0, 0.25)]
    elif kind == 'sweep':
        x, a = take('1486', 3.0, at='peak', rel=1.0); L += [(x, -a + 0.1, 0.7), (noise_sweep(1.6, 300, 3000, up=False), 0, 0.3), (sub(1.8, 58, 32), 0, 0.7)]
    elif kind == 'sonar':
        for j in range(3): L += [(ping(1180 if j % 2 == 0 else 990), j * 1.1, 0.35 * (0.75 ** j))]
    elif kind == 'scan':
        x, _ = take('2135', 1.7, start=0.2, rel=0.4); L += [(x, 0, 0.4), (noise_sweep(1.6, 600, 6000), 0, 0.12)]
    elif kind == 'data':
        i = rot(kind, ['2135', '3116'])
        x, _ = take(i, float(arg), start=0.05, rel=0.3); L += [(x, 0, 0.32)]
    elif kind == 'typing':
        x = smp('2531')
        s0 = int(rng.uniform(0.3, 19.0 - float(arg) - 0.3) * SR)
        L += [(fade(x[s0: s0 + int(float(arg) * SR)], 0.02, 0.15), 0, 0.5)]
    elif kind == 'riser':
        L += [(noise_sweep(1.6, 300, 7000), -1.4, 0.55)]
    elif kind == 'swell':
        x, _ = take('2501', 4.0, start=0.01, rel=1.5); L += [(x * np.linspace(0, 1, len(x))[:, None] ** 0.5, 0, 0.6)]
    elif kind == 'reverse':
        x, a = take('2900', 4.6, start=0.01, at='peak', rel=0.05); L += [(x, -a, 0.75)]
    elif kind == 'shimmer':
        x, _ = take('2950', 3.6, rel=1.4); L += [(x, 0, 0.5)]
    elif kind == 'chime':
        x, _ = take('911', 2.0, rel=0.6); L += [(x, 0, 0.5), (verb(bell(880) * 0.4 + bell(1318.5) * 0.25, IR_HALL, 0.5), 0, 0.35)]
    elif kind == 'bed':
        x, _ = take('2135', float(arg), start=1.0, rel=1.2); L += [(lp(x, 2500) * np.hanning(len(x))[:, None], 0, 0.35)]
    else:
        raise ValueError(kind)
    return L


# ---------------------------------------------------------------- voice
def make_vo():
    vo = np.zeros(N)
    for s in TL['scenes']:
        for l in s['lines']:
            a, sr = sf.read(l['file'])
            if a.ndim == 2: a = a.mean(1)
            a = resample_poly(a, SR, sr) if sr != SR else a
            i = int(l['start'] * SR)
            vo[i: i + len(a)] += a[: max(0, N - i)]
    # polish: high-pass rumble, a little presence and air, gentle compression, a short room
    vo = hp(vo, 85)
    vo = vo + bp(vo, 2500, 6000) * 0.22 + hp(vo, 9000) * 0.12
    env = np.sqrt(np.maximum(lp(vo ** 2, 12), 0) + 1e-9)
    vo = vo * np.where(env > 0.1, (0.1 / env) ** 0.45, 1)
    x = st(vo)
    room = verb(x * 0.5, IR_ROOM, 0.12)[:N] - x * 0.5
    return norm(x + room * 0.3, 0.9), vo


# ---------------------------------------------------------------- music
def music_track():
    sd, _ = sf.read(f'{M}/Silent_Descent.wav', always_2d=True)
    vt, _ = sf.read(f'{M}/Vertigo.wav', always_2d=True)
    out = np.zeros((N, 2))
    reveal = S['reveal']['start'] + 0.5  # the logo impact
    build = S['build']['lines'][0]['start'] - 0.3  # "Any agent can use it today."

    def place(src, v0, t0, t1, fin, fout, g=1.0):
        a, b = int(v0 * SR), int((v0 + t1 - t0) * SR)
        x = src[a:b].copy()
        n = len(x)
        fi, fo = int(fin * SR), int(fout * SR)
        if fi: x[:fi] *= np.linspace(0, 1, fi)[:, None] ** 0.7
        if fo: x[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
        add(out, x, t0, g)

    # act 1: Silent Descent from the top, out under the reveal
    place(sd, 0.0, 0.0, reveal + 0.6, 1.5, 1.4, 1.0)
    # act 2: Vertigo, its re-entry (52 s) on the logo impact, up to just before its own break (~176 s)
    o1 = 52.0 - reveal
    place(vt, reveal - 0.9 + o1, reveal - 0.9, build + 0.25, 0.9, 0.5, 0.82)
    # act 3: Vertigo after the break (184 s) on "Any agent can use it today", into its natural fade at the close
    place(vt, 184.0, build, DUR, 0.06, 4.5, 0.82)
    return out


def main():
    print('voice…', flush=True)
    vo, vo_mono = make_vo()
    print('sfx…', flush=True)
    fx = np.zeros((N, 2))
    for t, kind, g in CUES:
        k, _, arg = kind.partition(':')
        for x, off, gg in sfx(k, arg):
            add(fx, x, t + off, g * gg)
    # glue the sound design with a touch of hall
    fx = verb(fx, IR_HALL, 0.10)[:N]
    print('music…', flush=True)
    music = norm(music_track(), 0.9)
    # sidechain: duck the music under the voice (about -8 dB), the sound design a little (-3 dB)
    e = lp(np.abs(vo_mono), 30)
    e = e / (np.percentile(e[e > 1e-4], 95) or 1)
    att, rel = np.exp(-64 / (0.03 * SR)), np.exp(-64 / (0.5 * SR))
    sm = np.zeros(N)
    acc = 0.0
    for i in range(0, N, 64):
        v = min(1.0, e[i])
        acc = att * acc + (1 - att) * v if v > acc else rel * acc + (1 - rel) * v
        sm[i: i + 64] = acc
    duck_m = 1 - 0.6 * np.clip(sm * 1.4, 0, 1)
    duck_s = 1 - 0.3 * np.clip(sm * 1.4, 0, 1)
    fxn = norm(fx, 0.9)
    sf.write(f'{V}/vo.wav', vo, SR, subtype='PCM_24')
    sf.write(f'{V}/music.wav', music, SR, subtype='PCM_24')
    sf.write(f'{V}/sfx.wav', fxn, SR, subtype='PCM_24')
    mix = vo * 1.0 + music * 0.34 * duck_m[:, None] + fxn * 0.5 * duck_s[:, None]
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)  # soft clip safety
    sf.write(f'{V}/mix.wav', norm(mix, 0.95), SR, subtype='PCM_24')
    print('done', round(N / SR, 1), 's')


main()

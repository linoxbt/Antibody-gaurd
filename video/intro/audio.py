"""
Sound for the Antibody Guard intro (no voice). The score is Deep Techno Ambience (Mixkit) from 27.312 s, so its bass
drop lands on the logo at 10.908 s; it drops out for "Fooled once." and slams back on "Never twice.". The sound design
reuses the film's sample kinds (../audio.py) and adds trailer braams and heartbeat thumps.

  python intro/audio.py <intro dir> <music dir>   ->  music.wav, sfx.wav, mix.wav   (music dir holds Deep_Techno_Ambience.wav)
"""
import os, sys
import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import audio as A  # noqa: E402  (reads argv: the intro dir and the music dir)

SR, N = A.SR, A.N
B, D = 0.5457, 10.908
E1, E2 = D + 40 * B, D + 43 * B  # "Fooled once." (music out) and "Never twice." (music back)
OFFSET = 27.312


def braam(sec=2.6, root=36.71):
    """Trailer brass: detuned saws an octave and a fifth apart, a filter that opens then closes, hall."""
    t = A.tt(sec)
    x = np.zeros(len(t))
    for f, g in [(root, 1.0), (root * 2, 0.8), (root * 3, 0.45), (root * 4, 0.3)]:
        for det in (-0.25, 0, 0.25):
            ff = f * (1 + det / 100)
            x += g * (2 * ((ff * t + np.random.default_rng(int(ff)).random()) % 1) - 1)
    x /= np.abs(x).max()
    dark, bright = A.lp(x, 260), A.lp(x, 2400)
    open_ = np.minimum(1, t / 0.12) * np.exp(-t * 1.6)
    y = dark * (1 - open_) + bright * open_
    y = np.tanh(y * 2.2) * np.minimum(1, t / 0.02) * np.exp(-t * 0.9)
    return A.verb(A.st(y), A.IR_HALL, 0.45)


def thump():
    a = A.sub(0.45, 95, 48, 1.0)
    b = A.sub(0.4, 80, 44, 0.6)
    out = np.zeros((len(a) + int(0.2 * SR), 2))
    out[: len(a)] += a
    out[int(0.2 * SR): int(0.2 * SR) + len(b)] += b
    return out


def sfx(kind, arg):
    if kind == 'braam':
        return [(braam(), 0, 0.8)]
    if kind == 'thump':
        return [(thump(), 0, 0.9)]
    return A.sfx(kind, arg)


def music():
    x, sr = sf.read(f'{A.M}/Deep_Techno_Ambience.wav', always_2d=True)
    assert sr == SR
    m = x[int(OFFSET * SR): int(OFFSET * SR) + N].copy()
    if len(m) < N:
        m = np.concatenate([m, np.zeros((N - len(m), 2))])
    g = np.ones(N)
    i0, i1 = int((E1 - 0.03) * SR), int(E2 * SR)
    g[i0 - int(0.04 * SR): i0] = np.linspace(1, 0, int(0.04 * SR))
    g[i0:i1] = 0
    # the tail of the music rings into the drop-out through a long reverb instead of stopping dead
    tail = A.verb(m[i0 - int(0.3 * SR): i0] * np.linspace(0, 1, int(0.3 * SR))[:, None], A.IR_HALL, 1.0)
    fo0 = int((A.TL['duration'] - 2.6) * SR)
    g[fo0:] *= np.linspace(1, 0, N - fo0) ** 1.4
    g[: int(0.4 * SR)] *= np.linspace(0, 1, int(0.4 * SR))
    out = m * g[:, None]
    A.add(out, tail * 0.5, E1 - 0.33)
    return out


def main():
    fx = np.zeros((N, 2))
    for t, kind, g in A.CUES:
        k, _, arg = kind.partition(':')
        for x, off, gg in sfx(k, arg):
            A.add(fx, x, t + off, g * gg)
    fx = A.verb(fx, A.IR_HALL, 0.12)[:N]
    mu = A.norm(music(), 0.9)
    fxn = A.norm(fx, 0.9)
    # the music ducks a little under the big hits so they punch through
    e = A.lp(np.abs(fxn).max(1), 8)
    duck = 1 - 0.35 * np.clip(e / (np.percentile(e, 99) or 1), 0, 1)
    sf.write(f'{A.V}/music.wav', mu, SR, subtype='PCM_24')
    sf.write(f'{A.V}/sfx.wav', fxn, SR, subtype='PCM_24')
    mix = mu * 0.55 * duck[:, None] + fxn * 0.8
    mix = np.tanh(mix * 1.15) / np.tanh(1.15)
    sf.write(f'{A.V}/mix.wav', A.norm(mix, 0.95), SR, subtype='PCM_24')
    print('done', round(N / SR, 1), 's')


main()

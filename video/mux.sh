#!/usr/bin/env bash
# Join the rendered segments, master the audio to -14 LUFS / -1 dBTP (two-pass loudnorm), mux, and make a web copy.
set -euo pipefail
V="$1"; OUT="$2"
cd "$V"
printf "file '%s'\n" seg0.mp4 seg1.mp4 seg2.mp4 seg3.mp4 > segs.txt
ffmpeg -loglevel error -y -f concat -safe 0 -i segs.txt -c copy video.mp4
J=$(ffmpeg -hide_banner -nostats -i mix.wav -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -loglevel error -y -i mix.wav -af "loudnorm=I=-14:TP=-1:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" -c:a pcm_s24le master.wav
ffmpeg -loglevel error -y -i video.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart \
  -metadata title="Antibody Guard — an immune system for AI agents" \
  -metadata comment="Antibody Guard on Reactive Network. Voice: Kokoro-82M (af_heart). Music and sound effects: Mixkit (free license), with original sound design." "$OUT"
# a lighter copy for the web and chat apps
ffmpeg -loglevel error -y -i "$OUT" -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "${OUT%.mp4}-web.mp4"
ffmpeg -hide_banner -nostats -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)" | tr -s ' '

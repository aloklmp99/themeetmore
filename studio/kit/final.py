import os, sys, json, subprocess
from multiprocessing import Pool
import importlib, subprocess as _sp, re as _re
b = importlib.import_module(os.environ.get('STORY', 'story001'))
globals().update({k: getattr(b, k) for k in dir(b) if not k.startswith('__')})
OUTNAME = os.environ.get('OUTNAME', 'out/final.mp4')

_r = _sp.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', 'voice.mp3'], capture_output=True, text=True)
_d = float(_r.stdout.strip())
TEMPO = float(os.environ.get('TEMPO', min(1.10, max(1.0, _d / 56.0))))
T = float(os.environ.get('TOTAL', min(59.6, max(55.0, _d / TEMPO + 0.4 + 3.0))))
print('voice', _d, 'tempo', TEMPO, 'total', T, flush=True)
tm = timing_from_audio('voice.mp3', tempo=TEMPO, total=T)
bounds = scene_bounds(tm)
json.dump({'tm': tm, 'bounds': bounds}, open('out/timing.json', 'w'), ensure_ascii=False)
os.makedirs('out/scenes', exist_ok=True)
NS = len(bounds) - 1
jobs = [(i, tm, bounds, f'out/scenes/s{i}.mp4') for i in range(NS)]
if __name__ == '__main__':
    with Pool(2) as pool:
        for r in pool.imap_unordered(render_scene, jobs):
            print('done', r, flush=True)
    with open('out/scenes/list.txt', 'w') as f:
        for i in range(NS):
            f.write(f"file 's{i}.mp4'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'out/scenes/list.txt',
                    '-c', 'copy', 'out/video_noaudio.mp4'], check=True)
    make_music(T, bounds, 'out/music.wav')
    af = (f"[0:a]atempo={TEMPO},adelay=400|400,volume=1.0[v];[1:a]volume=0.42[m];"
          f"[v][m]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,"
          f"afade=t=out:st={T-1.5}:d=1.5,atrim=0:{T},asetpts=PTS-STARTPTS[a]")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'voice.mp3', '-i', 'out/music.wav',
                    '-i', 'out/video_noaudio.mp4', '-filter_complex', af, '-map', '2:v', '-map', '[a]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-t', str(T),
                    '-movflags', '+faststart', OUTNAME], check=True)
    print('FINISHED')

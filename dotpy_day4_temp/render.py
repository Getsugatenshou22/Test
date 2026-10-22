import asyncio
import json
import pathlib
import random
import sys

import edge_tts
from mutagen.mp3 import MP3

SCENES = json.loads(pathlib.Path("dotpy_day4_temp/scenes.json").read_text(encoding="utf-8"))["narration"]
assert len(SCENES) == 52, f"Expected 52, got {len(SCENES)}"
DEST = pathlib.Path("voice")
DEST.mkdir(exist_ok=True)
VOICE = "en-ZA-LukeNeural"
SEM = asyncio.Semaphore(2)

async def render(i, text):
    path = DEST / f"{i:03d}.mp3"
    if path.exists() and path.stat().st_size > 2500:
        return i, path
    for attempt in range(1, 6):
        try:
            async with SEM:
                await asyncio.wait_for(
                    edge_tts.Communicate(text, voice=VOICE, rate="-4%").save(str(path)),
                    timeout=135,
                )
                if path.stat().st_size < 2500:
                    raise ValueError("Speech file unexpectedly short")
                d = MP3(str(path)).info.length
                if d < 5:
                    raise ValueError("Speech duration unexpectedly short")
                print(f"Scene {i+1:02d}/{len(SCENES)}: {d:.1f} seconds, {path.stat().st_size} bytes", flush=True)
                return i, path
        except Exception as e:
            print(f"Scene {i+1:02d} attempt {attempt}: {e}", flush=True)
            path.unlink(missing_ok=True)
            if attempt == 5:
                raise
            await asyncio.sleep(min(30, 2**attempt + random.random()))

async def main():
    results = await asyncio.gather(*(render(i,t) for i,t in enumerate(SCENES)))
    rows = []
    for i, p in sorted(results):
        rows.append({"i": i, "file": p.name, "duration": MP3(str(p)).info.length, "bytes": p.stat().st_size})
    (DEST/"manifest.json").write_text(json.dumps({"voice":VOICE,"scenes":rows},indent=2),encoding="utf-8")
    print("DONE:",len(rows),"scenes, total speech",round(sum(x["duration"] for x in rows),1),"seconds",flush=True)

if __name__ == "__main__":
    asyncio.run(main())

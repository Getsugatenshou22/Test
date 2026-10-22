import asyncio
import json
import pathlib
import random

import edge_tts
from mutagen.mp3 import MP3

DOC=json.loads(pathlib.Path('dotpy_day5_temp/scenes.json').read_text(encoding='utf-8'))
SCENES=DOC['narration']
assert len(SCENES)==59
VOICE='en-ZA-LukeNeural'
OUT=pathlib.Path('voice')
OUT.mkdir(exist_ok=True)
SEM=asyncio.Semaphore(2)

async def render_one(i,text):
    path=OUT/f'{i:03d}.mp3'
    for attempt in range(1,6):
        try:
            async with SEM:
                voice=edge_tts.Communicate(text,voice=VOICE,rate='-4%')
                await asyncio.wait_for(voice.save(str(path)),timeout=150)
                duration=MP3(str(path)).info.length
                if duration<12 or path.stat().st_size<4000:raise ValueError(f'Audio too short: {duration}')
                print(f'Day5 {i+1:02d}/{len(SCENES)} - {duration:.2f}s - {path.stat().st_size} bytes',flush=True)
                return {'i':i,'file':path.name,'duration':duration,'bytes':path.stat().st_size}
        except Exception as e:
            print(f'Retry {i+1:02d} attempt {attempt}: {e}',flush=True)
            path.unlink(missing_ok=True)
            if attempt==5:raise
            await asyncio.sleep(min(20,2**attempt+random.random()))

async def main():
    result=await asyncio.gather(*(render_one(i,s) for i,s in enumerate(SCENES)))
    result.sort(key=lambda x:x['i'])
    assert len(result)==len(SCENES) and all(x['bytes']>4000 for x in result)
    doc={'voice':VOICE,'clips':result,'total_voice_seconds':sum(x['duration'] for x in result)}
    (OUT/'manifest.json').write_text(json.dumps(doc,indent=2),encoding='utf8')
    print('ALL 59 NATURAL VOICE CLIPS GENERATED, speech minutes=',round(doc['total_voice_seconds']/60,1),flush=True)

if __name__=='__main__':asyncio.run(main())

#!/usr/bin/env python3
"""Legacy whole-page narration inventory; default audio production is retired.

Use --plan for inspection. Historical functions remain for cache diagnostics.
New production uses authored audio/spoken scripts and synthesise_spoken.py.
"""
import argparse
import asyncio
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import edge_tts
import build
from page_narration import ROOT, MANIFEST, VOICE, RATE, VERSION, eligible, speech_sections, fingerprint, media_path, transcript

CACHE = Path(os.environ.get("BOOK_PAGE_AUDIO_CACHE", "/workspace/book-page-audio-cache"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], text=True))


def norm(text):
    return "".join(c.casefold() for c in text if c.isalnum())


def describe_error(error):
    status = getattr(error, 'status', None)
    if status:
        return f"HTTP {status}: {getattr(error, 'message', 'request failed')}"
    return re.sub(r'(?:https?|wss?)://\S+', '<service URL>', str(error))


def chunks(paragraphs, maximum=1800):
    result, current = [], ""
    for paragraph in paragraphs:
        # Split only at whitespace so no text is lost at long citations/sentences.
        for word in paragraph.split():
            if len(current) + len(word) + 1 > maximum and current:
                result.append(current)
                current = ""
            current += (" " if current else "") + word
        current += " "
    if current.strip():
        result.append(current.strip())
    assert norm(" ".join(result)) == norm(" ".join(paragraphs))
    return result


def plan():
    build.build(include_narration=False)
    pages = []
    for source, _ in build.PAGES:
        if not eligible(source):
            continue
        html = (build.OUT / build.destination(source)).read_text()
        title = re.search(r"<h1>(.*?)</h1>", html, re.S).group(1)
        from html import unescape
        title = unescape(re.sub(r"<[^>]+>", "", title))
        body = re.search(r'<div class="prose">(.*)</div>\s*</article>', html, re.S).group(1)
        sections = speech_sections(title, body)
        pages.append({"source": source, "title": title, "sections": sections,
                      "text_sha256": fingerprint(sections), "words": len(transcript(sections).split())})
    return pages


async def produce(pages, workers):
    catalogue = await edge_tts.list_voices(proxy=os.environ.get("HTTPS_PROXY"))
    assert VOICE in {voice["ShortName"] for voice in catalogue}, f"Voice unavailable: {VOICE}"
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "voice-catalogue.json").write_text(json.dumps(catalogue, indent=2))
    sem = asyncio.Semaphore(workers)
    network = asyncio.Semaphore(workers)
    encoders = asyncio.Semaphore(4)
    segment_locks = {}
    completed = 0

    async def raw_segment(text):
        signature = hashlib.sha256(json.dumps({"text": text, "voice": VOICE, "rate": RATE}, sort_keys=True).encode()).hexdigest()
        raw, meta = CACHE / (signature + ".mp3"), CACHE / (signature + ".json")
        if raw.exists() and meta.exists():
            cached = json.loads(meta.read_text())
            if cached.get("sha256") == digest(raw) and cached.get("text") == text:
                return raw, cached["duration"]
        for attempt in range(5):
            try:
                words = []
                part = raw.with_suffix(".part")
                async with network:
                    with part.open("wb") as out:
                        async for item in edge_tts.Communicate(text, voice=VOICE, rate=RATE, boundary="WordBoundary", proxy=os.environ.get("HTTPS_PROXY")).stream():
                            if item["type"] == "audio":
                                out.write(item["data"])
                            elif item["type"] == "WordBoundary":
                                words.append(item["text"])
                if norm(" ".join(words)) != norm(text):
                    import difflib
                    comparison = list(difflib.SequenceMatcher(None, norm(text), norm(" ".join(words))).get_opcodes())
                    difference = next((norm(text)[a:b], norm(" ".join(words))[c:d]) for op, a, b, c, d in comparison if op != "equal")
                    (CACHE / (signature + ".mismatch.json")).write_text(json.dumps({"text": text, "words": words, "first_difference": difference}, ensure_ascii=False))
                    raise AssertionError(f"Provider word-boundary mismatch {difference}: {text[:90]}")
                duration = await asyncio.to_thread(probe, part)
                assert duration > 0
                part.replace(raw)
                meta.write_text(json.dumps({"text": text, "words": words, "duration": duration, "sha256": digest(raw)}, ensure_ascii=False))
                return raw, duration
            except Exception as error:
                print(f"Retry {attempt + 1}/5: {type(error).__name__}: {describe_error(error)} [{signature[:8]}]", flush=True)
                if attempt == 4:
                    raise
                await asyncio.sleep(min(2 ** attempt, 12))

    async def segment(text):
        # Different entries can share a short foundation/notes section. Avoid
        # concurrent writes to the same content-addressed cache file.
        signature = hashlib.sha256(text.encode()).hexdigest()
        lock = segment_locks.setdefault(signature, asyncio.Lock())
        async with lock:
            return await raw_segment(text)

    async def page(item):
        nonlocal completed
        async with sem:
            source = item["source"]
            audio = ROOT / media_path(source, ".mp3")
            text_file = ROOT / media_path(source, ".txt")
            record = CACHE / (item["text_sha256"] + "-page.json")
            if record.exists() and audio.exists() and text_file.exists():
                cached = json.loads(record.read_text())
                if cached["audio_sha256"] == digest(audio) and cached["transcript_sha256"] == digest(text_file):
                    completed += 1
                    print(f"Ready {completed}/{len(pages)} (cached): {source}", flush=True)
                    return source, cached
            audio.parent.mkdir(parents=True, exist_ok=True)
            offset, inputs, sections, jobs, sizes = 0.0, [], [], [], []
            for section in item["sections"]:
                texts = chunks(section["paragraphs"])
                sizes.append(len(texts))
                jobs.extend(segment(text) for text in texts)
            # Section requests may overlap; results retain reading order. This
            # avoids a long source/glossary page serialising its entire recording.
            rendered = await asyncio.gather(*jobs)
            cursor = 0
            for section, size in zip(item["sections"], sizes):
                start = offset
                for raw, duration in rendered[cursor:cursor + size]:
                    inputs.append(raw)
                    offset += duration
                cursor += size
                sections.append({"title": section["title"], "anchor": section["anchor"], "start": round(start, 3), "end": round(offset, 3)})
            listing = CACHE / (item["text_sha256"] + "-concat.txt")
            listing.write_text("".join("file '" + str(path) + "'\n" for path in inputs))
            temporary = audio.with_suffix(".partial.mp3")
            async with encoders:
                await asyncio.to_thread(subprocess.run, ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "24000", "-ac", "1", "-b:a", "96k", "-metadata", "title=" + item["title"], "-metadata", "artist=Understanding people", "-metadata", "comment=Synthetic narration: " + VOICE, "-metadata", "copyright=Copyright 2026 Christopher Snow", str(temporary)], check=True)
                await asyncio.to_thread(subprocess.run, ["ffmpeg", "-nostdin", "-v", "error", "-i", str(temporary), "-f", "null", "-"], check=True)
            duration = await asyncio.to_thread(probe, temporary)
            assert abs(duration - offset) < 1.0, (source, duration, offset)
            temporary.replace(audio)
            text_file.write_text(transcript(item["sections"]))
            result = {"title": item["title"], "text_sha256": item["text_sha256"], "audio_sha256": digest(audio), "transcript_sha256": digest(text_file), "words": item["words"], "duration": duration, "sections": sections, "provider_words_verified": True}
            record.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            completed += 1
            print(f"Ready {completed}/{len(pages)}: {source} ({duration / 60:.1f} min)", flush=True)
            return source, result

    outcomes = await asyncio.gather(*(page(item) for item in pages), return_exceptions=True)
    failures = [(item["source"], describe_error(result)) for item, result in zip(pages, outcomes) if isinstance(result, BaseException)]
    if failures:
        (CACHE / "failures.json").write_text(json.dumps(failures, indent=2))
        raise RuntimeError(f"{len(failures)} pages could not be produced. Completed pages are cached; rerun to retry. See {CACHE / 'failures.json'}")
    results = outcomes
    manifest = {"version": VERSION, "service": "Microsoft Edge neural TTS via edge-tts", "edge_tts_version": edge_tts.__version__, "underlying_model": "Not exposed by the service metadata", "voice": VOICE, "rate": RATE, "generated": datetime.now(timezone.utc).isoformat(), "normalisation": "-16 LUFS target, -1.5 dBTP target, mono 24 kHz MP3 at 96 kbps", "pages": dict(results)}
    temporary = MANIFEST.with_suffix(".partial.json")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(MANIFEST)
    print(f"Complete: {len(results)} pages, {sum(r['duration'] for _, r in results) / 3600:.2f} hours.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true", help="Prepare/read the exact scripts and count scope without synthesising")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    assert 1 <= args.workers <= 32
    if not args.plan:
        parser.error('Verbatim whole-page production is retired after listening feedback. Author a spoken script and use scripts/synthesise_spoken.py; see .agents/skills/spoken-book-narration/SKILL.md. --plan remains available for inspection.')
    pages = plan()
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "plan.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n")
    words = sum(p["words"] for p in pages)
    print(f"Plan: {len(pages)} pages, {words:,} spoken words, approximately {words / 155 / 60:.1f} hours.", flush=True)
    if not args.plan:
        asyncio.run(produce(pages, args.workers))
        build.build()


if __name__ == "__main__":
    main()

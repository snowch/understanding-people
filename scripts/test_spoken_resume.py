"""Offline regressions for interrupted publication and resumable paragraph work."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import synthesise_spoken as producer


def lesson(*texts):
    return {
        'voice': 'en-US-AndrewMultilingualNeural',
        'rate': '-2%',
        'sections': [{'paragraphs': [{'text': text} for text in texts]}],
    }


class AtomicPublication(unittest.TestCase):
    def test_interrupted_audio_copy_preserves_previous_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, destination = root / 'verified.mp3', root / 'published.mp3'
            source.write_bytes(b'complete replacement recording')
            destination.write_bytes(b'previous recording')

            def interrupted_copy(source_path, pending):
                self.assertNotEqual(Path(pending), destination)
                Path(pending).write_bytes(Path(source_path).read_bytes()[:8])
                self.assertEqual(destination.read_bytes(), b'previous recording')
                raise KeyboardInterrupt('interrupted while copying')

            with patch.object(producer.shutil, 'copyfile', side_effect=interrupted_copy):
                with self.assertRaises(KeyboardInterrupt):
                    producer.atomic_copy(source, destination)

            self.assertEqual(destination.read_bytes(), b'previous recording')
            self.assertEqual(set(root.iterdir()), {source, destination})

    def test_interrupted_text_write_preserves_previous_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            destination = root / 'transcript.txt'
            destination.write_text('previous transcript')
            real_write_text = Path.write_text

            def interrupted_write(pending, text, *args, **kwargs):
                self.assertNotEqual(pending, destination)
                real_write_text(pending, text[:8], *args, **kwargs)
                self.assertEqual(destination.read_text(), 'previous transcript')
                raise KeyboardInterrupt('interrupted while writing')

            with patch.object(Path, 'write_text', new=interrupted_write):
                with self.assertRaises(KeyboardInterrupt):
                    producer.atomic_text(destination, 'complete replacement transcript')

            self.assertEqual(destination.read_text(), 'previous transcript')
            self.assertEqual(set(root.iterdir()), {destination})

    def test_failed_replace_cleans_staged_audio_and_text(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, destination = root / 'source.mp3', root / 'destination'
            source.write_bytes(b'new content')
            for kind in ('audio', 'text'):
                with self.subTest(kind=kind):
                    destination.write_bytes(b'old content')
                    with patch.object(Path, 'replace', side_effect=OSError('replace failed')):
                        with self.assertRaises(OSError):
                            if kind == 'audio':
                                producer.atomic_copy(source, destination)
                            else:
                                producer.atomic_text(destination, 'new content')
                    self.assertEqual(destination.read_bytes(), b'old content')
                    self.assertEqual(set(root.iterdir()), {source, destination})

    def test_successful_publication_replaces_content_without_pending_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, audio, text = root / 'source.mp3', root / 'audio.mp3', root / 'text.txt'
            source.write_bytes(b'verified audio')
            audio.write_bytes(b'old audio')
            text.write_text('old transcript')
            producer.atomic_copy(source, audio)
            producer.atomic_text(text, 'new transcript')
            self.assertEqual(audio.read_bytes(), source.read_bytes())
            self.assertEqual(text.read_text(), 'new transcript')
            self.assertEqual(set(root.iterdir()), {source, audio, text})


class ParagraphResume(unittest.IsolatedAsyncioTestCase):
    async def test_corrupted_cache_metadata_is_regenerated_and_reusable(self):
        text = 'A complete spoken paragraph.'
        calls = []

        class Speech:
            def __init__(self, requested_text, **kwargs):
                calls.append(requested_text)
                self.text = requested_text

            async def stream(self):
                yield {'type': 'audio', 'data': b'fake verified MP3'}
                yield {'type': 'WordBoundary', 'text': self.text}

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(producer, 'CACHE', root), \
                    patch.object(producer.edge_tts, 'Communicate', Speech), \
                    patch.object(producer, 'probe', return_value=1.0), \
                    patch.object(producer, 'print', create=True):
                original = (await producer.synthesise(lesson(text), workers=1))[0]
                metadata = original.with_suffix('.json')
                metadata.write_text('{"text":')
                original.write_bytes(b'old cached audio')

                regenerated = (await producer.synthesise(lesson(text), workers=1))[0]
                self.assertEqual(regenerated, original)
                self.assertEqual(regenerated.read_bytes(), b'fake verified MP3')
                saved = json.loads(metadata.read_text())
                self.assertEqual(saved['text'], text)
                self.assertTrue(saved['words_verified'])
                self.assertEqual(saved['sha256'], producer.spoken.sha(regenerated))

                cached = await producer.synthesise(lesson(text), workers=1)
                self.assertEqual(cached, [regenerated])
                self.assertEqual(calls, [text, text])
                self.assertFalse(list(root.glob('*.partial')))
                self.assertFalse(list(root.glob('*.part')))

    async def test_failed_paragraph_waits_for_successful_sibling_to_cache(self):
        failed_text, successful_text = 'This paragraph fails.', 'This paragraph succeeds.'
        successful_started = asyncio.Event()
        release_success = asyncio.Event()
        retries_exhausted = asyncio.Event()
        real_sleep = asyncio.sleep
        failed_attempts = []

        class Speech:
            def __init__(self, requested_text, **kwargs):
                self.text = requested_text

            async def stream(self):
                if self.text == failed_text:
                    failed_attempts.append(self.text)
                    if len(failed_attempts) == 6:
                        retries_exhausted.set()
                    raise OSError('mock provider failure')
                successful_started.set()
                await release_success.wait()
                yield {'type': 'audio', 'data': b'complete successful MP3'}
                yield {'type': 'WordBoundary', 'text': self.text}

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(producer, 'CACHE', root), \
                    patch.object(producer.edge_tts, 'Communicate', Speech), \
                    patch.object(producer, 'probe', return_value=1.0), \
                    patch.object(producer.asyncio, 'sleep', new=AsyncMock()), \
                    patch.object(producer, 'print', create=True):
                task = asyncio.create_task(producer.synthesise(
                    lesson(failed_text, successful_text), workers=2))
                try:
                    await asyncio.wait_for(successful_started.wait(), timeout=2)
                    await asyncio.wait_for(retries_exhausted.wait(), timeout=2)
                    # Let gather's completion callbacks run while the sibling is blocked.
                    for _ in range(3):
                        await real_sleep(0)
                    self.assertFalse(task.done(), 'Page returned while a sibling was still running')
                finally:
                    release_success.set()
                    outcomes = await asyncio.gather(task, return_exceptions=True)

                self.assertIsInstance(outcomes[0], RuntimeError)
                self.assertEqual(len(failed_attempts), 6)
                metadata = list(root.glob('*.json'))
                self.assertEqual(len(metadata), 1)
                saved = json.loads(metadata[0].read_text())
                self.assertEqual(saved['text'], successful_text)
                self.assertTrue(saved['words_verified'])
                audio = metadata[0].with_suffix('.mp3')
                self.assertEqual(audio.read_bytes(), b'complete successful MP3')
                self.assertEqual(saved['sha256'], producer.spoken.sha(audio))

                # Retrying the surviving paragraph must use its completed cache entry.
                with patch.object(producer.edge_tts, 'Communicate', side_effect=AssertionError('unexpected request')):
                    self.assertEqual(await producer.synthesise(lesson(successful_text), workers=1), [audio])


if __name__ == '__main__':
    unittest.main()

"""Protect the listening fixes: real gaps, intact internal pauses and spoken scripts."""
import array
import copy
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import spoken_narration as spoken
from synthesise_spoken import assemble, trim_edges


def pcm(value, milliseconds):
    return array.array('h', [value] * round(milliseconds * spoken.SAMPLE_RATE / 1000)).tobytes()


class SpokenProduction(unittest.TestCase):
    def test_trim_preserves_internal_silence_and_speech(self):
        raw = pcm(0, 1000) + pcm(1000, 200) + pcm(0, 450) + pcm(-1000, 200) + pcm(0, 1000)
        trimmed = trim_edges(raw)
        self.assertEqual(trimmed, pcm(0, 80) + pcm(1000, 200) + pcm(0, 450) + pcm(-1000, 200) + pcm(0, 120))

    def test_paragraphs_have_physical_gaps_in_the_audio(self):
        data = {'sections': [{'title': 'A thought', 'anchor': 'main', 'paragraphs': [
            {'text': 'First thought.', 'pause_after_ms': 800},
            {'text': 'Think before the answer.', 'pause_after_ms': 9000}]}]}
        take = pcm(0, 200) + pcm(1000, 200) + pcm(0, 200)
        with tempfile.TemporaryDirectory() as folder, patch('synthesise_spoken.decode', return_value=take):
            output = Path(folder) / 'lesson.wav'
            sections, pauses = assemble(data, ['first', 'second'], output)
            with wave.open(str(output)) as f:
                self.assertEqual(f.getframerate(), spoken.SAMPLE_RATE)
                samples = array.array('h', f.readframes(f.getnframes()))
            for pause in pauses:
                start, end = (round(pause[k] * spoken.SAMPLE_RATE) for k in ['start', 'end'])
                self.assertEqual(set(samples[start:end]), {0})
            self.assertAlmostEqual(pauses[0]['end'] - pauses[0]['start'], .8)
            self.assertAlmostEqual(pauses[1]['end'] - pauses[1]['start'], 9)
            self.assertEqual(sections[0]['start'], 0)

    def test_script_changes_invalidate_recording_and_raw_citations_are_rejected(self):
        for _, data in spoken.scripts().values():
            original = spoken.fingerprint(data)
            changed = copy.deepcopy(data)
            changed['sections'][0]['paragraphs'][0]['pause_after_ms'] += 100
            self.assertNotEqual(original, spoken.fingerprint(changed))
            changed = copy.deepcopy(data)
            changed['sections'][0]['paragraphs'][0]['text'] = 'Nickerson (1998).'
            with self.assertRaises(AssertionError):
                spoken.validate(changed)


if __name__ == '__main__':
    unittest.main()

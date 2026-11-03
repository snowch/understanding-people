"""The extraction must preserve meaning while excluding UI, notes and old media."""
import unittest
from page_narration import speech_sections, transcript, fingerprint
from synthesise_pages import chunks


class Extraction(unittest.TestCase):
    def test_content_order_tables_and_answer_warning(self):
        html = '''<p>First <strong>important</strong> claim.</p><h2 id="test">How to check?</h2>
        <table><thead><tr><th>Observation</th><th>Possible reason</th></tr></thead>
        <tbody><tr><td>No reply</td><td>Unknown</td></tr></tbody></table>
        <details class="answer-check"><summary>Compare an answer</summary><p>Check the date.</p></details>'''
        sections = speech_sections('Title', html)
        text = transcript(sections)
        self.assertEqual(sections[1]['anchor'], 'test')
        self.assertIn('First important claim.', text)
        self.assertIn('How to check?\n', text)
        self.assertNotIn('check?.', text)
        self.assertIn('Observation: No reply. Possible reason: Unknown.', text)
        self.assertLess(text.index('Pause here'), text.index('Check the date'))

    def test_no_ui_personal_notes_or_duplicate_recordings(self):
        html = '''<nav>Navigation</nav><div class="library-search">Search controls</div>
        <script>tracking()</script><section class="reference-listenings"><p>Old transcript</p></section>
        <details class="audio-exercise"><p>Old exercise</p></details>
        <details class="practice-notes"><textarea>PERSONAL NOTE</textarea></details>
        <p><a href="https://example.org/a-secret-query">Actual teaching</a>.</p>'''
        text = transcript(speech_sections('Title', html))
        for excluded in ['Navigation', 'Search controls', 'tracking', 'Old transcript', 'Old exercise', 'PERSONAL NOTE', 'a-secret-query']:
            self.assertNotIn(excluded, text)
        self.assertIn('Actual teaching.', text)
        self.assertIn('Optional practice notes', text)

    def test_chunks_and_staleness(self):
        self.assertEqual(speech_sections('Understanding people', '')[0]['paragraphs'], ['Understanding people.'])
        paragraphs = ['A complete first paragraph.'] + ['A much longer statement with details. ' * 300]
        result = chunks(paragraphs)
        self.assertTrue(all(len(s) <= 1800 for s in result))
        self.assertEqual(' '.join(' '.join(result).split()), ' '.join(' '.join(paragraphs).split()))
        a = speech_sections('Title', '<h2 id="one">Evidence</h2><p>A claim.</p>')
        b = speech_sections('Title', '<h2 id="one">Evidence</h2><p>A revised claim.</p>')
        c = speech_sections('Title', '<h2 id="two">Evidence</h2><p>A claim.</p>')
        self.assertNotEqual(fingerprint(a), fingerprint(b))
        self.assertNotEqual(fingerprint(a), fingerprint(c))


if __name__ == '__main__':
    unittest.main()

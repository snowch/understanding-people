import tempfile
import unittest
from pathlib import Path

from book_search import catalogue, write_index, book_guide_aliases
from page_narration import eligible


class PassageIndexTests(unittest.TestCase):
    def test_book_titles_resolve_without_aliasing_ambiguous_concepts(self):
        aliases=book_guide_aliases()
        self.assertIn('personality what makes you the way you are daniel nettle',aliases)
        self.assertIn('daniel nettle personality',aliases)
        self.assertIn('behave sapolsky',aliases)
        self.assertIn('the personality puzzle',aliases)
        self.assertNotIn('personality',aliases)
        self.assertNotIn('influence',aliases)
        self.assertNotIn('behave',aliases)

    def make(self, html):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        root=Path(folder.name);(root/'lesson.html').write_text(html)
        return root

    def test_index_preserves_passage_context_and_excludes_private_controls(self):
        root=self.make('''<main id="main"><h1>A useful concept</h1><h2 id="page-narration-title">Listen</h2>
        <div class="prose"><p>First paragraph. This is a useful introduction.</p><p>Second paragraph.</p>
        <nav>DO NOT INDEX NAVIGATION</nav><div class="practice-notes"><textarea>PRIVATE NOTES</textarea></div>
        <section class="audio-edition">DUPLICATE TRANSCRIPT</section>
        <h2 id="explanation">How this works</h2><p>The explanation must remain attached to its own heading.</p>
        <h2 id="related">Related entries</h2><p>DO NOT INDEX CROSS REFERENCES</p>
        <h2 id="practice">Put it into practice</h2><p>A concrete action that the reader can take this week.</p></div></main>''')
        data=catalogue(root,[('lesson.md','Lesson')],[])
        texts=' '.join(p['text'] for p in data['passages'])
        for forbidden in ['PRIVATE NOTES','DUPLICATE TRANSCRIPT','DO NOT INDEX']:
            self.assertNotIn(forbidden,texts)
        self.assertIn('introduction. Second paragraph.',texts)
        target=next(p for p in data['passages'] if 'explanation must' in p['text'])
        self.assertEqual((target['anchor'],target['heading']),('explanation','How this works'))
        self.assertEqual(data['documents'][0]['listen'],'page-narration-title')
        self.assertEqual(data['documents'][0]['practice'],'practice')

    def test_search_is_a_utility_and_does_not_require_or_index_narration(self):
        self.assertFalse(eligible('search.md'))
        self.assertTrue(eligible('chapters/01-before-you-explain.md'))

    def test_stale_vectors_fail_before_a_search_index_is_published(self):
        root=self.make('<main id="main"><h1>Changed teaching</h1><div class="prose"><p>A changed explanation with enough words to become a passage.</p></div></main>')
        with self.assertRaisesRegex(AssertionError,'Search passages changed'):
            write_index(root,[('lesson.md','Changed')],[])
        self.assertFalse((root/'assets/search/index.json').exists())


if __name__=='__main__':unittest.main()

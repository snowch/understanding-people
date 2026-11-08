"""Text-first exceptions must never silently represent old narration as current.

Fixtures stay independent of whichever pages currently have text-only status.
"""
import copy
import unittest
from unittest.mock import patch
from page_narration import load_manifest
from narration_voices import VOICES
from spoken_narration import scripts, source_hashes
import written_editions as written

class WrittenEditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifests = {v:load_manifest(v) for v in VOICES}

    def test_new_text_has_no_approved_script_or_recording(self):
        source = 'reference/future-text-fixture.md'
        item = {'status':'new-text', 'reason':'New unrecorded text', 'date':'2026-11-08', 'page_text_sha256':'reviewed-text'}
        with patch.object(written, 'editions', return_value={source:item}):
            self.assertTrue(written.verify(source, 'reviewed-text', self.manifests))
            with self.assertRaises(AssertionError):
                written.verify(source, 'unreviewed-writing', self.manifests)
            altered = copy.deepcopy(self.manifests)
            altered['andrew']['pages'][source] = {}
            with self.assertRaises(AssertionError):
                written.verify(source, 'reviewed-text', altered)

    def revised_fixture(self):
        source = 'reference/sources.md'
        recorded = self.manifests['andrew']['pages'][source]
        return source, {'status':'revised-text', 'reason':'Fixture revision preserving approved audio', 'date':'2026-11-08',
                        'page_text_sha256':'new-writing', 'recorded_page_text_sha256':recorded['page_text_sha256'],
                        'recorded_source_hashes':recorded['source_hashes'],
                        'current_source_hashes':source_hashes(scripts()[source][1])}

    def test_changed_recording_cannot_be_hidden_by_a_text_revision(self):
        source, item = self.revised_fixture()
        with patch.object(written, 'editions', return_value={source:item}):
            self.assertTrue(written.verify(source, 'new-writing', self.manifests))
            altered = copy.deepcopy(self.manifests)
            altered['andrew']['pages'][source]['script_sha256'] = 'unapproved-script'
            with self.assertRaises(AssertionError):
                written.verify(source, 'new-writing', altered)

    def test_unreviewed_source_change_is_rejected(self):
        source, item = self.revised_fixture()
        item['current_source_hashes'] = {}
        with patch.object(written, 'editions', return_value={source:item}):
            with self.assertRaises(AssertionError):
                written.verify(source, 'new-writing', self.manifests)

if __name__ == '__main__': unittest.main()

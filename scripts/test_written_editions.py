"""A text-first release must never silently represent old narration as current."""
import copy
import unittest
from unittest.mock import patch
from page_narration import load_manifest
from narration_voices import VOICES
import written_editions as written

class WrittenEditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifests={v:load_manifest(v) for v in VOICES}

    def test_new_text_has_no_approved_script_or_recording(self):
        source='reference/naming-and-belonging.md'
        item=written.editions()[source]
        self.assertTrue(written.verify(source,item['page_text_sha256'],self.manifests))
        with self.assertRaises(AssertionError):
            written.verify(source,'unreviewed-writing',self.manifests)

    def test_changed_recording_cannot_be_hidden_by_a_text_revision(self):
        source='reference/sources.md'
        item=written.editions()[source]
        self.assertTrue(written.verify(source,item['page_text_sha256'],self.manifests))
        altered=copy.deepcopy(self.manifests)
        altered['andrew']['pages'][source]['script_sha256']='unapproved-script'
        with self.assertRaises(AssertionError):
            written.verify(source,item['page_text_sha256'],altered)

    def test_unreviewed_source_change_is_rejected(self):
        data=copy.deepcopy(written.editions())
        data['reference/sources.md']['current_source_hashes']={}
        with patch.object(written,'editions',return_value=data):
            with self.assertRaises(AssertionError):
                written.verify('reference/sources.md',data['reference/sources.md']['page_text_sha256'],self.manifests)

if __name__=='__main__':unittest.main()

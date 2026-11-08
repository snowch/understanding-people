"""Container-only edits cannot bless changed teaching, scripts or source entries."""
import copy
import unittest
from unittest.mock import patch
from page_narration import load_manifest
from spoken_narration import scripts,source_hashes,for_voice,check_entry
import narration_source_reviews as review

class SourceReviewTests(unittest.TestCase):
 def setUp(self):
  self.source='reference/gaslighting.md'
  self.script=scripts()[self.source][1]
  self.entry=load_manifest('andrew')['pages'][self.source]
  self.current=source_hashes(self.script)
 def test_unchanged_entry_and_lesson_survive_a_sibling_edit(self):
  self.assertTrue(review.verify(self.source,self.script,self.entry,self.current))
  check_entry(self.source,self.entry['page_text_sha256'],self.entry)
  script=for_voice(self.script,'jenny');entry=load_manifest('jenny')['pages'][self.source]
  self.assertTrue(review.verify(self.source,script,entry,self.current))
 def test_changed_lesson_cannot_use_container_review(self):
  with self.assertRaisesRegex(AssertionError,'Page teaching changed'):
   check_entry(self.source,'different-lesson',self.entry)
  item=copy.deepcopy(review.reviews()[self.source]);item['canonical_entry_sha256']='0'*64
  with patch.object(review,'reviews',return_value={self.source:item}):
   with self.assertRaisesRegex(AssertionError,'Entry changed after'):
    review.verify(self.source,self.script,self.entry,self.current)
 def test_stale_source_or_altered_recording_binding_is_rejected(self):
  with self.assertRaises(AssertionError):review.verify(self.source,self.script,self.entry,{})
  altered=copy.deepcopy(self.entry);altered['script_sha256']='0'*64
  with self.assertRaises(AssertionError):review.verify(self.source,self.script,altered,self.current)

if __name__=='__main__':unittest.main()

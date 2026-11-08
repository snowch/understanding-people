"""Glossary lookups must clarify vocabulary without changing approved teaching."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import markdown
import reference_terminology as vocab
from page_narration import speech_sections

ROOT=Path(__file__).resolve().parents[1]
def render(source):
 text=(ROOT/source).read_text();title,body=text.split('\n',1)
 return title[2:],markdown.markdown(body,extensions=['tables','fenced_code','toc','md_in_html','attr_list'])

class TerminologyTests(unittest.TestCase):
 def test_family_term_links_without_rewriting_the_explanation(self):
  title,body=render('reference/family-membership.md')
  enhanced=vocab.annotate('reference/family-membership.md',body,Path('reference/family-membership.html'))
  self.assertIn('id="definition-family-boundary-ambiguity"',enhanced)
  self.assertIn('href="../glossary.html#family-boundary-ambiguity"',enhanced)
  self.assertEqual(speech_sections(title,body),speech_sections(title,enhanced))
  self.assertEqual(enhanced.count('id="definition-family-boundary-ambiguity"'),1)

 def test_dictionary_preserves_core_anchors_and_audio_scope(self):
  title,body=render('glossary.md');enhanced=vocab.glossary(body,Path('glossary.html'))
  self.assertEqual(speech_sections(title,body),speech_sections(title,enhanced))
  for term in [*vocab.core_terms(),*vocab.terms()]:self.assertIn(f'id="{term["id"]}"',enhanced)
  self.assertIn('href="#if-then-plan"',enhanced)
  self.assertIn('href="#boundary"',enhanced)
  self.assertIn('href="#obsession"',enhanced)
  self.assertNotIn('id="definition-autonomy"',enhanced)

 def test_markup_does_not_nest_links_or_treat_face_as_a_verb_definition(self):
  text='<p>We face a delay. Autonomy matters. <a href="x.html">Autonomy in a title</a>.</p>'
  linked=vocab.annotate('reference/declining-help.md',text,Path('reference/declining-help.html'))
  self.assertIn('href="../glossary.html#autonomy"',linked)
  self.assertNotIn('#face"',linked)
  self.assertIn('<a href="x.html">Autonomy in a title</a>',linked)

 def test_parent_change_requires_review(self):
  data=json.loads((ROOT/'reference/terminology.json').read_text());first=data['terms'][0]
  first['source_sha256']='0'*64
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'reference').mkdir()
   (root/'reference/terminology.json').write_text(json.dumps(data))
   (root/'glossary.md').write_bytes((ROOT/'glossary.md').read_bytes())
   (root/first['source']).write_bytes((ROOT/first['source']).read_bytes())
   vocab.terms.cache_clear()
   try:
    with patch.object(vocab,'ROOT',root):
     with self.assertRaisesRegex(AssertionError,'Review glossary wording'):vocab.terms()
   finally:vocab.terms.cache_clear()

if __name__=='__main__':unittest.main()

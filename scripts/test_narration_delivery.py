"""Check the external-media boundary without generating speech or using the network."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import narration_delivery as delivery

class ReleaseDeliveryTests(unittest.TestCase):
    def test_urls_pin_the_release_voice_and_content(self):
        source = 'reference/naming-and-belonging.md'
        with patch.object(delivery, 'config', return_value={'repository':'snowch/understanding-people', 'release_tag':'immutable-test', 'pages':[source]}):
            url = delivery.remote_url(source, 'jenny', {'audio_sha256':'a'*64})
            self.assertEqual(url, 'https://github.com/snowch/understanding-people/releases/download/immutable-test/narration-jenny-naming-and-belonging-aaaaaaaaaaaa.mp3')
            self.assertIsNone(delivery.remote_url('reference/confirmation-bias.md', 'jenny', {'audio_sha256':'a'*64}))
            paths = delivery.excluded_paths()
            self.assertEqual(paths, {'assets/media/narration/reference/naming-and-belonging.mp3', 'assets/media/narration/jenny/reference/naming-and-belonging.mp3'})
            self.assertFalse(any(p.endswith('.txt') for p in paths))

    def test_unsafe_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'delivery.json'
            for value in ('{"version":1,"repository":"evil.example","release_tag":"ok","pages":[]}',
                          '{"version":1,"repository":"snowch/understanding-people","release_tag":"../draft","pages":[]}'):
                path.write_text(value)
                delivery.config.cache_clear()
                with patch.object(delivery, 'MANIFEST', path):
                    with self.assertRaises(AssertionError): delivery.config()
        delivery.config.cache_clear()

if __name__ == '__main__': unittest.main()

"""Regressions for exact 6.7.4 resource and message identity."""

import unittest
from unittest.mock import patch

from build_product_notice_sbom import encode
from verify_inno674_product_resources import BODY, OPTIONS, check_messages, verify


class Inno674ResourcesTests(unittest.TestCase):
    """Reject different input identities and changed message source digests."""

    def test_message_pins(self) -> None:
        """Require both English text and language options."""
        result = {'body_sha256': BODY, 'language_options_sha256': OPTIONS}
        with patch('verify_inno674_product_resources.verify_messages', return_value=result):
            self.assertEqual(check_messages(b'messages')['message_semantics'],
                             'MATCH_PINNED_ENGLISH_TEXT')
            result['language_options_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                check_messages(b'messages')

    def test_unreviewed_identity(self) -> None:
        """Reject unrelated templates and attribution before resource parsing."""
        with self.assertRaises(ValueError):
            verify(b'setup', b'exe', b'loader', b'engine', b'icon', encode({}))


if __name__ == '__main__':
    unittest.main()

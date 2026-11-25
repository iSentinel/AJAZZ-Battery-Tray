"""Regressions for complete ordered OSV responses and candidate binding."""

import unittest

from build_product_notice_sbom import encode
from crosscheck_product_sbom_osv import crosscheck
from inventory_dotnet_pack_licenses import PACKS
from test_audit_product_sbom_advisories import fixture


def query() -> dict:
    """Return exact reviewed public package queries."""
    return {'queries': [{'package': {'ecosystem': 'NuGet', 'name': name},
                         'version': version} for name, version, _ in PACKS.values()]}


class OsvTests(unittest.TestCase):
    """Require a complete response and retain positive identifiers."""

    def test_clear_and_match(self) -> None:
        """Zero IDs and positive matches have distinct scoped results."""
        bom, record, _ = fixture()
        response = {'results': [{}, {}, {}, {}]}
        result = crosscheck(encode(bom), record, encode(query()), encode(response))
        self.assertEqual(result['result'], 'NO_IDS_RETURNED')
        response['results'][1] = {'vulns': [{'id': 'GHSA-aaaa-bbbb-cccc'}]}
        self.assertEqual(crosscheck(encode(bom), record, encode(query()),
                                    encode(response))['result'], 'MATCHES_FOUND')

    def test_incomplete_or_wrong_query(self) -> None:
        """Reject omitted results, pending pages and reordered queries."""
        bom, record, _ = fixture()
        for response in ({'results': [{}]}, {'results': [{}, {}, {}, {'next_page_token': 'next'}]}):
            with self.assertRaises(ValueError):
                crosscheck(encode(bom), record, encode(query()), encode(response))
        wrong = query()
        wrong['queries'].reverse()
        with self.assertRaises(ValueError):
            crosscheck(encode(bom), record, encode(wrong), encode({'results': [{}, {}, {}, {}]}))


if __name__ == '__main__':
    unittest.main()

import json,unittest,hashlib
from pathlib import Path
from xi_glyph.tessera import encode_v4,decode_v4
from xi_glyph.tessera_grammar import RULES

class GlyphTests(unittest.TestCase):
    def test_declared_reduction(self):
        r=decode_v4(encode_v4(['△'],['S4']))
        self.assertEqual(r['execution']['terminal'],['○'])
    def test_combined_atoms_and_unknown_extensions_survive(self):
        source=['κ̄','μ̄','⊚⟐⋈∞⋈⟐⊚','unlisted🌱']
        self.assertEqual(decode_v4(encode_v4(source,[]))['source'],source)
    def test_deterministic_transport(self):
        self.assertEqual(encode_v4(['△'],['S4']),encode_v4(['△'],['S4']))
    def test_corruption_rejected(self):
        packet=bytearray(encode_v4(['△'],['S4']));packet[-1]^=1
        with self.assertRaises((ValueError,KeyError)):decode_v4(bytes(packet))
    def test_all_declared_states_roundtrip(self):
        for rule in RULES:
            with self.subTest(state=rule.state,source=rule.lhs):
                r=decode_v4(encode_v4(list(rule.lhs),[rule.state]))
                self.assertEqual(r['source'],list(rule.lhs));self.assertEqual(r['path'],[rule.state])
    def test_mirror_lineage(self):
        for source in json.loads(Path('SOURCE-MANIFEST.json').read_text())['files']:
            self.assertEqual(hashlib.sha256(Path(source['mirror']).read_bytes()).hexdigest(),source['sha256'])
if __name__=='__main__':unittest.main()

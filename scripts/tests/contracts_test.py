import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_contracts import verify_service


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.baseline = json.loads((Path(__file__).resolve().parents[2] / 'release/contracts/chat-service-1.json').read_text())
        self.current = copy.deepcopy(self.baseline)

    def test_optional_new_method_is_compatible(self):
        method = copy.deepcopy(self.current['methods'][0]); method['id'] = 'optional_feature'
        self.current['methods'].append(method)
        self.assertEqual(verify_service(self.baseline, self.current), 1)

    def test_removing_or_changing_existing_method_is_rejected(self):
        self.current['methods'].pop()
        with self.assertRaisesRegex(ValueError, 'removed stable method'):
            verify_service(self.baseline, self.current)
        self.current = copy.deepcopy(self.baseline)
        self.current['methods'][0]['kind'] = 'operation'
        with self.assertRaisesRegex(ValueError, 'lifecycle'):
            verify_service(self.baseline, self.current)

    def test_changing_request_shape_is_rejected(self):
        self.current['methods'][0]['args_schema']['properties']['id']['type'] = 'integer'
        with self.assertRaisesRegex(ValueError, 'args_schema'):
            verify_service(self.baseline, self.current)

    def test_adding_output_enum_variant_is_rejected(self):
        target = next(m for m in self.current['methods'] if m['id'] == 'history')
        target['output_schema']['$defs']['Delivery']['enum'].append('read')
        with self.assertRaisesRegex(ValueError, 'variants'):
            verify_service(self.baseline, self.current)

    def test_optional_output_field_requires_retained_decoder_to_allow_it(self):
        target = next(m for m in self.current['methods'] if m['id'] == 'identify')
        target['output_schema']['properties']['optional_feature'] = {'type': 'string'}
        self.assertEqual(verify_service(self.baseline, self.current), 0)
        target = next(m for m in self.current['methods'] if m['id'] == 'files')
        target['output_schema']['properties']['optional_feature'] = {'type': 'string'}
        with self.assertRaisesRegex(ValueError, 'retained decoders'):
            verify_service(self.baseline, self.current)


if __name__ == '__main__': unittest.main()

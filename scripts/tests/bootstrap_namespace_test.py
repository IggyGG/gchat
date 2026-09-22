import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "bootstrap_namespace", Path(__file__).resolve().parents[1] / "test-bootstrap-namespace.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class NamespaceIsolation(unittest.TestCase):
    def setUp(self):
        self.devices = [{"ifname": "lo"}, {
            "ifname": "tunl0", "link_type": "ipip", "operstate": "DOWN",
            "flags": ["NOARP"], "address": "0.0.0.0", "broadcast": "0.0.0.0"}]
        self.addresses = [{"ifname": "tunl0", "addr_info": []}]

    def test_accepts_only_loopback_or_inert_kernel_tunnel(self):
        self.assertTrue(helper.disconnected_links(self.devices[:1], [], []))
        self.assertTrue(helper.disconnected_links(self.devices, self.addresses, []))
        self.assertFalse(helper.disconnected_links([], [], []))

    def test_rejects_live_configured_or_other_links(self):
        for changes in ({"flags": ["UP"]}, {"operstate": "UP"},
                        {"address": "192.0.2.1"}, {"ifname": "eth0"},
                        {"link_type": "ether"}):
            devices = copy.deepcopy(self.devices)
            devices[1].update(changes)
            self.assertFalse(helper.disconnected_links(devices, self.addresses, []))
        self.addresses[0]["addr_info"] = [{"local": "192.0.2.1"}]
        self.assertFalse(helper.disconnected_links(self.devices, self.addresses, []))

    def test_rejects_ipv4_and_ipv6_routes(self):
        for route in ({"dst": "default", "dev": "tunl0"},
                      {"dst": "::/0", "dev": "tunl0"}):
            self.assertFalse(helper.disconnected_links(self.devices, self.addresses, [route]))


if __name__ == "__main__":
    unittest.main()

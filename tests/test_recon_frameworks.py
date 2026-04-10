import unittest

from core.intel.recon_frameworks import (
    build_bbot_scan_plan,
    filter_bbot_modules,
    filter_bbot_presets,
    load_amass_reference,
    load_bbot_reference,
    load_temp_framework_inventory,
)


class TestReconFrameworks(unittest.TestCase):
    def test_load_temp_framework_inventory_discovers_local_frameworks(self):
        payload = load_temp_framework_inventory()
        names = {str(row.get("name")) for row in payload.get("frameworks", []) if isinstance(row, dict)}
        self.assertIn("bbot", names)
        self.assertIn("amass", names)

    def test_load_bbot_reference_parses_modules_and_presets(self):
        payload = load_bbot_reference()
        self.assertGreater(payload.get("module_count", 0), 0)
        self.assertGreater(payload.get("preset_count", 0), 0)
        preset_names = {str(row.get("name")) for row in payload.get("presets", []) if isinstance(row, dict)}
        self.assertIn("subdomain-enum", preset_names)

    def test_filter_bbot_modules_finds_httpx(self):
        rows = filter_bbot_modules(search="httpx", limit=10)
        names = {str(row.get("name")) for row in rows if isinstance(row, dict)}
        self.assertIn("httpx", names)

    def test_filter_bbot_presets_finds_web(self):
        rows = filter_bbot_presets(search="web", limit=10)
        names = {str(row.get("name")) for row in rows if isinstance(row, dict)}
        self.assertIn("web-basic", names)

    def test_build_bbot_scan_plan_translates_to_silica_surface(self):
        payload = build_bbot_scan_plan(domain="example.com", preset_name="subdomain-enum")
        mapping = payload.get("silica_mapping", {})
        self.assertEqual(mapping.get("recon_mode"), "passive")
        self.assertEqual(mapping.get("surface_preset"), "deep")
        self.assertTrue(mapping.get("include_ct"))
        self.assertIn("silica-x.py surface example.com", str(payload.get("execution_preview", "")))

    def test_load_amass_reference_discovers_commands(self):
        payload = load_amass_reference()
        commands = payload.get("commands", [])
        self.assertIn("oam_enum", commands)
        self.assertIn("amass_engine", commands)


if __name__ == "__main__":
    unittest.main()

import unittest

from core.intel.recon_sources import (
    build_surface_recipe_plan,
    filter_recipe_modules,
    filter_recipes,
    load_graph_registry_reference,
    load_recursive_module_reference,
    load_source_inventory,
)


class TestReconFrameworks(unittest.TestCase):
    def test_load_source_inventory_discovers_local_profiles(self):
        payload = load_source_inventory()
        names = {str(row.get("name")) for row in payload.get("profiles", []) if isinstance(row, dict)}
        self.assertIn("recursive-modules", names)
        self.assertIn("graph-registry", names)

    def test_load_recursive_module_reference_parses_modules_and_recipes(self):
        payload = load_recursive_module_reference()
        self.assertGreater(payload.get("module_count", 0), 0)
        self.assertGreater(payload.get("recipe_count", 0), 0)
        recipe_names = {str(row.get("name")) for row in payload.get("recipes", []) if isinstance(row, dict)}
        self.assertIn("subdomain-enum", recipe_names)

    def test_filter_recipe_modules_finds_httpx(self):
        rows = filter_recipe_modules(search="httpx", limit=10)
        names = {str(row.get("name")) for row in rows if isinstance(row, dict)}
        self.assertIn("httpx", names)

    def test_filter_recipes_finds_web(self):
        rows = filter_recipes(search="web", limit=10)
        names = {str(row.get("name")) for row in rows if isinstance(row, dict)}
        self.assertIn("web-basic", names)

    def test_build_surface_recipe_plan_translates_to_sylica_surface(self):
        payload = build_surface_recipe_plan(domain="example.com", recipe_name="subdomain-enum")
        mapping = payload.get("sylica_mapping", {})
        self.assertEqual(mapping.get("recon_mode"), "passive")
        self.assertEqual(mapping.get("surface_preset"), "deep")
        self.assertTrue(mapping.get("include_ct"))
        self.assertIn("silica-x.py surface example.com", str(payload.get("execution_preview", "")))

    def test_load_graph_registry_reference_discovers_commands(self):
        payload = load_graph_registry_reference()
        commands = payload.get("commands", [])
        self.assertIn("oam_enum", commands)
        self.assertIn("oam_track", commands)


if __name__ == "__main__":
    unittest.main()

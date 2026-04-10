import unittest
from unittest.mock import patch

from core.interface.command_spec import SurfaceScanDirectives
from core.packet_crafting.models import CraftedPacketArtifact, PacketCraftingBundle
from core.packet_crafting.surface_runtime import build_surface_packet_crafting_plan


def _fake_bundle(scan_type: str) -> PacketCraftingBundle:
    artifact = CraftedPacketArtifact(
        engine_id=f"engine_{scan_type}",
        scan_type=scan_type,
        packet_label=f"{scan_type}_packet",
        packet_summary=f"{scan_type} summary",
        layer_stack=("IP", "TCP"),
        authorized_host="192.0.2.10",
        service_inquiry_port=80,
        timeout_seconds=2.0,
        delay_seconds=0.2,
        response_guidance="guidance",
        response_dependent=False,
        scapy_packet=object(),
    )
    return PacketCraftingBundle(
        bundle_id=f"bundle_{scan_type}",
        title=f"{scan_type} title",
        purpose=f"{scan_type} purpose",
        scan_types=(scan_type,),
        artifacts=(artifact,),
        notes=(f"{scan_type} note",),
    )


class TestSurfacePacketCrafting(unittest.TestCase):
    def test_build_surface_packet_crafting_plan_summarizes_requested_bundles(self):
        domain_result = {
            "target": "example.com",
            "resolved_addresses": ["192.0.2.10"],
            "surface_map": {"probe_plan": {"recommended_ports": [80, 443, 8080]}},
        }
        directives = SurfaceScanDirectives(
            recon_mode="active",
            scan_types=("syn", "udp", "service"),
            scan_verbosity="verbose",
            os_fingerprint_enabled=False,
            delay_seconds=0.2,
            active_inquiry_requested=True,
            notes=(),
        )
        with patch("core.packet_crafting.surface_runtime.craft_packet_bundle", side_effect=lambda scan_type, _: _fake_bundle(scan_type)):
            plan = build_surface_packet_crafting_plan(domain_result, scan_directives=directives)

        self.assertEqual(plan.authorized_host, "192.0.2.10")
        self.assertEqual(plan.requested_scan_types, ("syn", "udp"))
        self.assertEqual(plan.selected_ports, (80, 443, 8080))
        self.assertEqual(len(plan.bundles), 2)
        self.assertEqual(plan.bundles[0]["artifact_count"], 1)

    def test_build_surface_packet_crafting_plan_handles_missing_ports(self):
        domain_result = {"target": "example.com", "resolved_addresses": ["198.51.100.10"]}
        directives = SurfaceScanDirectives(
            recon_mode="active",
            scan_types=("syn",),
            scan_verbosity="standard",
            os_fingerprint_enabled=False,
            delay_seconds=0.0,
            active_inquiry_requested=True,
            notes=(),
        )
        plan = build_surface_packet_crafting_plan(domain_result, scan_directives=directives)
        self.assertEqual(plan.bundles, ())
        self.assertTrue(any("No recommended service ports" in note for note in plan.notes))


if __name__ == "__main__":
    unittest.main()

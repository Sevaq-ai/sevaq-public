from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PRIVATE_REPO = ROOT.parent / "sevaq-private"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.interfaces.plugin_loader import load_probe, load_routing_policy
from app.interfaces.probe import ProbeResult
from app.interfaces.routing import RoutingContext
from app.models.common import ReasoningMode


def _clear_private_modules() -> None:
    for key in list(sys.modules.keys()):
        if key.startswith("sevaq_private"):
            del sys.modules[key]


def test_plugin_loader_falls_back_to_public_when_private_unavailable() -> None:
    _clear_private_modules()
    sys.path[:] = [p for p in sys.path if "sevaq-private" not in p]

    probe = load_probe()
    policy = load_routing_policy()

    assert probe.__class__.__name__ == "HeuristicProbe"
    assert policy.__class__.__name__ == "HeuristicRoutingPolicy"


def test_loaded_probe_has_assess_method_and_valid_result() -> None:
    _clear_private_modules()
    sys.path[:] = [p for p in sys.path if "sevaq-private" not in p]
    probe = load_probe()

    assert hasattr(probe, "assess")
    result = probe.assess("Analyze this plan.", "deep")
    assert isinstance(result, ProbeResult)
    assert 0.0 <= result.score <= 1.0


def test_routing_policy_can_produce_fast_deep_verified() -> None:
    _clear_private_modules()
    if str(PRIVATE_REPO) not in sys.path:
        sys.path.insert(0, str(PRIVATE_REPO))
    policy = load_routing_policy()

    fast = policy.decide(
        RoutingContext(prompt="Summarize this sentence.", probe_result=ProbeResult(score=0.1, notes="n"))
    )
    deep = policy.decide(
        RoutingContext(prompt="Create a roadmap and tradeoff analysis.", probe_result=ProbeResult(score=0.3, notes="n"))
    )
    verified = policy.decide(
        RoutingContext(prompt="Medical guidance question.", probe_result=ProbeResult(score=0.2, notes="n"))
    )

    assert fast.mode == ReasoningMode.FAST
    assert deep.mode == ReasoningMode.DEEP
    assert verified.mode == ReasoningMode.VERIFIED

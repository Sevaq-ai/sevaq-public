from __future__ import annotations

import logging

from app.interfaces.probe import Probe
from app.interfaces.routing import BaseRoutingPolicy
from app.public_policies.heuristic_routing_policy import HeuristicRoutingPolicy
from app.public_probes.heuristic_probe import HeuristicProbe

logger = logging.getLogger(__name__)


def load_probe() -> Probe:
    try:
        from sevaq_private.probes.private_probe import PrivateProbe

        logger.info("Loaded probe implementation source=private")
        return PrivateProbe()
    except ImportError:
        logger.info("Loaded probe implementation source=public")
        return HeuristicProbe()


def load_routing_policy() -> BaseRoutingPolicy:
    try:
        from sevaq_private.policies.private_routing_policy import PrivateRoutingPolicy

        logger.info("Loaded routing implementation source=private")
        return PrivateRoutingPolicy()
    except ImportError:
        logger.info("Loaded routing implementation source=public")
        return HeuristicRoutingPolicy()

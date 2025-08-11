from __future__ import annotations

from typing import Callable, List, Optional

from .utils import PacketInfo


Rule = Callable[[PacketInfo], Optional[str]]


class RuleEngine:
    def __init__(self) -> None:
        self._rules: List[Rule] = []
        self._install_default_rules()

    def _install_default_rules(self) -> None:
        def rule_blocked_services(packet: PacketInfo) -> Optional[str]:
            blocked = {23, 135, 139, 445, 3389}
            if packet.dst_port is not None and packet.dst_port in blocked:
                return f"Access to blocked service on port {packet.dst_port}"
            return None

        def rule_unusually_large(packet: PacketInfo) -> Optional[str]:
            if packet.length >= 1500:
                return "Unusually large packet length"
            return None

        self._rules.extend([rule_blocked_services, rule_unusually_large])

    def add_rule(self, rule: Rule) -> None:
        self._rules.append(rule)

    def evaluate(self, packet: PacketInfo) -> List[str]:
        alerts: List[str] = []
        for rule in self._rules:
            try:
                message = rule(packet)
                if message:
                    alerts.append(message)
            except Exception:
                # Nie przerywamy – pojedyncza reguła nie może zatrzymać przetwarzania
                continue
        return alerts

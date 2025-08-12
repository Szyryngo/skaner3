from __future__ import annotations

from typing import Callable, List, Optional

from .utils import PacketInfo


Rule = Callable[[PacketInfo], Optional[str]]
"""Typ funkcji reguły: przyjmuje PacketInfo i zwraca komunikat alertu lub None."""


class RuleEngine:
    """Silnik reguł do wykrywania podejrzanej aktywności sieciowej.
    
    Umożliwia definiowanie i wykonywanie reguł bezpieczeństwa na pakietach sieciowych.
    Zawiera domyślne reguły dla typowych zagrożeń i pozwala dodawać własne reguły.
    """

    def __init__(self) -> None:
        """Inicjalizuje silnik reguł z domyślnym zestawem reguł bezpieczeństwa."""
        self._rules: List[Rule] = []
        self._install_default_rules()

    def _install_default_rules(self) -> None:
        """Instaluje domyślne reguły wykrywania zagrożeń.
        
        Dodaje reguły dla:
        - Blokowanych usług sieciowych (telnet, SMB, RDP, etc.)
        - Nieprawidłowo dużych pakietów
        """
        def rule_blocked_services(packet: PacketInfo) -> Optional[str]:
            """Wykrywa dostęp do potencjalnie niebezpiecznych usług.
            
            Args:
                packet: Informacje o pakiecie
                
            Returns:
                Komunikat o zagrożeniu lub None jeśli port jest bezpieczny
            """
            blocked = {23, 135, 139, 445, 3389}
            if packet.dst_port is not None and packet.dst_port in blocked:
                return f"Access to blocked service on port {packet.dst_port}"
            return None

        def rule_unusually_large(packet: PacketInfo) -> Optional[str]:
            """Wykrywa pakiety o nieprawidłowo dużym rozmiarze.
            
            Args:
                packet: Informacje o pakiecie
                
            Returns:
                Komunikat o zagrożeniu lub None jeśli rozmiar jest normalny
            """
            if packet.length >= 1500:
                return "Unusually large packet length"
            return None

        self._rules.extend([rule_blocked_services, rule_unusually_large])

    def add_rule(self, rule: Rule) -> None:
        """Dodaje nową regułę do silnika.
        
        Args:
            rule: Funkcja reguły zgodna z typem Rule
            
        Example:
            >>> def custom_rule(packet):
            ...     if packet.dst_port == 1234:
            ...         return "Custom suspicious port"
            ...     return None
            >>> engine.add_rule(custom_rule)
        """
        self._rules.append(rule)

    def evaluate(self, packet: PacketInfo) -> List[str]:
        """Ocenia pakiet względem wszystkich zainstalowanych reguł.
        
        Args:
            packet: Informacje o pakiecie do sprawdzenia
            
        Returns:
            Lista komunikatów alertów wygenerowanych przez reguły.
            Pusta lista jeśli żadna reguła nie zostanie naruszona.
            
        Note:
            Błędy w pojedynczych regułach nie przerywają całego procesu oceny.
        """
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

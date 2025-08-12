from __future__ import annotations

import threading
import time
from queue import Queue
from typing import Optional

try:
    from scapy.all import AsyncSniffer  # type: ignore
except Exception:  # scapy opcjonalne
    AsyncSniffer = None  # type: ignore

from .utils import PacketInfo, is_scapy_available, make_fake_packet, packet_from_scapy


class PacketSniffer:
    """Sniffer pakietów z dwoma trybami pracy: scapy i symulacja.
    
    Umożliwia przechwytywanie pakietów sieciowych z rzeczywistego interfejsu
    lub generowanie sztucznych pakietów do celów testowych/demonstracyjnych.
    """

    def __init__(
        self,
        packet_queue: Queue,
        use_simulation: bool = False,
        interface: Optional[str] = None,
        bpf_filter: Optional[str] = None,
        interval_seconds: float = 0.2,
    ) -> None:
        """Inicjalizuje sniffer pakietów z określonymi parametrami.
        
        Args:
            packet_queue: Kolejka do której będą dodawane przechwycone pakiety
            use_simulation: Czy wymusić tryb symulacji zamiast rzeczywistego sniffingu
            interface: Nazwa interfejsu sieciowego (None = domyślny)
            bpf_filter: Filtr BPF dla ograniczenia przechwytywanych pakietów
            interval_seconds: Interwał między pakietami w trybie symulacji
        """
        self.packet_queue = packet_queue
        self.use_simulation = use_simulation or not is_scapy_available()
        self.interface = interface
        self.bpf_filter = bpf_filter
        self.interval_seconds = interval_seconds

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._sniffer = None

    def start(self) -> None:
        """Rozpoczyna przechwytywanie pakietów.
        
        Automatycznie wybiera tryb scapy lub symulacji w zależności
        od dostępności bibliotek i konfiguracji.
        """
        if self._running:
            return
        self._running = True

        if not self.use_simulation and AsyncSniffer is not None:
            self._start_scapy_sniffer()
        else:
            self._start_simulation_thread()

    def stop(self) -> None:
        """Zatrzymuje przechwytywanie pakietów i zwalnia zasoby.
        
        Bezpiecznie zamyka sniffery i wątki z timeout 2 sekund.
        """
        self._running = False

        if self._sniffer is not None:
            try:
                self._sniffer.stop()  # type: ignore[attr-defined]
            except Exception:
                pass
            self._sniffer = None

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    # --- Tryb scapy ---
    def _start_scapy_sniffer(self) -> None:
        """Uruchamia rzeczywisty sniffer używając biblioteki scapy.
        
        W przypadku błędu automatycznie przełącza na tryb symulacji.
        """
        def on_packet(scapy_packet: object) -> None:
            info = packet_from_scapy(scapy_packet)
            if info is not None:
                self.packet_queue.put(info)

        try:
            self._sniffer = AsyncSniffer(
                iface=self.interface,
                filter=self.bpf_filter,
                store=False,
                prn=on_packet,
            )
            self._sniffer.start()
        except Exception:
            # Awaryjnie przejdź do symulacji
            self.use_simulation = True
            self._sniffer = None
            self._start_simulation_thread()

    # --- Tryb symulacji ---
    def _start_simulation_thread(self) -> None:
        """Uruchamia wątek generujący sztuczne pakiety dla demonstracji.
        
        Generuje pakiety w regularnych odstępach określonych przez interval_seconds.
        """
        def run() -> None:
            while self._running:
                packet = make_fake_packet()
                self.packet_queue.put(packet)
                time.sleep(self.interval_seconds)

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

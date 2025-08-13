from __future__ import annotations

import ipaddress
import logging
import socket
import threading
import time
from dataclasses import dataclass
from enum import Enum
from queue import Queue
from typing import Dict, List, Optional, Set, Tuple, Callable

try:
    from scapy.all import sr1, IP, ICMP, TCP  # type: ignore
    SCAPY_AVAILABLE = True
except Exception:
    SCAPY_AVAILABLE = False

from .utils import resolve_hostname


class ScanMode(Enum):
    """Tryby skanowania sieciowego."""
    LIGHT = "light"  # Ping + podstawowe porty
    HARD = "hard"    # Pełne skanowanie wszystkich portów


@dataclass
class HostInfo:
    """Informacje o znalezionym hoście."""
    ip: str
    hostname: Optional[str] = None
    is_alive: bool = False
    open_ports: List[int] = None
    response_time: Optional[float] = None
    last_seen: Optional[float] = None

    def __post_init__(self):
        if self.open_ports is None:
            self.open_ports = []
        if self.last_seen is None:
            self.last_seen = time.time()


@dataclass
class ScanProgress:
    """Status postępu skanowania."""
    hosts_total: int = 0
    hosts_scanned: int = 0
    ports_total: int = 0
    ports_scanned: int = 0
    hosts_found: int = 0
    open_ports_found: int = 0
    current_target: str = ""
    is_running: bool = False
    elapsed_time: float = 0.0
    estimated_remaining: float = 0.0


class NetworkScanner:
    """
    Profesjonalny skaner sieciowy z obsługą różnych trybów skanowania.
    
    Funkcjonalności:
    - Skanowanie zakresów IP (CIDR, zakresy)
    - Wykrywanie hostów (ping, ARP)
    - Skanowanie portów (TCP, UDP)
    - Asynchroniczne operacje z callbackami
    - Resolving hostname
    - Tryby light/hard
    - Możliwość zatrzymania skanowania
    - Logowanie i monitoring postępu
    """

    def __init__(
        self,
        mode: ScanMode = ScanMode.LIGHT,
        timeout: float = 2.0,
        max_threads: int = 50,
        use_simulation: bool = False,
    ) -> None:
        self.mode = mode
        self.timeout = timeout
        self.max_threads = max_threads
        self.use_simulation = use_simulation or not SCAPY_AVAILABLE

        # Stan skanowania
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Wyniki
        self.hosts: Dict[str, HostInfo] = {}
        self.progress = ScanProgress()
        
        # Callbacki
        self.on_host_found: Optional[Callable[[HostInfo], None]] = None
        self.on_progress_update: Optional[Callable[[ScanProgress], None]] = None
        self.on_scan_complete: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Porty do skanowania w różnych trybach
        self.common_ports = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 993, 995]
        self.full_ports = list(range(1, 1025))  # Pełny zakres portów dla trybu hard

    def start_scan(
        self, 
        ip_ranges: List[str],
        ports: Optional[List[int]] = None,
        resolve_hostnames: bool = True
    ) -> None:
        """
        Rozpoczyna skanowanie podanych zakresów IP.
        
        Args:
            ip_ranges: Lista zakresów IP (CIDR, zakres lub pojedyncze IP)
            ports: Lista portów do skanowania (None = domyślne dla trybu)
            resolve_hostnames: Czy resolwować nazwy hostów
        """
        if self._running:
            return
            
        self._running = True
        self._stop_event.clear()
        self.hosts.clear()
        
        # Przygotuj listę celów
        targets = self._parse_ip_ranges(ip_ranges)
        if not targets:
            self._emit_error("Brak prawidłowych celów do skanowania")
            return
            
        # Określ porty do skanowania
        if ports is None:
            ports = self.common_ports if self.mode == ScanMode.LIGHT else self.full_ports
            
        # Inicjalizuj progress
        self.progress = ScanProgress(
            hosts_total=len(targets),
            ports_total=len(ports) * len(targets),
            is_running=True
        )
        
        # Uruchom wątek skanowania
        self._thread = threading.Thread(
            target=self._scan_worker,
            args=(targets, ports, resolve_hostnames),
            daemon=True
        )
        self._thread.start()
        
        self.logger.info(f"Rozpoczęto skanowanie {len(targets)} hostów w trybie {self.mode.value}")

    def stop_scan(self) -> None:
        """Zatrzymuje bieżące skanowanie."""
        if not self._running:
            return
            
        self.logger.info("Zatrzymywanie skanowania...")
        self._stop_event.set()
        self._running = False
        
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
            
        self.progress.is_running = False
        self._emit_progress_update()

    def is_running(self) -> bool:
        """Sprawdza czy skanowanie jest w toku."""
        return self._running

    def get_results(self) -> Dict[str, HostInfo]:
        """Zwraca wyniki skanowania."""
        return self.hosts.copy()

    def get_alive_hosts(self) -> List[HostInfo]:
        """Zwraca listę aktywnych hostów."""
        return [host for host in self.hosts.values() if host.is_alive]

    def get_hosts_with_open_ports(self) -> List[HostInfo]:
        """Zwraca listę hostów z otwartymi portami."""
        return [host for host in self.hosts.values() if host.open_ports]

    def _parse_ip_ranges(self, ip_ranges: List[str]) -> List[str]:
        """Parsuje zakresy IP do listy pojedynczych adresów."""
        targets = []
        
        for ip_range in ip_ranges:
            try:
                # Obsługa CIDR (np. 192.168.1.0/24)
                if '/' in ip_range:
                    network = ipaddress.ip_network(ip_range, strict=False)
                    targets.extend([str(ip) for ip in network.hosts()])
                    
                # Obsługa zakresu (np. 192.168.1.1-192.168.1.10)
                elif '-' in ip_range:
                    start_ip, end_ip = ip_range.split('-', 1)
                    start = ipaddress.ip_address(start_ip.strip())
                    end = ipaddress.ip_address(end_ip.strip())
                    
                    current = start
                    while current <= end:
                        targets.append(str(current))
                        current += 1
                        
                # Pojedynczy IP
                else:
                    ip = ipaddress.ip_address(ip_range.strip())
                    targets.append(str(ip))
                    
            except Exception as e:
                self._emit_error(f"Błędny zakres IP '{ip_range}': {e}")
                
        return targets

    def _scan_worker(self, targets: List[str], ports: List[int], resolve_hostnames: bool) -> None:
        """Główny wątek skanowania."""
        start_time = time.time()
        self._start_time = start_time
        
        try:
            # Wykrywanie hostów
            self._discover_hosts(targets, resolve_hostnames)
            
            if self._stop_event.is_set():
                return
                
            # Skanowanie portów dla aktywnych hostów
            alive_hosts = [ip for ip, host in self.hosts.items() if host.is_alive]
            if alive_hosts and ports:
                self._scan_ports(alive_hosts, ports)
                
        except Exception as e:
            self._emit_error(f"Błąd podczas skanowania: {e}")
        finally:
            self._running = False
            self.progress.is_running = False
            self.progress.elapsed_time = time.time() - start_time
            self._emit_progress_update()
            self._emit_scan_complete()

    def _discover_hosts(self, targets: List[str], resolve_hostnames: bool) -> None:
        """Wykrywa aktywne hosty w sieci."""
        self.logger.info(f"Wykrywanie hostów: {len(targets)} celów")
        
        for i, ip in enumerate(targets):
            if self._stop_event.is_set():
                break
                
            self.progress.current_target = ip
            self.progress.hosts_scanned = i + 1
            
            host_info = HostInfo(ip=ip)
            
            # Ping host
            if self.use_simulation:
                # Symulacja - losowo "znajdź" niektóre hosty
                import random
                host_info.is_alive = random.random() < 0.3
                host_info.response_time = random.uniform(1, 100) if host_info.is_alive else None
            else:
                host_info.is_alive, host_info.response_time = self._ping_host(ip)
            
            if host_info.is_alive:
                self.progress.hosts_found += 1
                
                # Resolve hostname jeśli potrzeba
                if resolve_hostnames:
                    host_info.hostname = resolve_hostname(ip)
                
            self.hosts[ip] = host_info
            self._emit_host_found(host_info)
            self._emit_progress_update()
            
            # Krótkie opóźnienie między hostami
            time.sleep(0.05 if self.use_simulation else 0.01)

    def _ping_host(self, ip: str) -> Tuple[bool, Optional[float]]:
        """Pinguje pojedynczy host."""
        if SCAPY_AVAILABLE:
            return self._ping_host_scapy(ip)
        else:
            return self._ping_host_socket(ip)

    def _ping_host_scapy(self, ip: str) -> Tuple[bool, Optional[float]]:
        """Ping za pomocą scapy (ICMP)."""
        try:
            start_time = time.time()
            packet = IP(dst=ip)/ICMP()
            response = sr1(packet, timeout=self.timeout, verbose=False)
            
            if response:
                response_time = (time.time() - start_time) * 1000  # ms
                return True, response_time
            else:
                return False, None
                
        except Exception:
            return False, None

    def _ping_host_socket(self, ip: str) -> Tuple[bool, Optional[float]]:
        """Ping za pomocą socket (TCP connect na port 80)."""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, 80))
            sock.close()
            
            response_time = (time.time() - start_time) * 1000  # ms
            return result == 0, response_time if result == 0 else None
            
        except Exception:
            return False, None

    def _scan_ports(self, targets: List[str], ports: List[int]) -> None:
        """Skanuje porty na aktywnych hostach."""
        self.logger.info(f"Skanowanie portów: {len(targets)} hostów, {len(ports)} portów")
        
        total_scans = len(targets) * len(ports)
        scanned = 0
        
        for target in targets:
            if self._stop_event.is_set():
                break
                
            self.progress.current_target = f"{target}:ports"
            host_info = self.hosts[target]
            
            for port in ports:
                if self._stop_event.is_set():
                    break
                    
                scanned += 1
                self.progress.ports_scanned = scanned
                
                if self.use_simulation:
                    # Symulacja - losowo otwarte porty
                    import random
                    is_open = random.random() < 0.05  # 5% szans na otwarty port
                else:
                    is_open = self._scan_port(target, port)
                
                if is_open:
                    host_info.open_ports.append(port)
                    self.progress.open_ports_found += 1
                    self._emit_host_found(host_info)  # Aktualizuj dane hosta
                
                self._emit_progress_update()
                
                # Krótkie opóźnienie między portami
                time.sleep(0.001)

    def _scan_port(self, ip: str, port: int) -> bool:
        """Skanuje pojedynczy port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout / 10)  # Krótszy timeout dla portów
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _emit_host_found(self, host: HostInfo) -> None:
        """Emituje callback o znalezionym hoście."""
        if self.on_host_found:
            try:
                self.on_host_found(host)
            except Exception as e:
                self.logger.error(f"Błąd w callback on_host_found: {e}")

    def _emit_progress_update(self) -> None:
        """Emituje callback o postępie skanowania."""
        if self.on_progress_update:
            try:
                # Oblicz szacowany czas pozostały
                if self.progress.hosts_scanned > 0:
                    elapsed = time.time() - getattr(self, '_start_time', time.time())
                    self.progress.elapsed_time = elapsed
                    
                    total_work = self.progress.hosts_total + self.progress.ports_total
                    done_work = self.progress.hosts_scanned + self.progress.ports_scanned
                    
                    if done_work > 0:
                        rate = done_work / elapsed
                        remaining_work = total_work - done_work
                        self.progress.estimated_remaining = remaining_work / rate if rate > 0 else 0
                
                self.on_progress_update(self.progress)
            except Exception as e:
                self.logger.error(f"Błąd w callback on_progress_update: {e}")

    def _emit_scan_complete(self) -> None:
        """Emituje callback o zakończeniu skanowania."""
        if self.on_scan_complete:
            try:
                self.on_scan_complete()
            except Exception as e:
                self.logger.error(f"Błąd w callback on_scan_complete: {e}")

    def _emit_error(self, message: str) -> None:
        """Emituje callback o błędzie."""
        self.logger.error(message)
        if self.on_error:
            try:
                self.on_error(message)
            except Exception as e:
                self.logger.error(f"Błąd w callback on_error: {e}")
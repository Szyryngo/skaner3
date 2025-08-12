from __future__ import annotations

import random
import socket
import time
from dataclasses import dataclass
from functools import lru_cache
from datetime import datetime
from typing import Any, Dict, Optional

try:
    # Importowane opcjonalnie – środowisko bez scapy przejdzie w tryb symulacji
    from scapy.all import IP, TCP, UDP, Raw  # type: ignore
    SCAPY_AVAILABLE = True
except Exception:
    SCAPY_AVAILABLE = False

try:
    import psutil  # type: ignore
    PSUTIL_AVAILABLE = True
except Exception:
    PSUTIL_AVAILABLE = False


@dataclass
class PacketInfo:
    """Struktura danych zawierająca informacje o pakiecie sieciowym.
    
    Attributes:
        timestamp: Znacznik czasowy przechwycenia pakietu
        src_ip: Adres IP źródłowy
        dst_ip: Adres IP docelowy  
        src_port: Port źródłowy (None dla protokołów bez portów)
        dst_port: Port docelowy (None dla protokołów bez portów)
        protocol: Nazwa protokołu (TCP, UDP, IP, etc.)
        length: Długość pakietu w bajtach
        raw_bytes: Surowe bajty pakietu (opcjonalne)
    """
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: Optional[int]
    dst_port: Optional[int]
    protocol: str
    length: int
    raw_bytes: Optional[bytes] = None


def is_scapy_available() -> bool:
    """Sprawdza czy biblioteka scapy jest dostępna w środowisku.
    
    Returns:
        True jeśli scapy można zaimportować, False w przeciwnym razie
    """
    return SCAPY_AVAILABLE


def now_timestamp() -> float:
    """Zwraca aktualny znacznik czasowy UNIX.
    
    Returns:
        Timestamp jako liczba zmiennoprzecinkowa sekund od epoki UNIX
    """
    return time.time()


def format_timestamp_human(ts: float) -> str:
    """Formatuje timestamp do czytelnej formy HH:MM:SS.mmm.
    
    Args:
        ts: Timestamp UNIX do sformatowania
        
    Returns:
        Sformatowany czas w formacie HH:MM:SS.mmm
    """
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S.%f")[:-3]


def packet_from_scapy(scapy_packet: Any) -> Optional[PacketInfo]:
    """Konwertuje pakiet scapy na strukturę PacketInfo.
    
    Args:
        scapy_packet: Obiekt pakietu z biblioteki scapy
        
    Returns:
        PacketInfo lub None jeśli konwersja się nie powiodła lub scapy niedostępne
        
    Note:
        Funkcja obsługuje protokoły TCP, UDP i IP. Inne protokoły są oznaczane jako "OTHER".
    """
    if not SCAPY_AVAILABLE:
        return None

    try:
        protocol = "OTHER"
        src_ip = getattr(scapy_packet[IP], "src", "?") if scapy_packet.haslayer(IP) else "?"
        dst_ip = getattr(scapy_packet[IP], "dst", "?") if scapy_packet.haslayer(IP) else "?"

        src_port: Optional[int] = None
        dst_port: Optional[int] = None

        if scapy_packet.haslayer(TCP):
            protocol = "TCP"
            src_port = int(scapy_packet[TCP].sport)
            dst_port = int(scapy_packet[TCP].dport)
        elif scapy_packet.haslayer(UDP):
            protocol = "UDP"
            src_port = int(scapy_packet[UDP].sport)
            dst_port = int(scapy_packet[UDP].dport)
        elif scapy_packet.haslayer(IP):
            protocol = "IP"

        raw = bytes(scapy_packet)
        length = int(len(raw))

        return PacketInfo(
            timestamp=now_timestamp(),
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            length=length,
            raw_bytes=raw,
        )
    except Exception:
        return None


def _random_ip() -> str:
    """Generuje losowy adres IP w zakresie 1-254 dla każdego oktetu.
    
    Returns:
        Losowy adres IP w formacie string
    """
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def make_fake_packet() -> PacketInfo:
    """Tworzy sztuczny pakiet dla celów testowych i demonstracyjnych.
    
    Returns:
        PacketInfo z losowymi ale realistycznymi danymi pakietu
        
    Note:
        Używane gdy scapy nie jest dostępne lub do symulacji ruchu sieciowego.
    """
    protocol = random.choice(["TCP", "UDP", "IP"])
    src_port = random.randint(1024, 65535) if protocol in {"TCP", "UDP"} else None
    dst_port = random.choice([53, 80, 123, 443, 22, 23, 3389]) if protocol in {"TCP", "UDP"} else None
    length = random.randint(60, 1600)
    # Losowa treść bajtów do hexdump/ASCII
    raw = bytes(random.getrandbits(8) for _ in range(length))

    return PacketInfo(
        timestamp=now_timestamp(),
        src_ip=_random_ip(),
        dst_ip=_random_ip(),
        src_port=src_port,
        dst_port=dst_port,
        protocol=protocol,
        length=length,
        raw_bytes=raw,
    )


def resolve_hostname(ip_address: str) -> str:
    """Próbuje rozwiązać adres IP na nazwę hosta.
    
    Args:
        ip_address: Adres IP do rozwiązania
        
    Returns:
        Nazwa hosta lub oryginalny adres IP jeśli rozwiązanie się nie powiodło
    """
    try:
        return socket.gethostbyaddr(ip_address)[0]
    except Exception:
        return ip_address


def packetinfo_to_row(packet: PacketInfo) -> Dict[str, str]:
    """Konwertuje PacketInfo na słownik stringów dla wyświetlania w tabelach.
    
    Args:
        packet: Informacje o pakiecie
        
    Returns:
        Słownik z kluczami: time, src_ip, dst_ip, src_port, dst_port, protocol, length
    """
    return {
        "time": format_timestamp_human(packet.timestamp),
        "src_ip": packet.src_ip,
        "dst_ip": packet.dst_ip,
        "src_port": str(packet.src_port) if packet.src_port is not None else "-",
        "dst_port": str(packet.dst_port) if packet.dst_port is not None else "-",
        "protocol": packet.protocol,
        "length": str(packet.length),
    }


def _chunk_bytes(data: bytes, width: int) -> list[bytes]:
    """Dzieli dane bajtowe na fragmenty o określonej szerokości.
    
    Args:
        data: Dane do podzielenia
        width: Szerokość każdego fragmentu
        
    Returns:
        Lista fragmentów bajtowych
    """
    return [data[i : i + width] for i in range(0, len(data), width)]


def bytes_to_hex_dump(data: bytes, width: int = 16) -> str:
    """Konwertuje dane bajtowe na czytelny hex dump w stylu hexdump.
    
    Args:
        data: Dane do skonwertowania
        width: Liczba bajtów na linię (domyślnie 16)
        
    Returns:
        Sformatowany hex dump zawierający offset, wartości hex i reprezentację ASCII
        
    Example:
        >>> data = b"Hello World!"
        >>> print(bytes_to_hex_dump(data))
        0000: 48 65 6C 6C 6F 20 57 6F 72 6C 64 21              Hello World!
    """
    lines: list[str] = []
    for offset, chunk in enumerate(_chunk_bytes(data, width)):
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{offset*width:04X}: {hex_part:<{width*3}}  {ascii_part}")
    return "\n".join(lines)


def bytes_to_ascii(data: bytes) -> str:
    """Konwertuje dane bajtowe na reprezentację ASCII z maskowaniem.
    
    Args:
        data: Dane do skonwertowania
        
    Returns:
        String z drukowalnymi znakami ASCII, nidrukowane zastąpione kropkami
    """
    return "".join(chr(b) if 32 <= b <= 126 else "." for b in data)


@lru_cache(maxsize=2048)
def geolocate_ip(ip_address: str) -> Dict[str, str]:
    """Prosta geolokalizacja przez usługę ip-api.com z pamięcią podręczną.

    Args:
        ip_address: Adres IP do geolokalizacji
        
    Returns:
        Słownik z kluczami: country, regionName, city, isp.
        W przypadku błędu wszystkie wartości to "Unknown".
        
    Note:
        Wyniki są cachowane (LRU cache) aby ograniczyć zapytania do API.
        Timeout zapytania wynosi 2.5 sekundy.
    """
    try:
        import requests  # import lokalny, by nie wymagać w każdym środowisku

        resp = requests.get(
            f"http://ip-api.com/json/{ip_address}?fields=status,country,regionName,city,isp,query",
            timeout=2.5,
        )
        data = resp.json() if resp.ok else {}
        if data.get("status") == "success":
            return {
                "country": data.get("country", "Unknown"),
                "regionName": data.get("regionName", "Unknown"),
                "city": data.get("city", "Unknown"),
                "isp": data.get("isp", "Unknown"),
            }
    except Exception:
        pass
    return {"country": "Unknown", "regionName": "Unknown", "city": "Unknown", "isp": "Unknown"}


# --- Interfejsy sieciowe ---
def _categorize_interface(name: str) -> str:
    """Kategoryzuje interfejs sieciowy na podstawie nazwy.
    
    Args:
        name: Nazwa interfejsu sieciowego
        
    Returns:
        Kategoria interfejsu: Wi‑Fi, Ethernet, Loopback, Cellular, Virtual lub Other
    """
    n = name.lower()
    if any(x in n for x in ["wi-fi", "wifi", "wlan", "wireless"]):
        return "Wi‑Fi"
    if any(x in n for x in ["eth", "ethernet", "en0", "en1", "en2"]):
        return "Ethernet"
    if any(x in n for x in ["loopback", "lo"]):
        return "Loopback"
    if any(x in n for x in ["ppp", "wwan", "cell"]):
        return "Cellular"
    if any(x in n for x in ["virtual", "veth", "vethernet", "hyper-v", "vmware", "vbox"]):
        return "Virtual"
    return "Other"


def list_network_interfaces(show_inactive: bool = False) -> list[dict]:
    """Zwraca listę interfejsów sieciowych z czytelnymi etykietami.

    Args:
        show_inactive: Czy uwzględnić nieaktywne interfejsy (domyślnie False)
        
    Returns:
        Lista słowników, każdy zawiera: id, name, type, is_up, ipv4.
        Posortowana: aktywne najpierw, potem alfabetycznie po typie i nazwie.
        
    Note:
        Wymaga biblioteki psutil. Zwraca pustą listę jeśli psutil niedostępne.
    """
    results: list[dict] = []
    if not PSUTIL_AVAILABLE:
        return results

    try:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        for if_name, st in stats.items():
            is_up = bool(st.isup)
            if not is_up and not show_inactive:
                continue
            ipv4 = ""
            for a in addrs.get(if_name, []):
                if getattr(a, "family", None) == socket.AF_INET and a.address:
                    ipv4 = a.address
                    break
            category = _categorize_interface(if_name)
            results.append(
                {
                    "id": if_name,
                    "name": if_name,
                    "type": category,
                    "is_up": is_up,
                    "ipv4": ipv4,
                }
            )
        # Sortuj: aktywne najpierw, potem alfabetycznie po typie i nazwie
        results.sort(key=lambda x: (not x["is_up"], x["type"], x["name"]))
    except Exception:
        return []
    return results


# --- Rotujący logger CSV ---
class LogWriter:
    """Prosty zapis rotujący do CSV/TXT na podstawie liczby wierszy.

    Gdy `max_rows_per_file` zostanie przekroczone, plik jest zamykany i
    otwierany nowy z przyrostowym sufiksem numerycznym.
    
    Attributes:
        base_path: Ścieżka bazowa dla plików
        is_csv: Czy format to CSV (True) czy TXT (False)
        max_rows_per_file: Maksymalna liczba wierszy na plik
        headers: Opcjonalne nagłówki kolumn dla CSV
    """

    def __init__(self, base_path: str, *, is_csv: bool = True, max_rows_per_file: int = 100000, headers: Optional[list[str]] = None) -> None:
        """Inicjalizuje LogWriter z określonymi parametrami rotacji.
        
        Args:
            base_path: Bazowa ścieżka pliku (bez numeru)
            is_csv: True dla formatu CSV z separatorami, False dla TXT z tabulatorami
            max_rows_per_file: Liczba wierszy po której następuje rotacja
            headers: Opcjonalne nagłówki dla plików CSV
        """
        import os
        import csv

        self.base_path = base_path
        self.is_csv = is_csv
        self.max_rows_per_file = max_rows_per_file
        self.headers = headers[:] if headers else None
        self._idx = 0
        self._rows = 0
        self._file = None
        self._writer = None
        self._csv = csv
        self._os = os
        self._open_new()

    def _open_new(self) -> None:
        """Otwiera nowy plik z kolejnym numerem w sekwencji.
        
        Zamyka poprzedni plik i tworzy nowy z odpowiednim rozszerzeniem
        i nagłówkami (jeśli format CSV).
        """
        if self._file:
            try:
                self._file.close()
            except Exception:
                pass
        root, ext = self._os.path.splitext(self.base_path)
        path = f"{root}.{self._idx}{ext or ('.csv' if self.is_csv else '.txt')}"
        self._file = open(path, "w", newline="", encoding="utf-8")
        if self.is_csv:
            self._writer = self._csv.writer(self._file)
            if self.headers:
                self._writer.writerow(self.headers)
        self._rows = 0
        self._idx += 1

    def write_row(self, row: list[str]) -> None:
        """Zapisuje wiersz danych do aktualnego pliku.
        
        Args:
            row: Lista stringów reprezentująca wiersz danych
            
        Note:
            Automatycznie rotuje pliki gdy osiągnięty zostanie max_rows_per_file.
        """
        if self.is_csv and self._writer is not None:
            self._writer.writerow(row)
        else:
            self._file.write("\t".join(row) + "\n")
        self._rows += 1
        if self._rows >= self.max_rows_per_file:
            self._open_new()

    def close(self) -> None:
        """Zamyka aktualny plik i kończy operacje zapisu.
        
        Należy wywołać przed zakończeniem pracy z LogWriter.
        """
        if self._file:
            try:
                self._file.close()
            except Exception:
                pass


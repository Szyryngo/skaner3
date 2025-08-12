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
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: Optional[int]
    dst_port: Optional[int]
    protocol: str
    length: int
    raw_bytes: Optional[bytes] = None
    ai_score: float = 0.0  # AI anomaly score for threat level filtering


def is_scapy_available() -> bool:
    return SCAPY_AVAILABLE


def now_timestamp() -> float:
    return time.time()


def format_timestamp_human(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S.%f")[:-3]


def packet_from_scapy(scapy_packet: Any) -> Optional[PacketInfo]:
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
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def make_fake_packet() -> PacketInfo:
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
    try:
        return socket.gethostbyaddr(ip_address)[0]
    except Exception:
        return ip_address


def packetinfo_to_row(packet: PacketInfo) -> Dict[str, str]:
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
    return [data[i : i + width] for i in range(0, len(data), width)]


def bytes_to_hex_dump(data: bytes, width: int = 16) -> str:
    lines: list[str] = []
    for offset, chunk in enumerate(_chunk_bytes(data, width)):
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{offset*width:04X}: {hex_part:<{width*3}}  {ascii_part}")
    return "\n".join(lines)


def bytes_to_ascii(data: bytes) -> str:
    return "".join(chr(b) if 32 <= b <= 126 else "." for b in data)


@lru_cache(maxsize=2048)
def geolocate_ip(ip_address: str) -> Dict[str, str]:
    """Prosta geolokalizacja przez usługę ip-api.com.

    Zwraca słownik: { country, regionName, city, isp }. W przypadku błędu -> Unknown.
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
    """Zwraca listę interfejsów z czytelnymi etykietami.

    Każdy element: { id, name, type, is_up, ipv4 }
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
    otwierany nowy z przyrostowym sufiksem.
    """

    def __init__(self, base_path: str, *, is_csv: bool = True, max_rows_per_file: int = 100000, headers: Optional[list[str]] = None) -> None:
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
        if self.is_csv and self._writer is not None:
            self._writer.writerow(row)
        else:
            self._file.write("\t".join(row) + "\n")
        self._rows += 1
        if self._rows >= self.max_rows_per_file:
            self._open_new()

    def close(self) -> None:
        if self._file:
            try:
                self._file.close()
            except Exception:
                pass


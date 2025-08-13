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
    from scapy.all import IP, TCP, UDP, Raw, Ether  # type: ignore
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
    # Device information
    src_mac: str = ""
    dst_mac: str = ""
    user_agent: str = ""


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
        
        # Extract device information
        src_mac = ""
        dst_mac = ""
        user_agent = ""
        
        try:
            if scapy_packet.haslayer(Ether):
                src_mac = scapy_packet[Ether].src or ""
                dst_mac = scapy_packet[Ether].dst or ""
        except Exception:
            pass
            
        try:
            user_agent = extract_user_agent_from_packet(scapy_packet)
        except Exception:
            pass

        return PacketInfo(
            timestamp=now_timestamp(),
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            length=length,
            raw_bytes=raw,
            src_mac=src_mac,
            dst_mac=dst_mac,
            user_agent=user_agent,
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
    
    # Generate fake MAC addresses for simulation
    fake_src_mac = ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])
    fake_dst_mac = ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])
    fake_user_agent = random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ""
    ])

    return PacketInfo(
        timestamp=now_timestamp(),
        src_ip=_random_ip(),
        dst_ip=_random_ip(),
        src_port=src_port,
        dst_port=dst_port,
        protocol=protocol,
        length=length,
        raw_bytes=raw,
        src_mac=fake_src_mac,
        dst_mac=fake_dst_mac,
        user_agent=fake_user_agent,
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


# --- Network Devices ---
@dataclass
class NetworkDevice:
    """Informacje o urządzeniu wykrytym w sieci"""
    ip_address: str
    mac_address: str
    hostname: str
    oui_vendor: str
    user_agent: str
    protocols: set[str]
    first_seen: float
    last_seen: float


def get_mac_address_from_packet(scapy_packet: Any) -> Optional[str]:
    """Wyciąg adresu MAC z pakietu scapy"""
    if not SCAPY_AVAILABLE or not scapy_packet:
        return None
    
    try:
        if scapy_packet.haslayer(Ether):
            return scapy_packet[Ether].src
    except Exception:
        pass
    return None


@lru_cache(maxsize=1024)
def get_oui_vendor(mac_address: str) -> str:
    """Próba identyfikacji producenta na podstawie OUI (pierwszych 3 bajtów MAC)"""
    if not mac_address or len(mac_address) < 8:
        return "Unknown"
    
    # Wyciągnij pierwsze 3 bajty MAC (OUI)
    oui = mac_address.replace(":", "").replace("-", "").upper()[:6]
    
    # Podstawowe mapowanie OUI -> vendor (można rozszerzyć)
    oui_vendors = {
        "000C29": "VMware",
        "080027": "VirtualBox",
        "005056": "VMware",
        "0050F2": "Microsoft",
        "001B63": "Apple",
        "F4F26D": "Google",
        "B8E856": "Apple",
        "20C9D0": "Apple",
        "003065": "Apple",
        "000D93": "Apple",
        "00A040": "Apple",
        "00061B": "Apple",
        "0013CE": "Intel",
        "001CC4": "Intel",
        "0022FB": "Intel",
        "001E64": "Intel",
        "7C7A91": "Cisco",
        "00D0C9": "Cisco",
        "001094": "Cisco",
        "00192F": "Cisco",
        "00E014": "Cisco",
        "0019E7": "Cisco",
        "D85DE2": "Cisco",
        "006008": "Cisco",
        "00A0C9": "Cisco",
        "001560": "Cisco",
        "002155": "Cisco",
        "00907C": "Cisco",
        "00D098": "Cisco",
        "00906D": "Cisco",
        "001C0E": "Cisco",
        "001A30": "Cisco",
        "000FE2": "Cisco",
        "0013C4": "Cisco",
        "00E099": "Cisco",
        "000ECB": "Cisco",
        "000A8A": "Cisco",
        "000ED7": "Cisco",
        "0017E0": "Cisco",
        "001279": "Cisco",
        "0019AA": "Cisco",
        "001C58": "Cisco",
        "0016C7": "Cisco",
        "0015C6": "Cisco",
        "00230D": "Cisco",
        "001CDF": "Cisco",
        "001F9E": "Cisco",
        "0024F7": "Cisco",
        "002467": "Cisco",
        "0025B5": "Cisco",
        "002764": "Cisco",
        "0026F1": "Cisco",
        "002854": "Cisco",
        "0029A3": "Cisco",
        "002BC1": "Cisco",
        "002FD0": "Cisco",
        "0031FD": "Cisco",
        "003471": "Cisco",
        "003A98": "Cisco",
        "003A9A": "Cisco",
        "003A9B": "Cisco",
        "003A9C": "Cisco",
        "4C00AD": "Cisco",
        "504618": "Cisco",
        "0894EF": "Cisco",
        "10F3DB": "Cisco",
        "1C99E8": "Cisco",
        "20B9E0": "Cisco",
        "28C7CE": "Cisco",
        "3CDCBC": "Cisco",
        "44D3CA": "Cisco",
        "50E085": "Cisco",
        "5C5015": "Cisco",
        "689C70": "Cisco",
        "6CAB31": "Cisco",
        "70E4C7": "Cisco",
        "7426AC": "Cisco",
        "84B8AC": "Cisco",
        "881D74": "Cisco",
        "8C60C3": "Cisco",
        "9CE6E7": "Cisco",
        "A0EC80": "Cisco",
        "A46CF1": "Cisco",
        "ACF2C5": "Cisco",
        "B4A4E3": "Cisco",
        "B8BE6E": "Cisco",
        "BC16F5": "Cisco",
        "C49DED": "Cisco",
        "C83A35": "Cisco",
        "CC161D": "Cisco",
        "D067E5": "Cisco",
        "D4A0F8": "Cisco",
        "D8B377": "Cisco",
        "E0F9B7": "Cisco",
        "E49AD0": "Cisco",
        "E84E84": "Cisco",
        "E8B748": "Cisco",
        "EC44A9": "Cisco",
        "ECCE13": "Cisco",
        "F07F06": "Cisco",
        "F0F61C": "Cisco",
        "F4CFE2": "Cisco",
        "F8DB7F": "Cisco",
        "FC5B39": "Cisco"
    }
    
    return oui_vendors.get(oui, f"Unknown-{oui}")


def extract_user_agent_from_packet(scapy_packet: Any) -> str:
    """Próba wyciągnięcia User-Agent z pakietu HTTP"""
    if not SCAPY_AVAILABLE or not scapy_packet:
        return ""
    
    try:
        if scapy_packet.haslayer(Raw):
            payload = bytes(scapy_packet[Raw])
            payload_str = payload.decode('utf-8', errors='ignore')
            
            # Szukaj User-Agent w nagłówkach HTTP
            lines = payload_str.split('\r\n')
            for line in lines:
                if line.lower().startswith('user-agent:'):
                    return line[11:].strip()  # Usuń "User-Agent: "
                    
    except Exception:
        pass
    return ""


def extract_device_info_from_packet(scapy_packet: Any, packet_info: PacketInfo) -> Optional[Dict[str, str]]:
    """Wyciąg informacji o urządzeniu z pakietu"""
    if not SCAPY_AVAILABLE:
        return None
    
    try:
        device_info = {
            "mac_address": get_mac_address_from_packet(scapy_packet) or "",
            "hostname": resolve_hostname(packet_info.src_ip),
            "user_agent": extract_user_agent_from_packet(scapy_packet),
        }
        
        if device_info["mac_address"]:
            device_info["oui_vendor"] = get_oui_vendor(device_info["mac_address"])
        else:
            device_info["oui_vendor"] = ""
            
        return device_info
    except Exception:
        return None


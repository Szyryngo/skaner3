APP_NAME = "AI Network Sniffer"
__version__ = "0.3.2"

# Eksport najważniejszych klas/funkcji z core dla wygodnych importów
from .ai_engine import AIEngine
from .utils import PacketInfo, LogWriter, make_fake_packet
from .network_scanner import NetworkScanner, ScanResult

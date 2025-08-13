# Network Scanner - Dokumentacja

## Przegląd

Network Scanner to nowy moduł w AI Network Sniffer umożliwiający profesjonalne skanowanie sieci. Składa się z dwóch głównych komponentów:

1. **`core/network_scanner.py`** - Silnik skanowania
2. **`ui/network_scanner_tab.py`** - Interfejs graficzny

## Funkcjonalności

### Core Features
- **Wykrywanie hostów**: Ping ICMP/TCP dla identyfikacji aktywnych urządzeń
- **Skanowanie portów**: TCP port scanning z konfigurowalnymi zakresami
- **Resolving hostów**: Opcjonalne rozwiązywanie nazw DNS
- **Asynchroniczne operacje**: Wielowątkowe skanowanie z callbackami
- **Tryby skanowania**: Light (podstawowe porty) i Hard (pełny zakres)
- **Obsługa zakresów**: CIDR, zakresy IP, pojedyncze adresy

### GUI Features
- **Konfiguracja zakresów**: Intuicyjne wprowadzanie celów skanowania
- **Presety portów**: Predefiniowane zestawy portów (Web, Mail, etc.)
- **Kontrola postępu**: Real-time monitoring z paskiem postępu
- **Wyniki na żywo**: Tabela z aktualizowanymi wynikami
- **Eksport danych**: Zapis wyników do CSV
- **Menu kontekstowe**: Kopiowanie danych, reskanowanie

## Użycie

### Core API

```python
from core.network_scanner import NetworkScanner, ScanMode

# Konfiguracja skanera
scanner = NetworkScanner(
    mode=ScanMode.LIGHT,
    timeout=2.0,
    max_threads=50
)

# Ustawienie callbacków
scanner.on_host_found = lambda host: print(f"Found: {host.ip}")
scanner.on_progress_update = lambda progress: print(f"Progress: {progress.hosts_scanned}")
scanner.on_scan_complete = lambda: print("Scan complete!")

# Rozpoczęcie skanowania
scanner.start_scan(
    ip_ranges=["192.168.1.0/24", "10.0.0.1-10.0.0.50"],
    ports=[22, 80, 443],
    resolve_hostnames=True
)

# Oczekiwanie na zakończenie
while scanner.is_running():
    time.sleep(0.1)

# Pobieranie wyników
results = scanner.get_results()
alive_hosts = scanner.get_alive_hosts()
```

### GUI Integration

Scanner jest dostępny jako zakładka "Scanner" w głównym oknie aplikacji. Automatycznie integruje się z systemem konfiguracji i nie blokuje interfejsu użytkownika.

## Architektura

### NetworkScanner Class

**Metody publiczne:**
- `start_scan(ip_ranges, ports, resolve_hostnames)` - Rozpoczyna skanowanie
- `stop_scan()` - Zatrzymuje skanowanie
- `is_running()` - Sprawdza stan skanowania
- `get_results()` - Zwraca wszystkie wyniki
- `get_alive_hosts()` - Zwraca aktywne hosty
- `get_hosts_with_open_ports()` - Zwraca hosty z otwartymi portami

**Callbacki:**
- `on_host_found(HostInfo)` - Wywołany przy znalezieniu hosta
- `on_progress_update(ScanProgress)` - Aktualizacja postępu
- `on_scan_complete()` - Zakończenie skanowania
- `on_error(str)` - Błąd podczas skanowania

### HostInfo Dataclass

```python
@dataclass
class HostInfo:
    ip: str
    hostname: Optional[str] = None
    is_alive: bool = False
    open_ports: List[int] = None
    response_time: Optional[float] = None
    last_seen: Optional[float] = None
```

### ScanProgress Dataclass

```python
@dataclass
class ScanProgress:
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
```

## Tryby skanowania

### Light Mode
- Szybki ping hostów
- Skanowanie podstawowych portów (21, 22, 23, 25, 53, 80, 110, 443, ...)
- Rekomendowany dla szybkich przeglądów sieci

### Hard Mode
- Dokładne skanowanie hostów
- Pełny zakres portów (1-1024)
- Dokładniejsze, ale czasochłonne

## Konfiguracja zakresów IP

### Obsługiwane formaty:

1. **Pojedynczy IP**: `192.168.1.1`
2. **Zakres IP**: `192.168.1.1-192.168.1.50`
3. **CIDR**: `192.168.1.0/24`
4. **Mieszane**: Kombinacja powyższych

### Przykłady:

```
192.168.1.0/24
10.0.0.1-10.0.0.100
172.16.1.10
203.0.113.5
```

## Presety portów

### Podstawowe
Porty: 21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 993, 995

### Web
Porty: 80, 443, 8080, 8443

### Mail
Porty: 25, 110, 143, 993, 995

### Custom
Możliwość definiowania własnych portów w formatach:
- Lista: `22,80,443`
- Zakres: `1-1000`
- Mieszane: `22,80,443,8000-9000`

## Eksport wyników

Wyniki można eksportować do pliku CSV zawierającego:
- IP Address
- Hostname
- Is Alive (Yes/No)
- Response Time (ms)
- Open Ports
- Last Seen (timestamp)

## Integracja z aplikacją

### main_window.py

Scanner jest zintegrowany jako `self.network_scanner` i dodany jako zakładka:

```python
self.network_scanner = NetworkScannerTab(self)
self.tabs.addTab(self.network_scanner, "Scanner")
```

### Współpraca z innymi modułami

Scanner jest niezależny od innych modułów aplikacji, ale można go rozszerzyć o:
- Integrację z AI engine dla analizy wyników
- Eksport do systemu alertów
- Zapisywanie do logów systemowych

## Testy

Kompletne testy jednostkowe w `tests/test_network_scanner.py` obejmują:
- Tworzenie i konfigurację skanera
- Parsowanie zakresów IP
- Symulację skanowania
- Obsługę callbacków
- Kontrolę start/stop

## Demo

Uruchom `demo_network_scanner.py` aby zobaczyć działanie skanera w trybie symulacji bez GUI.

## Bezpieczeństwo

- Scanner używa standardowych technik skanowania (TCP connect, ICMP ping)
- Nie wykonuje żadnych operacji potencjalnie szkodliwych
- Szanuje limity systemowe (timeout, liczba wątków)
- Może być wykryty przez systemy IDS/IPS jako skanowanie portów

## Wydajność

- Wielowątkowe operacje dla lepszej wydajności
- Konfigurowalne timeouty i liczba wątków
- Batch updates UI dla płynności interfejsu
- Możliwość zatrzymania skanowania w dowolnym momencie

## Rozszerzenia (przyszłe wersje)

- Skanowanie UDP
- Wykrywanie usług (service detection)
- Skanowanie stealth (SYN scan)
- Integracja z Nmap
- Import/export konfiguracji skanowania
- Scheduler dla regularnych skanów
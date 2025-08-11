# AI Network Sniffer (Python + Qt5)

Nowoczesny sniffer sieciowy z aktywną AI do monitorowania i ochrony sieci.

## Główne funkcje
- Przechwytywanie i analiza pakietów sieciowych w czasie rzeczywistym
- Wykrywanie zagrożeń i anomalii z użyciem AI/ML
- Intuicyjny interfejs GUI (Qt5)
- Automatyczne reakcje na wykryte zagrożenia
- Rozwijana architektura modułowa

## Jak uruchomić
1. Zainstaluj wymagane pakiety:
    ```
    pip install -r requirements.txt
    ```
2. Uruchom aplikację:
    ```
    python main.py
    ```

Domyślnie aplikacja startuje w trybie symulacji (bez scapy). Aby przechwytywać realny ruch:
- Zainstaluj Npcap/WinPcap i uruchom Python z uprawnieniami administratora (Windows),
- W menu Plik → Konfiguracja… odznacz „Tryb symulacji”, ustaw interfejs i ewentualny filtr BPF.

## Struktura katalogów
- `core/` — logika sniffera, AI, reguły
- `ui/` — komponenty GUI
- `main.py` — punkt startowy aplikacji
- `SESSION_NOTES.md` — notatki projektowe i struktura katalogów

## Dokumentacja
Szczegółowe założenia i postępy znajdziesz w pliku `SESSION_NOTES.md`.

## MVP (obecny stan)
- Okno główne z zakładkami „Pakiety” i „Alerty”,
- Kolejka pakietów zasilana przez `PacketSniffer` (scapy lub tryb symulacji),
- Prosty `AIEngine` z heurystyką oraz `RuleEngine` z regułami (np. porty zablokowane, duże pakiety).
 - Indeksowanie pakietów od najstarszych do najnowszych; wybór wiersza pokazuje hexdump, ASCII oraz geolokalizację IP.
  - Konfiguracja interfejsu: lista aktywnych interfejsów z czytelnymi etykietami (Wi‑Fi/Ethernet/Loopback/Virtual), z opcją pokazania nieaktywnych. Ikony/kolory typów, zapamiętywanie ostatniego interfejsu.

## Znane ograniczenia
- Zatrzymywanie sniffera scapy wymaga `AsyncSniffer` i uprawnień, w środowiskach bez scapy aplikacja automatycznie przełącza się na symulację,
- Heurystyka AI to placeholder – do wymiany na model ML.
 - Geolokalizacja korzysta z `ip-api.com` i wymaga dostępu do internetu; brak gwarancji dokładności.
 - Pokazywanie interfejsów wymaga `psutil`; jeśli brak, dropdown będzie pusty.
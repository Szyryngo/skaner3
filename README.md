# AI Network Sniffer (Python + Qt5)

Nowoczesny sniffer sieciowy z aktywną AI do monitorowania i ochrony sieci.

## Główne funkcje
- Przechwytywanie i analiza pakietów sieciowych w czasie rzeczywistym
- Wykrywanie zagrożeń i anomalii z użyciem AI/ML
- Intuicyjny interfejs GUI (Qt5)
- Automatyczne reakcje na wykryte zagrożenia
- Rozwijana architektura modułowa

## Co nowego (MVP+)
- Widok pakietów z filtrami (tekst/PROTOCOL), menu kontekstowym i szczegółami (hexdump, ASCII, geolokalizacja IP)
- Pasek narzędzi z szybkim dostępem (Start/Stop/Konfiguracja), skróty: F5, Shift+F5, Ctrl+,
- Monitor zasobów w prawym górnym rogu (CPU i RAM)
- Wydajność: batch update tabeli i limit 5000 wierszy (niższe obciążenie CPU/RAM)
- Konfiguracja interfejsu: lista aktywnych interfejsów z czytelnymi etykietami (Wi‑Fi/Ethernet/Loopback/Virtual/Cellular), opcja pokazania nieaktywnych; zapamiętywanie ostatniego wyboru
- AI: heurystyka + modele ML: IsolationForest (sklearn) oraz Half‑Space Trees (river, strumieniowo). Karta „AI” pokazuje status (ostatni score, reasons, decyzje, metryki stream)
- Próg i alerty: regulowany próg `combined_threshold`; przełącznik „tylko anomalie do alertów” (można wyciszyć alerty reguł)
- Eksport i logowanie: ręczny eksport (CSV/TXT) z menu oraz automatyczne logowanie pakietów i alertów z rotacją (konfigurowalne)

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

W prawym górnym rogu paska narzędzi widoczny jest wskaźnik CPU i RAM (`psutil`).

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
  - Konfiguracja interfejsu: lista aktywnych interfejsów z czytelnymi etykietami (Wi‑Fi/Ethernet/Loopback/Virtual/Cellular), z opcją pokazania nieaktywnych. Ikony/kolory typów, zapamiętywanie ostatniego interfejsu.
  - Karta „AI” z podglądem działania (status ML, ostatnie powody/anomalia), konfiguracja ML w oknie ustawień (włącz/wyłącz, contamination, refit interval).
  - Eksport pakietów (CSV) i alertów (TXT) z menu Plik.

## Znane ograniczenia
- Zatrzymywanie sniffera scapy wymaga `AsyncSniffer` i uprawnień, w środowiskach bez scapy aplikacja automatycznie przełącza się na symulację,
- Heurystyka AI to placeholder – do wymiany na model ML.
  - Geolokalizacja korzysta z `ip-api.com` i wymaga dostępu do internetu; brak gwarancji dokładności.
  - Lista interfejsów i monitor CPU/RAM wymagają `psutil`.
  - Modele ML: `scikit-learn` dla IsolationForest i `river` dla Half‑Space Trees; w razie braku bibliotek używana jest sama heurystyka.

## Konfiguracja (skrót)
- Plik → Konfiguracja…: wybór interfejsu (aktywny domyślnie), tryb symulacji, filtr BPF
- Sekcja AI: włącz/wyłącz IsolationForest; próg `combined_threshold`; model strumieniowy i próg Z
- Sekcja Alerty: „tylko anomalie” (wycisza alerty reguł)
- Sekcja Eksport: format CSV/TXT, rotacja co N wierszy, automatyczny zapis podczas przechwytywania

## Konfiguracja użytkownika
- Zapis/Wczytanie: Plik → „Zapisz konfigurację…” / „Wczytaj konfigurację…” (format JSON)
- Stan UI jest zachowywany (układ splitterów, aktywna zakładka, geometria okna)
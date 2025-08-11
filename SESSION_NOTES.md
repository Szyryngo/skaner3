# Notatki z sesji projektowej: AI Network Sniffer

**Data rozpoczęcia:** 2025-08-11

---

## Założenia projektu

- **Cel:** Aplikacja desktopowa do monitorowania ruchu sieciowego i wykrywania zagrożeń z użyciem AI.
- **Język:** Python 3.x
- **GUI:** Qt5 (PyQt5 lub PySide2)
- **Funkcje AI:** Wykrywanie anomalii i zagrożeń w czasie rzeczywistym, uczenie się na bieżąco.
- **Przechwytywanie pakietów:** scapy, pyshark lub pcapy.

## Struktura katalogów i plików (aktualizowana na bieżąco)

```
skaner3/
│
├── core/
│   ├── __init__.py
│   ├── packet_sniffer.py      # Przechwytywanie i dekodowanie pakietów
│   ├── ai_engine.py           # Silnik AI/ML wykrywający anomalie
│   ├── rules.py               # Reguły wykrywania i automatyczne reakcje
│   └── utils.py               # Narzędzia pomocnicze
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # Główne okno aplikacji
│   ├── packet_viewer.py       # Widok pakietów
│   ├── alert_viewer.py        # Widok alertów
│   └── config_dialog.py       # Okno konfiguracji
│
├── main.py                    # Punkt startowy aplikacji
├── requirements.txt           # Lista zależności
├── SESSION_NOTES.md           # Te notatki
└── README.md                  # Opis projektu
```

## Inspiracje

- Wireshark, Zeek, Suricata, AI NIDS (DeepNIDS)
- Najlepsze praktyki aplikacji desktopowych i bezpieczeństwa sieci

---

### Log zmian i postępu

- **2025-08-11:** Inicjalizacja repozytorium, utworzenie pierwszej wersji struktury katalogów i plików.
- **2025-08-11 (MVP):** Dodano działające szkielety:
  - `core/packet_sniffer.py` z trybem `AsyncSniffer` (scapy) i trybem symulacji,
  - `core/ai_engine.py` prosta heurystyka (duży pakiet, podejrzane porty),
  - `core/rules.py` podstawowe reguły (blokowane porty, duża długość),
  - `core/utils.py` konwersje pakietów i generator danych testowych,
  - `ui/main_window.py`, `ui/packet_viewer.py`, `ui/alert_viewer.py`, `ui/config_dialog.py` – GUI z zakładkami i konfiguracją,
  - `main.py` – start aplikacji z PyQt5.

- **2025-08-11 (UX + funkcje):**
  - `ui/packet_viewer.py`: filtry, wyszukiwarka, menu kontekstowe, dopasowanie kolumn,
  - `ui/alert_viewer.py`: kolorowanie alertów wg score,
  - `ui/main_window.py`: pasek narzędzi, skróty (F5/Shift+F5/Ctrl+,), licznik pakietów, batch update tabeli, limit 5000 wierszy, monitor CPU/RAM,
  - `core/utils.py`: geolokalizacja IP, hexdump/ASCII, lista interfejsów z kategoryzacją (Wi‑Fi/Ethernet/Cellular/Loopback/Virtual), `LogWriter` z rotacją,
  - `ui/config_dialog.py`: wybór aktywnych interfejsów, opcja pokazania nieaktywnych, ikony/kolory typów; sekcja AI (włącz/wyłącz ML, contamination, refit, próg combined, model strumieniowy i próg Z), sekcja alertów („tylko anomalie”), sekcja eksportu (format, rotacja, auto-zapis),
  - Zapamiętywanie ustawień w `QSettings` (interfejs, BPF, symulacja, AI – w tym stream i progi, alerty, eksport).
  - `ui/ai_status_viewer.py`: karta „AI” – status modelu (batch i stream) i ostatnie powody/score; `core/ai_engine.py` – IsolationForest + Half‑Space Trees + heurystyka, `get_status()`.


---

## TODO

- [x] Rozwinąć szkielet plików `core/` i `ui/`
- [x] Rozszerzyć `AIEngine` o model ML (IsolationForest) i trening inkrementalny (Half‑Space Trees)
- [x] Dodać sekcję AI w konfiguracji i kartę statusu AI
- [ ] Dodać zapisywanie i ładowanie konfiguracji użytkownika
- [x] Zapis/Wczytanie konfiguracji (JSON) + zachowanie układu UI (splitter, zakładki, geometria)
- [x] Zapisywanie ustawień w `QSettings`
- [ ] Dodać eksport/import logów pakietów i alertów
- [x] Eksport pakietów/alertów z GUI; rotacja plików w `LogWriter`
- [ ] Auto-eksport do wskazanego katalogu + selekcja docelowej ścieżki w GUI
- [ ] Testy jednostkowe dla utils/ai/rules
- [x] Testy podstawowe dla AIEngine i utils
- [ ] Ikony w zasobach i spójny theme (jasny/ciemny)
- [ ] Skróty klawiaturowe (Start/Stop/Focus filter)

# SESSION_NOTES.md - AI Network Sniffer

## Projekt: AI Network Sniffer v0.3.2

### Cel
Stworzenie inteligentnego sniffera sieciowego z AI do wykrywania anomalii i zagrożeń bezpieczeństwa.

### Architektura
- **core/**: Logika biznesowa (AI, sniffer, reguły, utils)
- **ui/**: Komponenty GUI (Qt5)
- **tests/**: Testy jednostkowe
- **main.py**: Punkt wejścia

## Postęp implementacji

### ✅ MVP (v0.1.0) - ZAKOŃCZONE
- [x] Podstawowa struktura projektu
- [x] `PacketSniffer` z scapy i trybem symulacji
- [x] `AIEngine` z heurystyką
- [x] `RuleEngine` z regułami bezpieczeństwa
- [x] `MainWindow` z zakładkami Pakiety/Alerty
- [x] `PacketViewer` z tabelą pakietów
- [x] `AlertViewer` z listą alertów
- [x] `ConfigDialog` z podstawowymi ustawieniami
- [x] Indeksowanie pakietów od najstarszego do najnowszego
- [x] Szczegółowy widok pakietów (hex, ASCII, geolokalizacja)

### ✅ UI/UX Enhancements (v0.1.0) - ZAKOŃCZONE
- [x] Filtry i wyszukiwanie pakietów
- [x] Menu kontekstowe dla pakietów
- [x] Toolbar z Start/Stop/Config
- [x] Monitor CPU/RAM w czasie rzeczywistym
- [x] Skróty klawiaturowe (F5, Shift+F5, Ctrl+,)
- [x] Czytelne interfejsy sieciowe (Wi-Fi, Ethernet, Loopback, Virtual, Cellular)
- [x] Ikony i kolory dla typów interfejsów
- [x] Zapamiętywanie ostatniego wybranego interfejsu

### ✅ AI/ML Integration (v0.2.0) - ZAKOŃCZONE
- [x] Integration IsolationForest (sklearn) do AIEngine
- [x] Integration Half-Space Trees (river) dla modelu strumieniowego
- [x] Konfigurowalne parametry ML (contamination, refit interval, stream threshold)
- [x] Przełącznik "tylko anomalie do alertów"
- [x] Konfigurowalny próg `combined_score`
- [x] AI Status Viewer z metrykami w czasie rzeczywistym
- [x] Fuzja wyników heurystyki + ML batch + ML streaming

### ✅ Export & Logging (v0.2.0) - ZAKOŃCZONE
- [x] Ręczny eksport pakietów (CSV) i alertów (TXT)
- [x] Automatyczne logowanie pakietów i alertów
- [x] Rotacja plików po określonej liczbie wierszy
- [x] `LogWriter` utility dla zarządzania plikami
- [x] Eksport/import konfiguracji (JSON)
- [x] Persystentne ustawienia UI (geometria, splittery, zakładki)

### ✅ Testing & CI/CD (v0.2.0) - ZAKOŃCZONE
- [x] Testy jednostkowe dla `AIEngine`
- [x] Testy jednostkowe dla `utils`
- [x] GitHub Actions workflow (pytest na Ubuntu/Windows)

### ✅ Advanced Export & Configuration (v0.3.0) - ZAKOŃCZONE
- [x] Osobne formaty eksportu dla pakietów i alertów (CSV/TXT)
- [x] Wybór katalogu docelowego dla auto-logowania i eksportów
- [x] Auto-czyszczenie starych plików po X dniach
- [x] Przycisk "Reset do domyślnych" w konfiguracji
- [x] Tytuł okna z wersją programu (v0.3.0)
- [x] Naprawione błędy spójności konfiguracji

### ✅ Enhanced UI/UX & Packet Visualization (v0.3.2) - ZAKOŃCZONE
- [x] Podgląd pakietów w alertach (hex dump, ASCII)
- [x] Zaawansowane kolorowanie pakietów według wagi zagrożenia AI
- [x] Kolorowanie wierszy w tabeli pakietów według score
- [x] Splitter w widoku alertów z listą i szczegółami
- [x] Lepsze wizualne rozróżnienie poziomów zagrożenia (czerwony/pomarańczowy/żółty/zielony)
- [x] Pogrubione czcionki dla wysokich zagrożeń

### ✅ Nowe funkcjonalności / zmiany (v0.3.x)
- [x] Dodano moduł `core/system_info.py` – zaawansowany zbieracz informacji o systemie operacyjnym, CPU, RAM i dysku (psutil).
- [x] Wydzielono pełny sniffer pakietów do `core/packet_sniffer.py` – obsługa trybu scapy i symulacji, zasilanie kolejki pakietów.
- [x] Rozbudowano `utils.py` o generację losowych pakietów do testów, formatowanie timestampów, konwersję z obiektów scapy.
- [x] Dodano komponent UI do wizualizacji sieci: `network_visualization.py` (tab "Wizualizacja" w main_window.py), przekazywanie bufora pakietów do wizualizacji.
- [x] W `config_dialog.py` – kolorowanie i emoji dla typów interfejsów sieciowych.
- [x] Przekazywanie bufora pakietów do AlertViewer i NetworkVisualization w main_window.
- [x] Szczegółowy widok geolokalizacji w main_window.
- [x] Usprawnienia w kolorowaniu poziomów alertów i pakietów w UI (kolorowanie wierszy/tła zależnie od score ML).
- [x] Nowe funkcje monitorowania zasobów systemowych (CPU/RAM/dysk) w GUI.

## Aktualny stan

### Wersja: 0.3.2
- **Nazwa**: AI Network Sniffer
- **Status**: Stabilna wersja z pełną funkcjonalnością, naprawionymi błędami i nowymi funkcjami UI
- **Wszystkie główne funkcje**: Zaimplementowane
- **Wszystkie błędy**: Naprawione i przetestowane
- **Nowe funkcje**: Podgląd pakietów w alertach, zaawansowane kolorowanie

### Pliki zaimplementowane
- ✅ `core/__init__.py` - nazwa i wersja aplikacji
- ✅ `core/ai_engine.py` - silnik AI z ML (IsolationForest + Half-Space Trees)
- ✅ `core/packet_sniffer.py` - przechwytywanie pakietów (scapy/symulacja)
- ✅ `core/system_info.py` - monitorowanie zasobów systemowych
- ✅ `core/rules.py` - reguły bezpieczeństwa
- ✅ `core/utils.py` - narzędzia pomocnicze, geolokalizacja, LogWriter
- ✅ `ui/main_window.py` - główne okno aplikacji
- ✅ `ui/packet_viewer.py` - widok pakietów z filtrami
- ✅ `ui/alert_viewer.py` - widok alertów
- ✅ `ui/config_dialog.py` - dialog konfiguracji
- ✅ `ui/ai_status_viewer.py` - status AI
- ✅ `ui/network_visualization.py` - wizualizacja ruchu sieciowego
- ✅ `main.py` - punkt wejścia
- ✅ `tests/test_ai_engine.py` - testy AIEngine
- ✅ `tests/test_utils.py` - testy utils
- ✅ `.github/workflows/ci.yml` - GitHub Actions CI/CD

## Optymalizacje wydajności

### CPU/RAM
- ✅ Batch updates UI (200 pakietów na tick)
- ✅ Limit wierszy tabeli (5000)
- ✅ Timer 1s dla metryk systemowych
- ✅ `n_jobs=1` w IsolationForest
- ✅ Bufor ML ograniczony do 4000 próbek
- ✅ Refit modelu co 500 próbek

### Buforowanie
- ✅ Indeksowanie pakietów od najstarszego
- ✅ Auto-rotacja logów
- ✅ Auto-czyszczenie starych plików
- ✅ Persystentne ustawienia UI

## Następne kroki (opcjonalne)

### Możliwe rozszerzenia
- [ ] Dodanie więcej modeli ML (LSTM, Autoencoder)
- [ ] Wizualizacja ruchu sieciowego (wykresy, mapy)
- [ ] Integracja z systemami SIEM
- [ ] Alerty w czasie rzeczywistym (notifications)
- [ ] Wsparcie dla protokołów specyficznych (HTTP, DNS, DHCP)
- [ ] Dashboard z metrykami sieciowymi
- [ ] Wsparcie dla wielu interfejsów jednocześnie
- [ ] Backup i restore konfiguracji
- [ ] Logi systemowe (syslog, Windows Event Log)
- [ ] Wsparcie dla kontenerów (Docker)

### Dokumentacja
- [x] README.md zaktualizowany do v0.3.0
- [x] SESSION_NOTES.md zaktualizowany
- [x] Historia zmian w README
- [x] BUGS_AND_FIXES.md - dokumentacja błędów i rozwiązań
- [ ] Dokumentacja API
- [ ] Przewodnik użytkownika
- [ ] Przewodnik dewelopera

## Uwagi techniczne

### Zależności
- **Wymagane**: PyQt5, numpy, psutil, requests
- **Opcjonalne**: scapy, scikit-learn, river
- **Testy**: pytest, pytest-cov

### Kompatybilność
- **Python**: 3.8+
- **OS**: Windows, Linux, macOS
- **GUI**: Qt5 (PyQt5/PySide2)

### Wydajność
- **Pakietów/sekundę**: ~1000-5000 (zależnie od sprzętu)
- **Pamięć**: ~50-200MB (zależnie od buforów)
- **CPU**: 5-20% (zależnie od aktywności sieci)
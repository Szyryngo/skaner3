# skaner3

## Opis projektu

Skaner3 to zaawansowana aplikacja do analizy ruchu sieciowego z wykorzystaniem sztucznej inteligencji. Aplikacja oferuje możliwość przechwytywania pakietów sieciowych w czasie rzeczywistym, ich analizy pod kątem anomalii oraz monitorowania stanu systemu.

### Główne funkcje

- **Przechwytywanie pakietów sieciowych** - w czasie rzeczywistym lub symulacja
- **Wykrywanie anomalii AI** - wykorzystuje algorytmy uczenia maszynowego (Isolation Forest, Half-Space Trees)
- **System alertów** - automatyczne powiadomienia o wykrytych anomaliach
- **Diagnostyka systemu** - monitorowanie zasobów systemowych i wydajności
- **Historia decyzji AI** - śledzenie i analiza działań systemu AI
- **Eksport danych** - możliwość eksportu pakietów, alertów i konfiguracji

## Struktura projektu

```
skaner3/
├── main.py                    # Punkt startowy aplikacji
├── requirements.txt           # Zależności Python
├── README.md                 # Dokumentacja projektu
├── core/                     # Moduły podstawowe
│   ├── __init__.py
│   ├── ai_engine.py          # Silnik wykrywania anomalii AI
│   ├── diagnostics_history.py # Historia diagnostyki i decyzji AI
│   ├── packet_sniffer.py     # Przechwytywanie pakietów
│   ├── rules.py              # Silnik reguł
│   ├── system_info.py        # Informacje o systemie
│   └── utils.py              # Narzędzia pomocnicze
├── ui/                       # Interfejs użytkownika
│   ├── __init__.py
│   ├── main_window.py        # Główne okno aplikacji
│   ├── packet_viewer.py      # Widok pakietów
│   ├── alert_viewer.py       # Widok alertów
│   ├── ai_status_viewer.py   # Status AI
│   ├── config_dialog.py      # Dialog konfiguracji
│   └── system_diagnostics_tab.py # Diagnostyka systemu i optymalizacja AI
└── tests/                    # Testy jednostkowe
    ├── test_ai_engine.py
    └── test_utils.py
```

## Nowa funkcjonalność: Diagnostyka systemu i optymalizacja AI

Aplikacja została rozszerzona o zaawansowaną zakładkę diagnostyki systemu, która oferuje:

### Monitorowanie systemu w czasie rzeczywistym
- **Metryki zasobów**: CPU, RAM, dysk, sieć
- **Informacje o procesach**: Top procesy według wykorzystania CPU/pamięci
- **Uptime systemu**: Czas działania i statystyki sieciowe
- **Interfejsy sieciowe**: Status i konfiguracja połączeń

### Analiza działania AI
- **Status silnika AI**: Aktualny stan, konfiguracja, gotowość modelu
- **Historia decyzji**: Szczegółowy log decyzji AI z możliwością filtrowania
- **Statystyki anomalii**: Współczynniki wykrycia, rozkład w czasie
- **Optymalizacja**: Monitorowanie wydajności algorytmów ML

### Zarządzanie historią
- **Automatyczny zapis**: Wszystkie decyzje AI są zapisywane lokalnie
- **Filtrowanie czasowe**: Analiza danych z różnych okresów
- **Statystyki podsumowujące**: Raporty wydajności i wykrycia
- **Zarządzanie przestrzenią**: Automatyczne czyszczenie starych danych

## Instrukcja uruchomienia

### Wymagania systemowe
- Python 3.8+
- System operacyjny: Linux, Windows, macOS
- Biblioteki: PyQt5, scapy, numpy, scikit-learn, psutil, river

### Instalacja

1. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/Szyryngo/skaner3.git
   cd skaner3
   ```

2. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```

3. Uruchom aplikację:
   ```bash
   python main.py
   ```

### Konfiguracja

Aplikacja automatycznie zapisuje konfigurację w systemie. Główne ustawienia:

- **Przechwytywanie**: Interfejs sieciowy, filtry BPF, tryb symulacji
- **AI**: Włączenie ML, progi anomalii, parametry algorytmów
- **Eksport**: Formaty plików, automatyczny zapis, rotacja logów
- **Diagnostyka**: Okres przechowywania historii, częstotliwość próbkowania

## Zakładki aplikacji

1. **Pakiety** - Podgląd przechwyconych pakietów w czasie rzeczywistym
2. **Alerty** - Lista wykrytych anomalii i alertów
3. **AI** - Status silnika sztucznej inteligencji
4. **Diagnostyka systemu i optymalizacja AI** - Nowa zakładka z:
   - Metrykami systemowymi w czasie rzeczywistym
   - Historią decyzji AI
   - Statystykami wydajności
   - Narzędziami optymalizacji

## Wykonane prace

- Scalono pull request #2, w którym wprowadzono następujące zmiany:
  - Dodano nową zakładkę "Diagnostyka systemu i optymalizacja AI"
  - Implementowano moduł `diagnostics_history.py` do zarządzania historią
  - Rozszerzono `ai_engine.py` o śledzenie decyzji AI
  - Uzupełniono `system_info.py` o zaawansowane funkcje diagnostyczne
  - Zaktualizowano interfejs użytkownika o nową funkcjonalność
- Zaktualizowano strukturę repozytorium po scaleniu gałęzi.

## Testowanie

Uruchom testy jednostkowe:
```bash
python -m unittest discover tests/ -v
```

Przetestuj komponenty:
```bash
python test_components.py
```

## Historia zmian

### Najnowsza wersja
- ✅ Dodano zakładkę diagnostyki systemu
- ✅ Implementowano historię decyzji AI
- ✅ Rozszerzono monitorowanie zasobów systemowych
- ✅ Dodano statystyki i analizy wydajności
- ✅ Ulepszono dokumentację projektu

## Kontakt

Autor: Szyryngo

---

Ten plik README został zaktualizowany po dodaniu funkcjonalności diagnostyki systemu i optymalizacji AI.
# Skaner3 - Inteligentny Analizator Ruchu Sieciowego

## Opis projektu

Projekt służy do analizy ruchu sieciowego z wykorzystaniem sztucznej inteligencji. Zawiera zaawansowane narzędzia do wykrywania anomalii oraz automatycznego dostosowania parametrów aplikacji do środowiska uruchomieniowego.

## 🔧 Nowa funkcjonalność: Automatyczne dostosowanie parametrów

Aplikacja została wzbogacona o inteligentny system adaptacyjny, który automatycznie analizuje środowisko uruchomieniowe i sugeruje optymalne parametry konfiguracyjne.

### Funkcje systemu adaptacyjnego:

- **Analiza systemu operacyjnego**: Wykrywanie typu OS, wersji oraz architektury
- **Analiza zasobów sprzętowych**: Monitorowanie CPU, RAM i dysku przy użyciu biblioteki `psutil`
- **Inteligentne dostosowanie parametrów**: AI analizuje zasoby i proponuje optymalne ustawienia:
  - Liczba wątków roboczych
  - Wielkość buforów pamięciowych
  - Maksymalny rozmiar logów
  - Rozmiar paczek przetwarzania
  - Interwał odświeżania interfejsu

### Komponenty systemu:

1. **`core/system_info.py`** - Moduł zbierający szczegółowe informacje o systemie
2. **`core/adaptive_engine.py`** - Silnik AI analizujący dane i generujący rekomendacje
3. **Rozszerzone `main.py`** - Demonstracja funkcjonalności z interfejsem linii poleceń

## Wymagania

### Zależności Python:
```
PyQt5           # Interfejs graficzny
scapy           # Analiza pakietów sieciowych
numpy           # Obliczenia numeryczne
scikit-learn    # Uczenie maszynowe
requests        # Komunikacja HTTP
psutil          # Informacje o systemie
river           # Uczenie maszynowe strumieniowe
```

### Wymagania systemowe:
- Python 3.8+
- Uprawnienia administratora (dla przechwytywania pakietów)
- Linux/Windows/macOS

## Instrukcja uruchomienia

### 1. Instalacja zależności:
```bash
git clone https://github.com/Szyryngo/skaner3.git
cd skaner3
pip install -r requirements.txt
```

### 2. Tryby uruchomienia:

#### Aplikacja GUI (domyślny):
```bash
python main.py
```

#### Demonstracja systemu adaptacyjnego:
```bash
python main.py --demo
```

#### Informacje o systemie:
```bash
python main.py --system-info
```

#### Wyniki w formacie JSON:
```bash
python main.py --demo --json
python main.py --system-info --json
```

### 3. Przykładowy rezultat działania:

```
======================================================================
🔧 AUTOMATYCZNE DOSTOSOWANIE PARAMETRÓW APLIKACJI
======================================================================

📊 ANALIZA SYSTEMU OPERACYJNEGO:
----------------------------------------
System operacyjny: Linux
Wersja systemu: Ubuntu 24.04.1

🖥️ PROCESOR:
   Rdzenie fizyczne: 4
   Wątki logiczne: 8
   Częstotliwość: 3200.0 MHz

💾 PAMIĘĆ RAM:
   Całkowita: 16.0 GB
   Dostępna: 12.8 GB
   Wykorzystanie: 20.0%

💿 DYSK TWARDY:
   Całkowita pojemność: 512.0 GB
   Wolne miejsce: 256.0 GB
   Wykorzystanie: 50.0%

🤖 ANALIZA AI I SUGEROWANE PARAMETRY:
----------------------------------------

📈 TRYB NORMALNY (zrównoważony):
   Optymalna liczba wątków: 6
   Rozmiar bufora głównego: 512 MB
   Rozmiar bufora pakietów: 768 MB
   Maksymalny rozmiar logów: 512 MB
   Rozmiar paczki przetwarzania: 1000 pakietów
   Interwał odświeżania UI: 250 ms
   Profil wydajnościowy: high_performance

💡 REKOMENDACJE AI:
----------------------------------------

🔸 THREADS:
   Wykryto 8 wątków CPU, ale sugeruję 6 dla stabilności i zostawienia 
   zasobów dla systemu.

🔸 MEMORY:
   Dostępne 12.8 GB RAM. Bufor 512 MB (3.9% dostępnej pamięci) zapewni 
   optymalną wydajność bez wpływu na stabilność systemu.

🔸 STORAGE:
   Dostępne 256.0 GB na dysku. Maksymalny rozmiar logów 512 MB (0.2% 
   wolnego miejsca) pozwoli na długoterminowe działanie bez wypełnienia dysku.

🔸 GENERAL:
   System ma wysoką wydajność. Możesz używać agresywnych ustawień dla 
   maksymalnej przepustowości.
```

## Profile wydajnościowe

System automatycznie rozpoznaje trzy profile wydajnościowe:

### 🚀 High Performance
- **Kryteria**: ≥8 wątków CPU + ≥16 GB RAM
- **Charakterystyka**: Agresywne wykorzystanie zasobów
- **Parametry**: Duże bufory, szybkie odświeżanie UI

### ⚖️ Balanced  
- **Kryteria**: ≥4 wątki CPU + ≥8 GB RAM
- **Charakterystyka**: Zrównoważone wykorzystanie zasobów
- **Parametry**: Średnie bufory, umiarkowane odświeżanie

### 🛡️ Low Resource
- **Kryteria**: <4 wątki CPU lub <8 GB RAM
- **Charakterystyka**: Oszczędne wykorzystanie zasobów
- **Parametry**: Małe bufory, wolne odświeżanie

## Tryby działania silnika adaptacyjnego

### Tryb normalny (domyślny):
- Wykorzystuje 10-15% dostępnej pamięci dla buforów
- Używa liczbę wątków = min(logiczne wątki, 1.5 × fizyczne rdzenie)
- Przeznacza 1-2% wolnego miejsca na dysku dla logów

### Tryb zachowawczy:
```python
from core.adaptive_engine import AdaptiveEngine

engine = AdaptiveEngine(conservative_mode=True)
results = engine.analyze_system()
```
- Wykorzystuje maksymalnie 5% dostępnej pamięci
- Używa 75% dostępnych rdzeni CPU
- Ogranicza logi do 1% wolnego miejsca

## API silnika adaptacyjnego

### Podstawowe użycie:
```python
from core.adaptive_engine import AdaptiveEngine

# Inicjalizacja silnika
engine = AdaptiveEngine()

# Analiza systemu
results = engine.analyze_system()

# Dostęp do wyników
optimal_threads = results['optimal_threads']
buffer_size = results['buffer_size_mb']
recommendations = results['recommendations']
```

### Konfiguracja zaawansowana:
```python
engine = AdaptiveEngine(
    conservative_mode=True,      # Tryb zachowawczy
    min_threads=2,               # Minimum 2 wątki
    max_threads=16,              # Maksimum 16 wątków
    min_buffer_mb=10,            # Minimum 10 MB bufora
    max_buffer_mb=1024,          # Maksimum 1 GB bufora
    min_log_mb=50,               # Minimum 50 MB logów
    max_log_mb=2048              # Maksimum 2 GB logów
)
```

## Testowanie

Uruchomienie testów jednostkowych:
```bash
# Wszystkie testy
python -m unittest discover -s tests -v

# Tylko testy systemu adaptacyjnego
python -m unittest tests.test_adaptive_engine -v

# Tylko testy utils
python -m unittest tests.test_utils -v
```

## Wykonane prace

- ✅ Scalono pull request #2, wprowadzając podstawową funkcjonalność analizy pakietów
- ✅ Dodano moduł `core/system_info.py` z integracją psutil
- ✅ Utworzono inteligentny silnik adaptacyjny `core/adaptive_engine.py`
- ✅ Rozszerzono `main.py` o demonstrację funkcjonalności
- ✅ Dodano pełną dokumentację i komentarze w kodzie
- ✅ Utworzono kompleksowe testy jednostkowe
- ✅ Zaktualizowano README.md z instrukcjami użytkowania

## Struktura projektu

```
skaner3/
├── core/
│   ├── __init__.py
│   ├── system_info.py          # Zbieranie informacji o systemie
│   ├── adaptive_engine.py      # Silnik adaptacyjny AI
│   ├── ai_engine.py           # Wykrywanie anomalii sieciowych
│   ├── packet_sniffer.py      # Przechwytywanie pakietów
│   ├── rules.py               # Reguły analizy
│   └── utils.py               # Narzędzia pomocnicze
├── ui/                        # Interfejs graficzny
├── tests/                     # Testy jednostkowe
├── main.py                    # Punkt startowy aplikacji
├── requirements.txt           # Zależności Python
└── README.md                  # Dokumentacja
```

## Kontakt

**Autor**: Szyryngo  
**Repository**: https://github.com/Szyryngo/skaner3

---

*Ten projekt wykorzystuje sztuczną inteligencję do automatycznego dostosowania parametrów aplikacji oraz wykrywania anomalii w ruchu sieciowym.*
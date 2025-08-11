# BUGS_AND_FIXES.md - Dokumentacja błędów i rozwiązań

## AI Network Sniffer v0.3.1

### Cel dokumentu
Ten plik zawiera dokumentację wszystkich znalezionych błędów, ich przyczyn, rozwiązań i lekcji na przyszłość.

---

## 🐛 Błędy krytyczne (blokujące uruchomienie)

### 1. AttributeError: 'MainWindow' object has no attribute 'resource_label'

**Data wykrycia:** 2025-01-27  
**Wersja:** v0.3.0  
**Status:** ✅ NAPRAWIONE  

#### Opis błędu
```
Traceback (most recent call last):
  File "C:\tmp\main.py", line 18, in <module>
    sys.exit(main())
  File "C:\tmp\main.py", line 12, in main
    window = MainWindow()
  File "ui\main_window.py", line 94, in __init__
    self._create_actions()
  File "ui\main_window.py", line 203, in _create_actions
    toolbar.addWidget(self.resource_label)
AttributeError: 'MainWindow' object has no attribute 'resource_label'
```

#### Przyczyna
**Błąd w kolejności inicjalizacji** - metoda `_create_actions()` była wywoływana przed utworzeniem `self.resource_label`, ale próbowała go użyć w toolbar.

#### Lokalizacja
- **Plik:** `ui/main_window.py`
- **Linia:** 203 w `_create_actions()`
- **Metoda:** `MainWindow.__init__()`

#### Rozwiązanie
**Przeniesienie tworzenia `resource_label` przed `_create_actions()`:**

```python
# PRZED (błędna kolejność):
def __init__(self) -> None:
    # ... inne inicjalizacje ...
    self._create_actions()  # ❌ Próbuje użyć resource_label
    # ... później ...
    self.resource_label = QLabel("CPU: --%  RAM: --%", self)  # ❌ Za późno

# PO (poprawna kolejność):
def __init__(self) -> None:
    # ... inne inicjalizacje ...
    # Timer do metryk systemowych (CPU/RAM)
    self.resource_label = QLabel("CPU: --%  RAM: --%", self)  # ✅ Najpierw tworzenie
    self.resource_timer = QTimer(self)
    self.resource_timer.setInterval(1000)
    self.resource_timer.timeout.connect(self._update_resource_label)
    self.resource_timer.start()
    
    # ... konfiguracja ...
    
    self._create_actions()  # ✅ Teraz resource_label istnieje
```

#### Commit
```
fix(ui): resolve AttributeError - move resource_label creation before _create_actions()
```

#### Lekcja na przyszłość
- **Zawsze sprawdzaj kolejność inicjalizacji** w `__init__`
- **Używaj atrybutów dopiero po ich utworzeniu**
- **Rozważ grupowanie powiązanych inicjalizacji** w osobnych metodach

---

## 🔧 Błędy spójności konfiguracji

### 2. Niespójność pól konfiguracji export

**Data wykrycia:** 2025-01-27  
**Wersja:** v0.3.0  
**Status:** ✅ NAPRAWIONE  

#### Opis problemu
W `ui/main_window.py` struktura `cfg_export` miała tylko 4 pola, ale w `ui/config_dialog.py` było 7 pól. Brakujące pola:
- `format_packets`
- `format_alerts` 
- `cleanup_days`

#### Przyczyna
**Niedokończona implementacja** - nowe pola zostały dodane w UI, ale nie w logice aplikacji.

#### Rozwiązanie
**Dodanie brakujących pól w `MainWindow`:**

```python
# PRZED (niepełna konfiguracja):
self.cfg_export: dict = {
    "format": str(settings.value("export/format", "csv")),
    "rotate_rows": int(settings.value("export/rotate_rows", 100000)),
    "auto": bool(settings.value("export/auto", False)),
    "dir": str(settings.value("export/dir", "")),
}

# PO (pełna konfiguracja):
self.cfg_export: dict = {
    "format": str(settings.value("export/format", "csv")),
    "format_packets": str(settings.value("export/format_packets", "")),
    "format_alerts": str(settings.value("export/format_alerts", "")),
    "rotate_rows": int(settings.value("export/rotate_rows", 100000)),
    "auto": bool(settings.value("export/auto", False)),
    "dir": str(settings.value("export/dir", "")),
    "cleanup_days": int(settings.value("export/cleanup_days", 0)),
}
```

#### Commit
```
feat(export): separate formats for packets/alerts, target dir and auto-cleanup; ui: show app version; bump version to 0.3.0
```

---

## 🐍 Błędy składni Python

### 3. Nieprawidłowe użycie walrus operator w comprehension

**Data wykrycia:** 2025-01-27  
**Wersja:** v0.3.0  
**Status:** ✅ NAPRAWIONE  

#### Opis błędu
```python
# BŁĘDNY kod w export_packets():
row = [
    row_value
    for row_value in [
        *([row := packetinfo_to_row(p)] and [
            row["time"], row["src_ip"], row["dst_ip"], 
            row["src_port"], row["dst_port"], row["protocol"], row["length"]
        ])
    ]
]
```

#### Przyczyna
**Walrus operator (`:=`) nie może być używany w comprehension iterable expression** - to ograniczenie składni Python.

#### Rozwiązanie
**Uproszczenie logiki bez walrus operator:**

```python
# PO (poprawny kod):
for p in self._packets_buffer:
    row = packetinfo_to_row(p)
    writer.writerow([
        row["time"], row["src_ip"], row["dst_ip"], 
        row["src_port"], row["dst_port"], row["protocol"], row["length"]
    ])
```

#### Commit
```
fix(core): resolve AIEngine decision variable error and missing imports; fix(ui): resolve config inconsistencies and syntax errors; docs: update README and SESSION_NOTES to v0.3.0
```

---

## 🔌 Błędy importów i zależności

### 4. Brakujący import `deque` w AIEngine

**Data wykrycia:** 2025-01-27  
**Wersja:** v0.3.0  
**Status:** ✅ NAPRAWIONE  

#### Opis problemu
W `core/ai_engine.py` brakowało importu `from collections import deque`, mimo że kod był przygotowany na jego użycie.

#### Rozwiązanie
**Dodanie brakującego importu:**

```python
from __future__ import annotations
from typing import Dict, List, Optional
from collections import deque  # ✅ Dodane

import numpy as np
# ... reszta importów
```

### 5. Błąd z niezdefiniowaną zmienną `decision` w AIEngine

**Data wykrycia:** 2025-01-27  
**Wersja:** v0.3.0  
**Status:** ✅ NAPRAWIONE  

#### Opis błędu
```python
# BŁĘDNY kod:
try:
    self._last_ml_decision = float(decision)  # ❌ decision może nie istnieć
except Exception:
    self._last_ml_decision = None
```

#### Przyczyna
**Zmienna `decision` była definiowana tylko w bloku `if self.ml_enabled`**, ale używana poza nim.

#### Rozwiązanie
**Inicjalizacja zmiennej `decision` na początku metody:**

```python
def analyze_packet(self, packet: PacketInfo) -> Dict[str, object]:
    # ... heurystyka ...
    
    # ML batch (IsolationForest)
    ml_score = None
    is_ml_anomaly = False
    decision = None  # ✅ Inicjalizacja zmiennej
    
    if self.ml_enabled:
        # ... logika ML ...
        if self._model is not None:
            try:
                decision = float(self._model.decision_function(feat.reshape(1, -1))[0])
                # ... reszta logiki ...
            except Exception:
                self._model = None
    
    # ... reszta metody ...
    
    try:
        self._last_ml_decision = float(decision) if decision is not None else None
    except Exception:
        self._last_ml_decision = None
```

---

## 📋 Lista sprawdzania przed commitem

### Sprawdź kolejność inicjalizacji
- [ ] Wszystkie atrybuty są tworzone przed ich użyciem
- [ ] Metody `_create_*()` są wywoływane po utworzeniu potrzebnych atrybutów
- [ ] Timery i sygnały są konfigurowane po utworzeniu widgetów

### Sprawdź spójność konfiguracji
- [ ] Wszystkie pola z UI są obecne w logice aplikacji
- [ ] QSettings zapisuje i odczytuje te same klucze
- [ ] Import/export konfiguracji obsługuje wszystkie pola

### Sprawdź składnię Python
- [ ] Walrus operator nie jest używany w comprehension
- [ ] Wszystkie zmienne są inicjalizowane przed użyciem
- [ ] Try-except bloki obsługują wszystkie przypadki

### Sprawdź importy
- [ ] Wszystkie używane moduły są zaimportowane
- [ ] Importy są na górze pliku
- [ ] Nie ma nieużywanych importów

---

## 🚀 Prewencja błędów

### 1. Testy jednostkowe
- Uruchamiaj `pytest tests/` przed commitem
- Dodawaj testy dla nowych funkcji
- Testuj edge cases (puste dane, błędy)

### 2. Linting
- Używaj `python -m py_compile <plik>` do sprawdzenia składni
- Rozważ dodanie `flake8` lub `pylint`
- Sprawdzaj typy z `mypy` (opcjonalnie)

### 3. Code Review
- Sprawdzaj kolejność inicjalizacji w `__init__`
- Weryfikuj spójność między UI a logiką
- Testuj różne scenariusze konfiguracji

### 4. Dokumentacja
- Aktualizuj `SESSION_NOTES.md` po każdej zmianie
- Dokumentuj znalezione błędy w tym pliku
- Dodawaj komentarze do skomplikowanej logiki

---

## 📊 Statystyki błędów

| Typ błędu | Liczba | Status |
|-----------|--------|---------|
| AttributeError | 1 | ✅ NAPRAWIONE |
| Niespójność konfiguracji | 1 | ✅ NAPRAWIONE |
| Błąd składni Python | 1 | ✅ NAPRAWIONE |
| Brakujące importy | 2 | ✅ NAPRAWIONE |
| **RAZEM** | **5** | **100% NAPRAWIONE** |

---

## 🔗 Powiązane pliki

- `ui/main_window.py` - główne okno aplikacji
- `ui/config_dialog.py` - dialog konfiguracji
- `core/ai_engine.py` - silnik AI/ML
- `core/__init__.py` - nazwa i wersja aplikacji
- `README.md` - dokumentacja użytkownika
- `SESSION_NOTES.md` - notatki projektowe

---

**Ostatnia aktualizacja:** 2025-01-27  
**Wersja dokumentu:** 1.1  
**Autor:** AI Assistant  
**Status:** ✅ Wszystkie błędy naprawione, wersja 0.3.1

# AI Network Sniffer

## Opis projektu
AI Network Sniffer to inteligentny sniffer sieciowy z wbudowanym silnikiem AI do wykrywania anomalii i zagrożeń bezpieczeństwa w ruchu sieciowym. Umożliwia analizę pakietów w czasie rzeczywistym, wykrywanie podejrzanych zdarzeń, eksport danych i konfigurację parametrów systemu oraz AI.

## Funkcjonalności
- Analiza ruchu sieciowego na żywo (tryb rzeczywisty i symulacyjny)
- Wykrywanie anomalii: heurystyki, IsolationForest (sklearn), Half-Space Trees (river)
- System reguł bezpieczeństwa (RuleEngine)
- Eksport pakietów i alertów do plików
- Automatyczne logowanie i rotacja plików
- Wielozakładkowy interfejs graficzny (PyQt5)
- Podgląd statusu AI/modelu, monitor zasobów systemowych
- Zaawansowane kolorowanie i filtracja alertów

## Wymagania
- Python 3.10+ (zalecany 3.13)
- PyQt5
- scapy (opcjonalnie, do trybu rzeczywistego)
- scikit-learn (opcjonalnie, IsolationForest)
- river (opcjonalnie, Half-Space Trees)
- psutil (monitorowanie zasobów)

## Instalacja
```bash
pip install -r requirements.txt
```
lub ręcznie:
```bash
pip install PyQt5 scapy scikit-learn river psutil
```

## Uruchomienie
```bash
python main.py
```

## Struktura katalogów
Patrz: [STRUKTURA_PROJEKTU.md](STRUKTURA_PROJEKTU.md)

## Dokumentacja techniczna
- [BUGS_AND_FIXES.md](BUGS_AND_FIXES.md) – lista błędów i poprawek
- [SESSION_NOTES.md](SESSION_NOTES.md) – dziennik postępu i roadmapa
- [STRUKTURA_PROJEKTU.md](STRUKTURA_PROJEKTU.md) – opis architektury
- [STRUKTURA_KATALOGÓW.md](STRUKTURA_KATALOGÓW.md) – szczegółowy opis katalogów

## Jak się przyczynić?
- Forkuj repozytorium i utwórz Pull Request
- Przed commitem uruchom testy jednostkowe: `pytest tests/`
- Stosuj checklistę jakości z [BUGS_AND_FIXES.md](BUGS_AND_FIXES.md)
- Opisuj zmiany w [SESSION_NOTES.md](SESSION_NOTES.md)

## Autorzy
- Szyryngo (main dev)

## Licencja

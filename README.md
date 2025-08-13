# AI Network Sniffer

## Opis projektu
AI Network Sniffer to inteligentny sniffer sieciowy z wbudowanym silnikiem AI do wykrywania anomalii i zagrożeń bezpieczeństwa w ruchu sieciowym. Umożliwia analizę pakietów w czasie rzeczywistym lub w trybie symulacji, łącząc heurystyki, uczenie maszynowe oraz system reguł.

## Funkcjonalności
- Analiza ruchu sieciowego na żywo (tryb rzeczywisty i symulacyjny)
- Wykrywanie anomalii w ruchu sieciowym:
  - Heurystyki (proste reguły)
  - IsolationForest (scikit-learn)
  - Half-Space Trees (river) – detekcja online
  - Fuzja heurystyk i ML
- System reguł bezpieczeństwa (RuleEngine)
- Eksport pakietów oraz alertów do plików (z automatyczną rotacją)
- Wielozakładkowy interfejs graficzny (PyQt5):
  - Podgląd i filtrowanie pakietów sieciowych
  - Szczegóły pakietów (hex/ascii/geolokalizacja)
  - Widok alertów bezpieczeństwa
  - Wizualizacja statystyk sieciowych (ruch, protokoły, itp.)
  - **Zakładka „Status systemu”** – prezentacja na żywo:
    - Lista interfejsów sieciowych (nazwa, status, typ, adres IPv4)
    - Liczba uruchomionych wątków
    - Wykorzystanie CPU, RAM
    - Uptime systemu
- Zaawansowane kolorowanie i filtrowanie alertów
- Monitorowanie zasobów systemowych (psutil)
- Konfigurowalność AI oraz reguł przez GUI
- Geolokalizacja adresów IP
- Testy jednostkowe

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
olę ręcznie:
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

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

## Dodatkowe funkcjonalności

- **Zaawansowany skaner sieci:**  
  - Wbudowana zakładka "Skaner sieci" w GUI umożliwia szybkie skanowanie hostów i portów w sieci lokalnej.
  - Obsługa dwóch trybów skanowania: lekki (ARP/ICMP) oraz twardy (pełny TCP scan).
  - Konfigurowalny zakres IP i portów, asynchroniczne skanowanie (nie blokuje GUI).
  - Prezentacja wyników na żywo, możliwość zatrzymania skanowania.
  - Automatyczne wykrywanie zakresu sieci na podstawie interfejsu.
  - Lista wykrytych hostów, status, otwarte porty, hostname (jeśli możliwe).

- **Wizualizacja ruchu sieciowego:**  
  - Dynamiczne wykresy i mapy prezentujące przepływ danych oraz aktywność protokołów.
  - Dashboard z metrykami ruchu i alarmów.

- **Zaawansowana konfiguracja:**  
  - Możliwość edycji reguł bezpieczeństwa i parametrów AI bezpośrednio z poziomu GUI.
  - Eksport i import konfiguracji oraz wyników skanowania/analityki.

- **Obsługa wielu interfejsów sieciowych jednocześnie:**  
  - Przełączanie monitoringu oraz skanowania pomiędzy różnymi kartami sieciowymi.
  - Podgląd statusu wszystkich dostępnych interfejsów.

- **Integracja z systemami zewnętrznymi:**  
  - Możliwość eksportu logów i alertów do syslog, Windows Event Log.
  - Przygotowanie pod integrację z SIEM oraz eksport do formatu kompatybilnego z narzędziami bezpieczeństwa.

- **Testy jednostkowe i automatyczne CI/CD:**  
  - Rozbudowany zestaw testów jednostkowych pokrywających kluczowe komponenty.
  - Zautomatyzowane workflow CI/CD w GitHub Actions.

Więcej szczegółów oraz pełny opis architektury znajdziesz w plikach:  
- [STRUKTURA_PROJEKTU.md](STRUKTURA_PROJEKTU.md)  
- [SESSION_NOTES.md](SESSION_NOTES.md)  
- [BUGS_AND_FIXES.md](BUGS_AND_FIXES.md)  
- [STRUKTURA_KATALOGÓW.md](STRUKTURA_KATALOGÓW.md)  

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

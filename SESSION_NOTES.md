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

---

## TODO

- [ ] Rozwinąć szkielet plików `core/` i `ui/`
- [ ] Rozpisać kolejne etapy rozwoju projektu
- [ ] Doprecyzować wymagania AI
- [ ] Opracować prototyp GUI

# Struktura projektu

Stan na dzień: 2025-08-12

```
.
├── .github/
│   ├── workflows/
│   │   └── python-app.yml
│   └── ISSUE_TEMPLATE/
│       └── bug_report.md
├── __pycache__/
│   └── main.cpython-311.pyc
├── core/
│   ├── __init__.py
│   ├── ai_engine.py
│   ├── packet_sniffer.py
│   ├── rules.py
│   ├── system_info.py
│   ├── utils.py
│   └── models/
│       ├── __init__.py
│       └── alert_model.py
├── tests/
│   ├── __init__.py
│   ├── test_ai_engine.py
│   ├── test_packet_sniffer.py
│   └── integration/
│       ├── __init__.py
│       └── test_end_to_end.py
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── menu.py
│   │   └── status_bar.py
│   └── resources/
│       ├── logo.png
│       └── style.qss
├── BUGS_AND_FIXES.md
├── README.md
├── SESSION_NOTES.md
├── main.py
├── requirements.txt
```  

## Opis katalogów i plików

- **.github/** – pliki konfiguracyjne GitHub (workflows, szablony zgłoszeń).
  - **workflows/** – workflow CI, np. GitHub Actions.
  - **ISSUE_TEMPLATE/** – szablony zgłoszeń błędów, propozycji.
- **__pycache__/** – pliki tymczasowe Pythona (ignorowane przez .gitignore).
- **core/** – moduły logiki aplikacji.
  - **models/** – modele danych, np. alertów, pakietów.
- **tests/** – testy jednostkowe i integracyjne.
  - **integration/** – testy integracyjne.
- **ui/** – elementy interfejsu użytkownika.
  - **components/** – komponenty GUI, np. menu, status bar.
  - **resources/** – zasoby statyczne, np. obrazki, style.
- **BUGS_AND_FIXES.md** – notatki o błędach i poprawkach.
- **README.md** – opis projektu.
- **SESSION_NOTES.md** – notatki z pracy/narady.
- **main.py** – główny plik uruchamiający aplikację.
- **requirements.txt** – zależności projektu.

---

## Notatki

- Jeśli pojawią się nowe podkatalogi lub pliki, dodawaj je do tej struktury.
- Zachowaj porządek w opisie podkatalogów – zawsze rozwijaj je do końca.
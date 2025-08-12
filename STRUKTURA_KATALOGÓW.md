skaner3/
│
├── .github/  
│   └── (zawartość niedostępna; katalog GitHub, np. workflow CI/CD)
│
├── __pycache__/
│   └── main.cpython-313.pyc  # Skopilowane pliki Pythona (cache)
│
├── core/
│   ├── __init__.py           # Inicjalizuje moduł core
│   ├── ai_engine.py          # Logika silnika AI, analiza danych
│   ├── sample.py             # Przykładowe dane/procesy
│   └── utils.py              # Funkcje pomocnicze (utilities) dla core
│
├── tests/
│   ├── __pycache__/
│   │   ├── test_ai_engine.cpython-313.pyc
│   │   ├── test_sample.cpython-313.pyc
│   │   └── test_utils.cpython-313.pyc
│   ├── test_ai_engine.py     # Testy jednostkowe dla ai_engine.py
│   ├── test_sample.py        # Testy jednostkowe dla sample.py
│   └── test_utils.py         # Testy jednostkowe dla utils.py
│
├── ui/
│   ├── __init__.py           # Inicjalizuje moduł ui
│   ├── __pycache__/
│   │   ├── ai_status_viewer.cpython-313.pyc
│   │   ├── alert_viewer.cpython-313.pyc
│   │   ├── config_dialog.cpython-313.pyc
│   │   ├── main_window.cpython-313.pyc
│   │   └── packet_viewer.cpython-313.pyc
│   ├── ai_status_viewer.py   # Komponent UI do podglądu statusu AI
│   ├── alert_viewer.py       # Komponent UI do wyświetlania alertów
│   ├── config_dialog.py      # Okno dialogowe konfiguracji
│   ├── main_window.py        # Główne okno aplikacji
│   └── packet_viewer.py      # Komponent UI do podglądu pakietów danych
│
├── BUGS_AND_FIXES.md         # Lista znanych błędów i poprawek
├── README.md                 # Podstawowy opis projektu
├── SESSION_NOTES.md          # Notatki z sesji programistycznych
├── STRUKTURA_PROJEKTU.md     # Opis architektury projektu
├── STRUKTURA_KATALOGÓW.md    # Struktura katalogów i opis plików
├── main.py                   # Plik główny uruchamiający aplikację
├── requirements.txt          # Wymagane biblioteki Pythona

# AI Network Sniffer v0.3.0

Inteligentny sniffer sieciowy z AI do wykrywania anomalii i zagrożeń bezpieczeństwa.

## 🚀 Funkcje

### Podstawowe
- **Przechwytywanie pakietów** w czasie rzeczywistym (Scapy) lub symulacja
- **Indeksowanie pakietów** od najstarszego do najnowszego
- **Szczegółowy widok pakietów** z hex dump, ASCII i geolokalizacją IP
- **Filtrowanie i wyszukiwanie** pakietów po protokole, IP, porcie

### AI/ML
- **Wykrywanie anomalii** heurystyczne + ML (IsolationForest + Half-Space Trees)
- **Konfigurowalne progi** dla różnych modeli
- **Status AI w czasie rzeczywistym** z parametrami i metrykami
- **Przełącznik "tylko anomalie do alertów"**

### Eksport i logowanie
- **Osobne formaty** dla pakietów i alertów (CSV/TXT)
- **Wybór katalogu docelowego** dla logów i eksportów
- **Auto-rotacja plików** po określonej liczbie wierszy
- **Auto-czyszczenie starych plików** po X dniach
- **Eksport konfiguracji** do/z JSON z UI state

### UI/UX
- **Czytelne interfejsy sieciowe** (Wi-Fi, Ethernet, Loopback, Virtual)
- **Ikony i kolory** dla typów interfejsów
- **Monitor CPU/RAM** w czasie rzeczywistym
- **Skróty klawiaturowe** (F5, Shift+F5, Ctrl+,)
- **Persystentne ustawienia** UI i konfiguracji
- **Przycisk "Reset do domyślnych"**

## 📋 Wymagania

- Python 3.8+
- PyQt5
- Scapy (opcjonalnie)
- NumPy
- scikit-learn (opcjonalnie)
- River (opcjonalnie)
- psutil
- requests

## 🚀 Jak uruchomić

```bash
# Instalacja zależności
pip install -r requirements.txt

# Uruchomienie
python main.py
```

## ⚙️ Konfiguracja

### Eksport
- **Format globalny**: domyślny format dla wszystkich plików
- **Format pakietów**: osobny format dla logów pakietów
- **Format alertów**: osobny format dla logów alertów
- **Auto-rotacja**: liczba wierszy przed rotacją pliku
- **Auto-czyszczenie**: usuwanie plików starszych niż X dni
- **Katalog docelowy**: wybór ścieżki dla logów i eksportów

### AI/ML
- **ML włączony**: włącza/wyłącza modele ML
- **Contamination**: próg anomalii dla IsolationForest
- **Refit interval**: co ile próbek trenować model
- **Stream model**: włącza model strumieniowy (River HST)
- **Z-threshold**: próg dla modelu strumieniowego
- **Combined threshold**: próg łączony dla wszystkich modeli

## 🔧 Struktura projektu

```
skaner3/
├── core/                 # Logika biznesowa
│   ├── ai_engine.py     # Silnik AI/ML
│   ├── packet_sniffer.py # Przechwytywanie pakietów
│   ├── rules.py         # Reguły bezpieczeństwa
│   └── utils.py         # Narzędzia pomocnicze
├── ui/                   # Interfejs użytkownika
│   ├── main_window.py   # Główne okno aplikacji
│   ├── packet_viewer.py # Widok pakietów
│   ├── alert_viewer.py  # Widok alertów
│   ├── config_dialog.py # Dialog konfiguracji
│   └── ai_status_viewer.py # Status AI
├── tests/                # Testy jednostkowe
├── main.py              # Punkt wejścia
└── requirements.txt     # Zależności
```

## 🧪 Testy

```bash
# Uruchomienie testów
pytest tests/

# Testy z pokryciem
pytest --cov=core tests/
```

## 📝 Historia zmian

### v0.3.0
- ✅ Osobne formaty eksportu dla pakietów i alertów
- ✅ Wybór katalogu docelowego dla auto-logowania
- ✅ Auto-czyszczenie starych plików po X dniach
- ✅ Przycisk "Reset do domyślnych" w konfiguracji
- ✅ Tytuł okna z wersją programu
- ✅ Naprawione błędy spójności konfiguracji

### v0.2.0
- ✅ Model ML strumieniowy (River Half-Space Trees)
- ✅ Konfigurowalny próg `combined_score`
- ✅ Przełącznik "tylko anomalie do alertów"
- ✅ Automatyczne logowanie z rotacją
- ✅ Testy jednostkowe dla AIEngine i utils
- ✅ GitHub Actions CI/CD

### v0.1.0
- ✅ MVP z podstawowym przechwytywaniem pakietów
- ✅ Indeksowanie i szczegółowy widok pakietów
- ✅ AI Engine z IsolationForest
- ✅ UI z filtrami i metrykami systemowymi
- ✅ Czytelne interfejsy sieciowe
- ✅ Eksport konfiguracji i UI state

## 🐛 Znane ograniczenia

- Scapy wymaga uprawnień administratora na niektórych systemach
- Model ML może wymagać dużej ilości pamięci przy dużych buforach
- Geolokalizacja IP może być ograniczona przez API

## 🤝 Wkład

1. Fork projektu
2. Utwórz branch (`git checkout -b feature/amazing-feature`)
3. Commit zmiany (`git commit -m 'Add amazing feature'`)
4. Push do branch (`git push origin feature/amazing-feature`)
5. Otwórz Pull Request

## 📄 Licencja

MIT License - zobacz [LICENSE](LICENSE) dla szczegółów.

### Dokumentacja
- [x] README.md zaktualizowany do v0.3.0
- [x] SESSION_NOTES.md zaktualizowany
- [x] Historia zmian w README
- [x] BUGS_AND_FIXES.md - dokumentacja błędów i rozwiązań
- [ ] Dokumentacja API
- [ ] Przewodnik użytkownika
- [ ] Przewodnik dewelopera
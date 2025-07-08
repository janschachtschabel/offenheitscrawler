# 🕷️ Offenheitscrawler

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red.svg)](https://streamlit.io)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Ein intelligenter, KI-gestützter Web-Crawler mit modernem Streamlit-Interface zur automatischen Bewertung von Offenheitskriterien bei verschiedenen Organisationstypen.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1Mnpwi9xlfdoUsNpBvwRCHkkiLmUkY2s3?usp=sharing)

**📊 [Demo: Offenheitscrawler Google Colab Notebook](https://colab.research.google.com/drive/1Mnpwi9xlfdoUsNpBvwRCHkkiLmUkY2s3?usp=sharing)**

> Testen Sie den Offenheitscrawler direkt im Browser – keine lokale Installation nötig!

## ✨ Hauptfunktionen

### 🤖 KI-gestützte Analyse
- **Large Language Model Integration**: Nutzt OpenAI GPT für intelligente Kriterienbewertung
- **Automatische Textanalyse**: Erkennt und bewertet Offenheitskriterien in Webinhalten
- **Konfidenz-Scoring**: Jede Bewertung wird mit einem Vertrauenswert versehen
- **Kontextuelle Begründungen**: Detaillierte Erklärungen für jede Bewertung

### 🕸️ Erweiterte Crawling-Funktionen
- **Crawl4AI Integration**: Moderne, asynchrone Crawling-Engine
- **Intelligente Navigation**: Automatische Erkennung relevanter Unterseiten
- **Robuste Fehlerbehandlung**: Graceful Handling von Netzwerkfehlern und Timeouts
- **Flexible Tiefensteuerung**: Konfigurierbare Crawling-Tiefe pro Organisation

### 📊 Umfassende Visualisierungen
- **Automatische Diagrammerstellung**: PNG-Export mit Matplotlib und Seaborn
- **Interaktive Dashboards**: Streamlit-basierte Echtzeit-Visualisierungen
- **Mehrdimensionale Statistiken**: Organisations- und kriterienbasierte Auswertungen
- **Export-Funktionen**: Download von Grafiken und Daten in verschiedenen Formaten

### 🎯 Multi-Format Export
- **Drei CSV-Ausgabeformate**: Detaillierte Kriterien, Organisations-Statistiken, Kriterien-Statistiken
- **Automatische Visualisierungen**: Balkendiagramme, Histogramme, Scatterplots, Tortendiagramme
- **Zeitstempel-basierte Archivierung**: Eindeutige Dateinamen für historische Nachverfolgung
- **Excel-kompatible Formate**: UTF-8-SIG Encoding für problemlose Excel-Integration

## 🏗️ Unterstützte Organisationstypen

Jeder Organisationstyp verfügt über einen spezialisierten YAML-Kriterienkatalog mit hierarchischer Struktur:

| Typ | Beschreibung | Kriterien-Dimensionen |
|-----|-------------|----------------------|
| 🎓 **Bildungseinrichtungen** | Schulen, Bildungsinstitute | Transparenz, Partizipation, Rechenschaftslegung |
| 🏛️ **Hochschulen** | Universitäten, Fachhochschulen | Governance, Forschung, Lehre, Verwaltung |
| 🎭 **Kultureinrichtungen** | Museen, Theater, Bibliotheken | Kulturelle Offenheit, Zugänglichkeit, Partizipation |
| 🔬 **Forschungseinrichtungen** | Institute, Forschungszentren | Open Science, Datenoffenheit, Kollaboration |
| 📺 **Öffentlich-rechtlicher Rundfunk** | TV- und Radiosender | Medientransparenz, Programmoffenheit, Bürgernähe |

### 📋 Kriterien-Hierarchie

Jeder Katalog folgt einer einheitlichen 4-stufigen Struktur:
```
Dimensionen → Faktoren → Faktortypen → Kriterien
```

## 🚀 Installation

### Voraussetzungen
- Python 3.8 oder höher
- OpenAI API-Schlüssel (für KI-gestützte Bewertungen)
- Mindestens 4GB RAM (für größere Crawling-Operationen)

### Schritt-für-Schritt Installation

```bash
# 1. Repository klonen
git clone https://github.com/janschachtschabel/offenheitscrawler
cd offenheitscrawler

# 2. Virtuelle Umgebung erstellen
python -m venv venv

# 3. Umgebung aktivieren
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Dependencies installieren
pip install -r requirements.txt

# 5. Umgebungsvariablen konfigurieren (optional)
cp .env.example .env
# Bearbeiten Sie .env mit Ihrem OpenAI API-Schlüssel
```

### 📦 Hauptabhängigkeiten

- **Streamlit** (≥1.28.0) - Web-Interface
- **Crawl4AI** (≥0.2.0) - Moderne Crawling-Engine
- **OpenAI** (≥1.0.0) - KI-Integration
- **Pandas** (≥2.0.0) - Datenverarbeitung
- **Matplotlib** (≥3.7.0) - Visualisierungen
- **Seaborn** (≥0.12.0) - Erweiterte Statistik-Plots
- **BeautifulSoup4** (≥4.12.0) - HTML-Parsing
- **Loguru** (≥0.7.0) - Erweiterte Protokollierung

## 💻 Verwendung

### 🚀 Anwendung starten

```bash
# Streamlit-App starten
streamlit run app.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:8501`.

### 📋 Detaillierter Workflow

#### 1️⃣ **Vorbereitung**
- 📁 CSV-Datei mit Organisationen vorbereiten (Format: `Name;URL`)
- 🔑 OpenAI API-Schlüssel in den Einstellungen konfigurieren
- ⚙️ Crawling-Parameter nach Bedarf anpassen

#### 2️⃣ **Datenimport**
- 📄 CSV-Datei hochladen (automatische Format-Erkennung)
- 🎯 Organisationsbereich auswählen (alle, Bereich, einzelne)
- 📋 Organisationstyp und Kriterienkatalog wählen

#### 3️⃣ **Konfiguration**
- 🔍 **Crawling-Tiefe**: Anzahl der zu durchsuchenden Unterseiten
- 🔄 **Retry-Versuche**: Anzahl Wiederholungen bei Fehlern
- 🎯 **Konfidenz-Schwellwert**: Mindestvertrauen für Bewertungen
- 🚀 **Crawling-Strategie**: Standard oder erweitert

#### 4️⃣ **Crawling-Prozess**
- ▶️ Crawling starten und Echtzeit-Fortschritt verfolgen
- 📊 Live-Statistiken zu erfolgreichen/fehlgeschlagenen Organisationen
- ⏸️ Möglichkeit zum Pausieren/Fortsetzen
- 📝 Detaillierte Logs für Debugging

#### 5️⃣ **Ergebnisanalyse**
- 📊 **Statistiken-Dashboard**: Übersicht über alle Ergebnisse
- 🗺️ **Interaktive Visualisierungen**: Automatisch generierte Diagramme
- 🔍 **Detailansicht**: Einzelne Organisationen und Kriterien erkunden
- 📈 **Performance-Metriken**: Erfüllungsraten und Konfidenzwerte

#### 6️⃣ **Export & Reporting**
- 📁 **Drei CSV-Formate**: Detailliert, Organisations-Stats, Kriterien-Stats
- 🖼️ **Automatische Visualisierungen**: PNG-Grafiken mit hoher Auflösung
- 📅 **Zeitstempel-Archivierung**: Historische Nachverfolgung
- 📊 **JSON-Export**: Maschinenlesbare Zusammenfassungen

### 🌐 Hauptbereiche der Anwendung

| Bereich | Funktion | Beschreibung |
|---------|----------|-------------|
| 🏠 **Hauptseite** | Crawling & Konfiguration | CSV-Upload, Einstellungen, Crawling-Start |
| 📊 **Statistiken** | Analyse & Visualisierung | Dashboards, Diagramme, Detailansichten |
| ⚙️ **Einstellungen** | Konfiguration | API-Keys, Crawling-Parameter, Erweiterte Optionen |

## 📁 Projektstruktur

```
offenheitscrawler/
├── app.py                     # 🏠 Streamlit Hauptanwendung
├── requirements.txt           # 📦 Python-Abhängigkeiten
├── README.md                  # 📝 Dokumentation
├── src/                       # 💻 Hauptquellcode
│   ├── __init__.py
│   ├── crawler/               # 🕷️ Crawling-Engine
│   │   ├── crawl4ai_crawler.py    # Moderne Crawling-Implementierung
│   │   ├── organization_crawler.py # Organisations-spezifisches Crawling
│   │   └── page_analyzer.py       # Seitenanalyse und -bewertung
│   ├── analysis/              # 🤖 KI-gestützte Analyse
│   │   ├── llm_evaluator.py       # OpenAI GPT Integration
│   │   ├── criteria_analyzer.py   # Kriterienauswertung
│   │   └── confidence_scorer.py   # Konfidenz-Bewertung
│   ├── config/                # ⚙️ Konfiguration & YAML-Loader
│   │   ├── yaml_loader.py         # YAML-Katalog-Parser
│   │   └── settings_manager.py    # Einstellungsverwaltung
│   ├── statistics/            # 📊 Statistiken & Reporting
│   │   ├── visualizations.py      # Matplotlib/Seaborn Plots
│   │   └── report_generator.py    # CSV/JSON Export
│   ├── ui/                    # 📱 Streamlit UI-Komponenten
│   │   ├── main_page.py           # Haupt-Crawling-Interface
│   │   ├── statistics_page.py     # Statistiken & Visualisierungen
│   │   └── settings_page.py       # Konfigurationsseite
│   └── utils/                 # 🔧 Hilfsfunktionen
│       ├── csv_handler.py         # CSV Import/Export
│       ├── logger.py              # Erweiterte Protokollierung
│       └── validators.py          # Datenvalidierung
├── criteria/                  # 📋 YAML-Kriterienkataloge
│   ├── bildungseinrichtungen.yaml
│   ├── hochschulen.yaml
│   ├── kultureinrichtungen.yaml
│   ├── forschungseinrichtungen.yaml
│   └── oeffentlich_rechtlicher_rundfunk.yaml
├── output/                    # 📁 Generierte Ausgaben
│   ├── *.csv                  # CSV-Exporte mit Zeitstempel
│   └── visualizations/        # Automatisch generierte Grafiken
├── tests/                     # 🧪 Unit Tests
├── data/                      # 📊 Beispieldaten
└── docs/                      # 📚 Erweiterte Dokumentation
```

## 🔧 Entwicklung

### 📝 Code-Qualität

```bash
# Code-Qualität prüfen
ruff check .
ruff format .

# Type-Checking
mypy src/

# Tests ausführen
pytest

# Coverage-Report
pytest --cov=src --cov-report=html
```

### 🔍 Debugging

```bash
# Detaillierte Logs aktivieren
streamlit run app.py --logger.level=DEBUG

# Einzelne Module testen
python -m src.crawler.crawl4ai_crawler
python -m src.analysis.llm_evaluator
```

### 📚 API-Dokumentation

```bash
# Automatische Dokumentation generieren
sphinx-build -b html docs/ docs/_build/
```

## 📁 CSV-Format (Input)

Die CSV-Datei unterstützt flexible Formate mit automatischer Erkennung:

### ✅ Unterstützte Formate

**Standard-Format mit Kopfzeile:**
```csv
Organisation;URL
Universität München;https://www.lmu.de
TU Berlin;https://www.tu-berlin.de
ETH Zürich;https://ethz.ch
```

**Ohne Kopfzeile:**
```csv
Universität München;https://www.lmu.de
TU Berlin;https://www.tu-berlin.de
ETH Zürich;https://ethz.ch
```

**Erweiterte Spalten (werden ignoriert):**
```csv
Organisation;URL;Stadt;Land;Typ
Universität München;https://www.lmu.de;München;Deutschland;Universität
```

### 📝 Format-Spezifikationen

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| **Trennzeichen** | `;` (Semikolon) | Standard-Separator |
| **Encoding** | UTF-8 | Unterstützt Umlaute und Sonderzeichen |
| **Kopfzeile** | Optional | Automatische Erkennung |
| **Minimale Spalten** | 2 | Name und URL erforderlich |
| **Maximale Zeilen** | Unbegrenzt | Abhängig von Systemressourcen |

## 📄 Output-Formate

Die Anwendung generiert umfassende Berichte in verschiedenen Formaten:

### 📁 CSV-Exporte (3 Dateien)

#### 1. **Detaillierte Kriterienbewertungen**
```csv
Organisation;Basis_URL;Kriterium_ID;Kriterium_Name;Erfüllt;Konfidenz;Begründung;Quelle_URL;Beweis_Text;Muster_Typ
Universität XYZ;https://uni-xyz.de;transparenz_finanzen;Transparenz Finanzen;Ja;0.85;Jahresbericht gefunden;https://uni-xyz.de/finanzen;Der Jahresbericht 2023 zeigt...;financial_report
```

#### 2. **Organisations-Statistiken**
```csv
Organisation;Basis_URL;Anzahl_Kriterien;Erfüllte_Kriterien;Erfüllungsgrad;Durchschnittliche_Konfidenz;Erfolgreiche_Seiten;Fehlgeschlagene_Seiten
Universität XYZ;https://uni-xyz.de;25;18;72.0;0.78;12;3
```

#### 3. **Kriterien-Statistiken**
```csv
Kriterium_ID;Kriterium_Name;Anzahl_Organisationen;Erfüllte_Organisationen;Erfüllungsrate;Durchschnittliche_Konfidenz
transparenz_finanzen;Transparenz Finanzen;50;35;70.0;0.82
```

### 🖼️ Automatische Visualisierungen

Jede Crawling-Session generiert automatisch hochauflösende PNG-Grafiken:

| Visualisierung | Dateiname | Beschreibung |
|----------------|-----------|-------------|
| **Organisations-Übersicht** | `organisationen_uebersicht_[katalog]_[timestamp].png` | Balkendiagramm und Histogramm der Erfüllungsgrade |
| **Kriterien-Performance** | `kriterien_performance_[katalog]_[timestamp].png` | Scatterplot Konfidenz vs. Erfüllungsrate |
| **Zusammenfassende Statistik** | `zusammenfassung_statistik_[katalog]_[timestamp].png` | Top/Bottom Kriterien, Tortendiagramme, Boxplots |

### 📊 JSON-Export

```json
{
  "timestamp": "2024-01-15T14:30:22",
  "catalog_used": "hochschulen",
  "total_organizations": 50,
  "successful_organizations": 45,
  "overall_fulfillment_rate": 68.5,
  "organizations": [
    {
      "name": "Universität XYZ",
      "url": "https://uni-xyz.de",
      "fulfillment_rate": 72.0,
      "total_criteria": 25,
      "fulfilled_criteria": 18
    }
  ]
}
```

## ⚙️ Erweiterte Konfiguration

### 🔑 OpenAI API-Konfiguration

```bash
# Umgebungsvariable setzen
export OPENAI_API_KEY="your-api-key-here"

# Oder in .env Datei
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### 🎛️ Crawling-Parameter

| Parameter | Standard | Beschreibung |
|-----------|----------|-------------|
| **Max. Tiefe** | 3 | Anzahl Unterseiten pro Organisation |
| **Retry-Versuche** | 3 | Wiederholungen bei Fehlern |
| **Timeout** | 30s | Maximale Wartezeit pro Seite |
| **Konfidenz-Schwellwert** | 0.7 | Mindestvertrauen für Bewertungen |
| **Parallelität** | 5 | Gleichzeitige Crawling-Prozesse |

### 📊 Visualisierungs-Einstellungen

```python
# In settings_page.py anpassbar
VISUALIZATION_CONFIG = {
    'dpi': 300,  # Auflösung der PNG-Dateien
    'figsize': (12, 8),  # Diagrammgröße
    'style': 'seaborn-v0_8',  # Matplotlib-Stil
    'color_palette': 'viridis'  # Farbschema
}
```

## 🚨 Troubleshooting

### ❌ Häufige Probleme

#### **OpenAI API-Fehler**
```
Error: OpenAI API key not found
```
**Lösung:** API-Schlüssel in den Einstellungen konfigurieren

#### **Crawling-Timeouts**
```
Timeout error after 30 seconds
```
**Lösung:** Timeout-Werte in den erweiterten Einstellungen erhöhen

#### **Speicher-Probleme**
```
MemoryError: Unable to allocate array
```
**Lösung:** Anzahl paralleler Prozesse reduzieren oder Organisationen in kleineren Batches verarbeiten

#### **Visualisierungs-Fehler**
```
ModuleNotFoundError: No module named 'matplotlib'
```
**Lösung:** 
```bash
pip install matplotlib seaborn
```

### 🔍 Debug-Modus

```bash
# Detaillierte Logs aktivieren
streamlit run app.py --logger.level=DEBUG

# Einzelne Komponenten testen
python -c "from src.crawler.crawl4ai_crawler import *; test_connection()"
```

### 📋 System-Anforderungen

| Komponente | Minimum | Empfohlen |
|------------|---------|----------|
| **Python** | 3.8 | 3.11+ |
| **RAM** | 4GB | 8GB+ |
| **Speicher** | 2GB | 10GB+ |
| **CPU** | 2 Kerne | 4+ Kerne |
| **Internet** | Stabil | Hochgeschwindigkeit |

## 🔄 Updates & Migration

### 📦 Abhängigkeiten aktualisieren

```bash
# Alle Pakete aktualisieren
pip install --upgrade -r requirements.txt

# Spezifische Pakete
pip install --upgrade streamlit crawl4ai openai
```

### 🗂️ Daten-Migration

Bei Updates werden bestehende CSV-Dateien und Visualisierungen automatisch beibehalten. Neue Features sind rückwärtskompatibel.

## 🤝 Beitragen

### 🚀 Entwicklung

1. **Fork** des Repositories
2. **Feature-Branch** erstellen (`git checkout -b feature/AmazingFeature`)
3. **Änderungen** committen (`git commit -m 'Add AmazingFeature'`)
4. **Branch** pushen (`git push origin feature/AmazingFeature`)
5. **Pull Request** erstellen

### 📋 Beitrag-Richtlinien

- **Code-Stil:** Folgen Sie PEP 8 und verwenden Sie `ruff` für Formatierung
- **Tests:** Fügen Sie Tests für neue Features hinzu
- **Dokumentation:** Aktualisieren Sie README und Docstrings
- **Commits:** Verwenden Sie aussagekräftige Commit-Nachrichten

### 🐛 Bug Reports

Beim Melden von Bugs bitte folgende Informationen angeben:
- Python-Version
- Betriebssystem
- Vollständige Fehlermeldung
- Schritte zur Reproduktion
- Screenshots (falls relevant)

## 📄 Lizenz

Dieses Projekt steht unter der **Apache 2.0 Lizenz**. Siehe `LICENSE` Datei für Details.

## 🆘 Support

### 📞 Kontakt

- **Issues:** [GitHub Issues](https://github.com/janschachtschabel/offenheitscrawler/issues)
- **Diskussionen:** [GitHub Discussions](https://github.com/janschachtschabel/offenheitscrawler/discussions)
- **E-Mail:** support@offenheitscrawler.de

### 📚 Weitere Ressourcen

- **Dokumentation:** [docs/](docs/)
- **Beispiele:** [data/examples/](data/examples/)
- **Video-Tutorials:** [YouTube Playlist](https://youtube.com/playlist)
- **API-Referenz:** [docs/api/](docs/api/)

---

**Entwickelt mit ❤️ für mehr Transparenz und Offenheit**

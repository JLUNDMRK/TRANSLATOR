# DTC Analyzer

Litet GUI-program för att:
- läsa claim-statistikfil (Excel)
- läsa DTC-databas (Excel)
- extrahera felkoder, komponentkoder, SW-versioner
- slå upp DTC-information
- översätta text till engelska
- tolka felmod (failure mode) med GPT (support för interna, OpenAI/extern och GitHub Copilot-stilen runtimes)
- skriva ut ny Excel-fil

## Körning (utveckling)

1. Installera beroenden:
   ```bash
   pip install openpyxl pandas requests
   ```

## Features (Steg 1) - Code Extraction

### Code Extraction Module
Nya funktioner för att automatiskt extrahera felkoder och komponentkoder från fritext:

- **Extrahera felkoder**: DTC0101, EMS23AF, 12345, 23AFh, etc.
- **Extrahera komponentkoder**: T123, T-123, T 987, etc.
- **Normalisering**: Ta bort skiljetecken, konvertera till versaler
- **Deduplicering**: Samma kod duplikeras inte
- **Batch-processing**: Förbättra hela Excel-filer med nya kolumner

**Moduler:**
- `src/pipeline/code_extract.py` - Huvudmodul
- `src/pipeline/extract_cli.py` - CLI-verktyg för Excel-filer
- `tests/test_code_extract.py` - 47+ enhetstester

**Dokumentation:** Se [CODE_EXTRACT_README.md](CODE_EXTRACT_README.md)

**Användning:**

```bash
# CLI - extrahera koder från Excel-fil
python -m src.pipeline.extract_cli --in claims.xlsx --out claims_extracted.xlsx --col "description"
```

```python
# Python API
from src.pipeline.code_extract import extract_codes, augment_dataframe
import pandas as pd

# Extrahera koder från text
text = "Engine error DTC0101 with component T123"
codes = extract_codes(text)

# Förbättra DataFrame
df = pd.read_excel('claims.xlsx')
result = augment_dataframe(df, 'description_col')
result.to_excel('claims_extracted.xlsx')
```

## Steg 2 (kommande)

- Ladda och analysera DTC-definitioner från XML
- Slå upp DTC-koder mot databasen för att hämta beskrivningar
- Utöka utdatafilen med DTC-headings

Se [CODE_EXTRACT_README.md](CODE_EXTRACT_README.md) för mer detaljer om implementation av Steg 1 och Steg 2 stubs.

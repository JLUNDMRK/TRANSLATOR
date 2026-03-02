# DTC Analyzer

Litet GUI-program för att:
- läsa claim-statistikfil (Excel)
- läsa DTC-databas (Excel)
- extrahera felkoder, komponentkoder, SW-versioner
- slå upp DTC-information
- översätta text till engelska
- tolka felmod (failure mode) med GPT
- skriva ut ny Excel-fil

## Körning (utveckling)

1. Installera beroenden:
   ```bash
   pip install openpyxl pandas requests

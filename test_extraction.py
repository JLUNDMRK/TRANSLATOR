from app_extract import extract_codes

# Test the problematic texts
test_cases = [
    ("CUST_TEXT:KUNDANMÄRKNING: FORDON TAPPAR VÄXELN IBLAND VID STILLASTÅENDE, FELSÖKNING - KONTROLL FELKODER OCH FRAS FELKOD GMS2579, LÄGESGIVAREN ANGER ATT KOPPLINGSHYLSAN INTE NÅR SITT NEUTRALLÄGE TROTS UPPREPADE FÖRSÖK, BYTE LEDNINGSNÄT MED GIVARE T229, T230 & T231, ÄVEN ETT OLJELÄCKAGE TILL VÄXLINGSENHETEN SOM ÅTGÄRDADES MED ATT BYTA PACKNINGAR TILL ENHETEN. PROVKÖRNING. ALLTING FUNGERAR SOM DET SKA. KUND NÖJD EFTER ÅTGÄRD ,WORKSHOP_TEXT:", "Test 1"),
    ("CUST_TEXT:Klient zglosil: Czasami gina biegi (nie mozna zmienic na R czy D jak zostawi sie na N) - powraca do normy po zgaszeniu auta. Mechanik zrobil diagnostyke.Bledy z czujnika t-229. Wymienil czuj...", "Test 2 (Polish with POWRACA)"),
    ("CUST_TEXT:Gears are lost while driving, it won't shift. Replaced the T229 harness, tested OK.", "Test 3 (English with REPLACED)"),
]

for text, label in test_cases:
    dtc, comp = extract_codes(text)
    print(f"\n{label}")
    print(f"DTC codes: {dtc}")
    print(f"COMP codes: {comp}")


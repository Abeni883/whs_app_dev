"""
Test-Script um WeasyPrint zu prüfen nach GTK3-Installation
"""

print("=" * 60)
print("TESTE WEASYPRINT")
print("=" * 60)

# Test 1: Import
print("\n[TEST 1] Importiere WeasyPrint...")
try:
    import weasyprint
    print("[OK] WeasyPrint erfolgreich importiert!")
    print(f"    Version: {weasyprint.__version__}")
except Exception as e:
    print(f"[FEHLER] Import fehlgeschlagen: {e}")
    exit(1)

# Test 2: HTML zu PDF
print("\n[TEST 2] Erstelle Test-PDF...")
try:
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test PDF</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { color: #2c3e50; }
        </style>
    </head>
    <body>
        <h1>WeasyPrint Test</h1>
        <p>Wenn du diese PDF siehst, funktioniert WeasyPrint!</p>
        <ul>
            <li>GTK3-Runtime: Installiert</li>
            <li>WeasyPrint: Funktioniert</li>
            <li>PDF-Export: Bereit</li>
        </ul>
    </body>
    </html>
    """

    from weasyprint import HTML
    pdf_bytes = HTML(string=html_content).write_pdf()

    # PDF speichern
    with open('test_weasyprint.pdf', 'wb') as f:
        f.write(pdf_bytes)

    print(f"[OK] Test-PDF erstellt: test_weasyprint.pdf")
    print(f"    Groesse: {len(pdf_bytes)} Bytes")

except Exception as e:
    print(f"[FEHLER] PDF-Erstellung fehlgeschlagen: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("[ERFOLG] WEASYPRINT FUNKTIONIERT!")
print("=" * 60)
print("\nDu kannst jetzt PDF-Exporte in der Anwendung nutzen!")
print("Test-PDF wurde erstellt: test_weasyprint.pdf")

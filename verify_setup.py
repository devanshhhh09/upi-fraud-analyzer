import sys
print(f"Python version: {sys.version}")

modules = [
    "pandas", "numpy", "sklearn", "xgboost",
    "sentence_transformers", "flask", "requests",
    "bs4", "pdfplumber", "whois", "langdetect",
    "matplotlib", "seaborn", "plotly", "folium",
    "jinja2", "pytest",
]

failed = []
for mod in modules:
    try:
        __import__(mod)
        print(f"  OK  {mod}")
    except ImportError:
        print(f"  FAIL  {mod}")
        failed.append(mod)

if failed:
    print(f"\nFailed imports: {failed}")
    print("Run: pip install " + " ".join(failed))
else:
    print("\nAll dependencies verified. Phase 1 complete.")

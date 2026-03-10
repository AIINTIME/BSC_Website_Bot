"""
Quick Google Sheets diagnostic.
Run from the Development folder: python test_sheets.py
"""
import json
import os
from dotenv import load_dotenv

load_dotenv()

SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")
SA_JSON        = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

print("=" * 60)
print("BSC Google Sheets Diagnostic")
print("=" * 60)
print(f"Spreadsheet ID : {SPREADSHEET_ID or 'NOT SET'}")
print(f"Service Account: {'loaded' if SA_JSON else 'NOT SET'}")
print()

if not SA_JSON:
    print("❌  GOOGLE_SERVICE_ACCOUNT_JSON is missing from .env")
    exit(1)

if not SPREADSHEET_ID:
    print("❌  GOOGLE_SPREADSHEET_ID is missing from .env")
    exit(1)

try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    from googleapiclient.errors import HttpError

    info  = json.loads(SA_JSON)
    print(f"Service account email: {info.get('client_email', 'unknown')}")

    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    print("✅  Service built OK")

    # Step 1: Can we read the spreadsheet?
    try:
        meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        tabs = [s["properties"]["title"] for s in meta["sheets"]]
        print(f"✅  Spreadsheet accessible: '{meta['properties']['title']}'")
        print(f"    Tabs: {tabs}")
    except HttpError as e:
        print(f"❌  Cannot read spreadsheet — HTTP {e.status_code}: {e.reason}")
        print("    Fix: Share the spreadsheet with the service account email above (Editor role)")
        exit(1)

    # Step 2: Can we write to Contacts_1?
    SHEET = "Contacts_1"
    if SHEET not in tabs:
        print(f"    Creating '{SHEET}' tab...")
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": [{"addSheet": {"properties": {"title": SHEET}}}]},
        ).execute()
        print(f"✅  Tab '{SHEET}' created")

    try:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET}!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [["DIAGNOSTIC_TEST", "test@bsc.com", "+880-123-456", "Test City", "diag-session"]]},
        ).execute()
        print(f"✅  Test row written to '{SHEET}' — check your spreadsheet!")
    except HttpError as e:
        print(f"❌  Cannot write to spreadsheet — HTTP {e.status_code}: {e.reason}")
        if e.status_code == 403:
            print("    Fix: Make sure the service account has EDITOR (not Viewer) access")
        exit(1)

except json.JSONDecodeError as e:
    print(f"❌  GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON: {e}")
    print("    Fix: Re-paste the JSON key (single line, no extra quotes around it)")
except Exception as e:
    print(f"❌  Unexpected error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

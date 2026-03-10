import json
import uuid
from datetime import datetime, timezone

from tenacity import retry, stop_after_attempt, wait_exponential
from googleapiclient.discovery import build
from google.oauth2 import service_account

from app.core.config import settings

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_HEADER = ["AuditID", "Timestamp", "Name", "Email", "Mobile", "Address", "SessionID"]


def _get_service():
    # Prefer loading from the JSON file on disk (avoids copy-paste corruption in .env)
    if settings.GOOGLE_SERVICE_ACCOUNT_FILE:
        creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=_SCOPES
        )
    else:
        info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _ensure_sheet_exists(service, spreadsheet_id: str, sheet_name: str) -> None:
    """Create a sheet tab if it doesn't exist, and write the header row."""
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = [s["properties"]["title"] for s in spreadsheet["sheets"]]
    if sheet_name not in existing:
        body = {"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        # Write header row
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption="RAW",
            body={"values": [_HEADER]},
        ).execute()


def _count_data_rows(service, spreadsheet_id: str, sheet_name: str) -> int:
    """Return number of data rows (header excluded)."""
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A:A",
    ).execute()
    return max(len(result.get("values", [])) - 1, 0)


def _find_active_sheet(service, spreadsheet_id: str) -> str:
    """Return the Contacts_N sheet that still has space, creating it if needed."""
    max_rows = settings.SHEETS_MAX_ROWS
    n = 1
    while True:
        sheet_name = f"Contacts_{n}"
        _ensure_sheet_exists(service, spreadsheet_id, sheet_name)
        if _count_data_rows(service, spreadsheet_id, sheet_name) < max_rows:
            return sheet_name
        n += 1


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def write_contact(name: str, email: str, mobile: str, address: str, session_id: str) -> str:
    """Append one contact row. Returns the sheet name used."""
    service = _get_service()
    spreadsheet_id = settings.GOOGLE_SPREADSHEET_ID
    sheet_name = _find_active_sheet(service, spreadsheet_id)

    row = [
        str(uuid.uuid4()),
        datetime.now(timezone.utc).isoformat(),
        name,
        email,
        mobile,
        address,
        session_id or "",
    ]

    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()

    return sheet_name

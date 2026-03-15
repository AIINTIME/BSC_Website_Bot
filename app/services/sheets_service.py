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


def _find_session_row(service, spreadsheet_id: str, session_id: str) -> tuple[str, int] | None:
    """Search all Contacts_N sheets for a row whose SessionID (col G) matches session_id.
    Returns (sheet_name, 1-based row number) or None if not found.
    """
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_names = [
        s["properties"]["title"]
        for s in spreadsheet["sheets"]
        if s["properties"]["title"].startswith("Contacts_")
    ]
    for sheet_name in sheet_names:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!G:G",
        ).execute()
        for i, cell in enumerate(result.get("values", [])):
            if cell and cell[0] == session_id:
                return sheet_name, i + 1  # 1-based
    return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def write_contact(name: str, email: str, mobile: str, address: str, session_id: str) -> str:
    """Upsert one contact row — updates in place if session already exists, otherwise appends.
    Returns the sheet name used.
    """
    service = _get_service()
    spreadsheet_id = settings.GOOGLE_SPREADSHEET_ID

    existing = _find_session_row(service, spreadsheet_id, session_id)

    if existing:
        sheet_name, row_num = existing
        # Keep the original AuditID (col A), update cols B-G only
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!B{row_num}",
            valueInputOption="RAW",
            body={"values": [[
                datetime.now(timezone.utc).isoformat(),
                name,
                email,
                mobile,
                address,
                session_id or "",
            ]]},
        ).execute()
        return sheet_name

    sheet_name = _find_active_sheet(service, spreadsheet_id)
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [[
            str(uuid.uuid4()),
            datetime.now(timezone.utc).isoformat(),
            name,
            email,
            mobile,
            address,
            session_id or "",
        ]]},
    ).execute()
    return sheet_name

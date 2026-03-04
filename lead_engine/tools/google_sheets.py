import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import logging
from typing import List, Dict, Any
from lead_engine.db.models import Lead

logger = logging.getLogger(__name__)

class GoogleSheetsTool:
    """
    Handles synchronization of leads to a Google Sheet using Service Account credentials.
    """
    
    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE")
        self.client = None
        self.sheet = None

    def _authenticate(self, override_sheet_id: str = None):
        """
        Authenticates with Google Sheets API.
        """
        target_id = override_sheet_id or self.sheet_id
        if not target_id or not self.creds_file:
            logger.warning("GoogleSheetsTool: Missing Sheet ID or GOOGLE_CREDENTIALS_FILE")
            return False
            
        if not os.path.exists(self.creds_file):
            logger.error(f"GoogleSheetsTool: Credentials file not found at {self.creds_file}")
            return False

        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(target_id).sheet1
            self.current_sheet_id = target_id
            return True
        except Exception as e:
            logger.error(f"GoogleSheetsTool: Authentication failed: {e}")
            return False

    def sync_lead(self, lead: Lead, override_sheet_id: str = None):
        """
        Pushes a single lead to the Google Sheet.
        """
        # Re-authenticate if sheet_id changed
        if override_sheet_id and (not self.sheet or getattr(self, 'current_sheet_id', None) != override_sheet_id):
            if not self._authenticate(override_sheet_id): return
        elif not self.sheet and not self._authenticate():
            return
            
        try:
            # Check if lead already exists in sheet (basic email check)
            # Fetch all emails from column 3 (C)
            emails = self.sheet.col_values(3)
            if lead.email in emails:
                logger.info(f"GoogleSheetsTool: Lead {lead.email} already exists in sheet. Skipping.")
                return

            # Append as new row
            row = [
                lead.name,
                lead.company,
                lead.email,
                lead.linkedin_url,
                lead.score,
                ", ".join(lead.tech_stack) if lead.tech_stack else "",
                lead.hiring_signal,
                lead.source_url
            ]
            self.sheet.append_row(row)
            logger.info(f"GoogleSheetsTool: Synced lead {lead.email} to Google Sheets.")
        except Exception as e:
            logger.error(f"GoogleSheetsTool: Sync failed for {lead.email}: {e}")

    def sync_all(self, leads: List[Lead]):
        """
        Bulk syncs multiple leads.
        """
        if not self.sheet and not self._authenticate():
            return
            
        for lead in leads:
            self.sync_lead(lead)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import logging
import re
import json
from typing import List, Dict, Any, Optional
from lead_engine.db.models import Lead
from lead_engine.security.encryption import SecretManager
from lead_engine.security.audit import AuditLogger

logger = logging.getLogger(__name__)


class GoogleSheetsSecurityError(Exception):
    """Raised when Google Sheets operation fails security validation"""
    pass


class GoogleSheetsTool:
    """
    Handles secure synchronization of leads to Google Sheets.
    Features:
    - Encrypted credentials storage
    - Sheet ID validation
    - Export review (only exports vetted leads)
    - Audit logging of exports
    """
    
    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.client = None
        self.sheet = None
    
    @staticmethod
    def validate_sheet_id(sheet_id: str) -> bool:
        """
        Validate Google Sheets ID format.
        Google Sheets IDs are 44 alphanumeric characters.
        """
        if not sheet_id:
            return False
        
        # Google Sheets IDs: 40-50 alphanumeric + dash/underscore
        pattern = r'^[a-zA-Z0-9\-_]{40,50}$'
        is_valid = bool(re.match(pattern, sheet_id))
        
        if not is_valid:
            logger.warning(f"Invalid Google Sheets ID format: {sheet_id[:10]}...")
        
        return is_valid

    def _authenticate(self, override_sheet_id: str = None):
        """
        Authenticate with Google Sheets API with validation.
        
        Raises:
            GoogleSheetsSecurityError: If validation fails
        """
        target_id = override_sheet_id or self.sheet_id
        
        # Validate sheet ID
        if not self.validate_sheet_id(target_id):
            raise GoogleSheetsSecurityError("Invalid Google Sheets ID format")
        
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Load from environment variable
            creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
            if not creds_json_str:
                raise GoogleSheetsSecurityError("No valid Google credentials found. Set GOOGLE_CREDENTIALS_JSON environment variable.")

            # Support encrypted credentials
            if creds_json_str.startswith("encrypted:"):
                logger.info("Decrypting Google credentials...")
                creds_json_str = SecretManager.decrypt(creds_json_str[10:])

            logger.info("Authenticating with Google Sheets via JSON environment variable.")
            creds_dict = json.loads(creds_json_str)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(target_id).sheet1
            self.current_sheet_id = target_id
            
            logger.info(f"✅ Successfully authenticated with Google Sheets: {target_id[:10]}...")
            return True
        except Exception as e:
            logger.error(f"Google Sheets authentication failed: {e}")
            raise GoogleSheetsSecurityError(f"Authentication failed: {e}")

    def sync_lead(self, lead: Lead, override_sheet_id: str = None, user: str = "system"):
        """
        Sync a lead to Google Sheets with validation.
        
        Only exports leads with vetting_status = 'good' by default.
        
        Args:
            lead: Lead object to export
            override_sheet_id: Optional Sheet ID to override default
            user: User performing the export (for audit logging)
            
        Raises:
            GoogleSheetsSecurityError: If validation fails
        """
        # Validate that lead is vetted (only export approved leads)
        if lead.vetting_status != 'good':
            raise GoogleSheetsSecurityError(
                f"Cannot export unvetted lead (status: {lead.vetting_status}). "
                "Only 'good' leads can be exported."
            )
        
        # Re-authenticate if sheet_id changed
        if override_sheet_id and (not self.sheet or getattr(self, 'current_sheet_id', None) != override_sheet_id):
            self._authenticate(override_sheet_id)
        elif not self.sheet:
            self._authenticate()
            
        try:
            # Check if lead already exists in sheet (basic email check)
            # Fetch all emails from column 3 (C)
            emails = self.sheet.col_values(3)
            if lead.email and lead.email in emails:
                logger.info(f"Lead {lead.email} already in sheet")
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
            
            # ✅ Audit log the export
            AuditLogger.log_lead_action(
                'EXPORT_TO_SHEETS',
                lead.id,
                details={'sheet_id': self.current_sheet_id},
                user=user
            )
            
            logger.info(f"✅ Exported lead {lead.name} to Google Sheets")
        except GoogleSheetsSecurityError as e:
            logger.error(f"Export failed (security): {e}")
            raise
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise

    def sync_all(self, leads: List[Lead], user: str = "system"):
        """
        Bulk syncs multiple leads with validation.
        Only exports vetted leads.
        """
        if not self.sheet:
            self._authenticate()
        
        exported_count = 0
        skipped_count = 0
        
        for lead in leads:
            try:
                self.sync_lead(lead, user=user)
                exported_count += 1
            except GoogleSheetsSecurityError as e:
                logger.warning(f"Skipped lead {lead.id}: {e}")
                skipped_count += 1
            except Exception as e:
                logger.error(f"Failed to export lead {lead.id}: {e}")
                skipped_count += 1
        
        logger.info(f"Bulk export complete: {exported_count} exported, {skipped_count} skipped")

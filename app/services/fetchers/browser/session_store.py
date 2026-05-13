"""Session store for persistent browser authentication."""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from app.core.logging import logger
from app.core.config.settings import settings


class SessionStore:
    """Persistent session storage for browser authentication."""
    
    def __init__(self, storage_dir: str = "sessions"):
        self.logger = logger.bind(service="session_store")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.session_file = self.storage_dir / "sessions.json"
        self.max_session_age_days = 30
        
    async def save_session(self, source_name: str, storage_state: Dict[str, Any]) -> None:
        """Save browser session state."""
        try:
            # Load existing sessions
            sessions = await self._load_sessions()
            
            # Update session with timestamp
            sessions[source_name] = {
                'storage_state': storage_state,
                'saved_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=self.max_session_age_days)).isoformat()
            }
            
            # Save to file
            await self._save_sessions(sessions)
            
            self.logger.info(f"Session saved for {source_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to save session for {source_name}: {e}")
    
    async def save_instahyre_session(self, storage_state: Dict[str, Any]) -> None:
        """Save Instahyre-specific session state."""
        try:
            # Create sessions directory if it doesn't exist
            self.storage_dir.mkdir(exist_ok=True)
            
            # Save to Instahyre-specific file using settings
            instahyre_session_file = Path(settings.instahyre_session_file)
            
            session_data = {
                'storage_state': storage_state,
                'saved_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=self.max_session_age_days)).isoformat(),
                'source': 'instahyre',
                'auth_method': 'google_sign_in'
            }
            
            with open(instahyre_session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Instahyre session saved to instahyre_session.json")
            
        except Exception as e:
            self.logger.error(f"Failed to save Instahyre session: {e}")
    
    async def get_instahyre_session(self) -> Optional[Dict[str, Any]]:
        """Get Instahyre-specific session state."""
        try:
            instahyre_session_file = Path(settings.instahyre_session_file)
            
            if not instahyre_session_file.exists():
                self.logger.info("No Instahyre session file found")
                return None
            
            with open(instahyre_session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.utcnow() > expires_at:
                self.logger.info("Instahyre session expired")
                return None
            
            self.logger.info("Instahyre session loaded successfully")
            return session_data['storage_state']
            
        except Exception as e:
            self.logger.error(f"Failed to load Instahyre session: {e}")
            return None
    
    async def delete_instahyre_session(self) -> None:
        """Delete Instahyre-specific session."""
        try:
            instahyre_session_file = Path(settings.instahyre_session_file)
            
            if instahyre_session_file.exists():
                instahyre_session_file.unlink()
                self.logger.info("Instahyre session deleted")
            
        except Exception as e:
            self.logger.error(f"Failed to delete Instahyre session: {e}")
    
    async def validate_instahyre_session(self, storage_state: Dict[str, Any]) -> bool:
        """Validate Instahyre session by checking for authentication indicators."""
        try:
            # Basic validation - check if session has cookies
            if not storage_state or 'cookies' not in storage_state:
                return False
            
            cookies = storage_state.get('cookies', [])
            if not cookies:
                return False
            
            # Check for Google auth cookies
            google_cookies = [
                cookie for cookie in cookies
                if 'google' in cookie.get('name', '').lower() or 
                   'accounts.google.com' in cookie.get('domain', '').lower()
            ]
            
            if not google_cookies:
                self.logger.debug("No Google auth cookies found in session")
                return False
            
            # Check session age
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate Instahyre session: {e}")
            return False
    
    async def get_session(self, source_name: str) -> Optional[Dict[str, Any]]:
        """Get saved session state."""
        try:
            sessions = await self._load_sessions()
            
            if source_name not in sessions:
                return None
            
            session_data = sessions[source_name]
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.utcnow() > expires_at:
                await self.delete_session(source_name)
                self.logger.info(f"Session expired for {source_name}")
                return None
            
            return session_data['storage_state']
            
        except Exception as e:
            self.logger.error(f"Failed to get session for {source_name}: {e}")
            return None
    
    async def delete_session(self, source_name: str) -> None:
        """Delete saved session."""
        try:
            sessions = await self._load_sessions()
            
            if source_name in sessions:
                del sessions[source_name]
                await self._save_sessions(sessions)
                self.logger.info(f"Session deleted for {source_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to delete session for {source_name}: {e}")
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            sessions = await self._load_sessions()
            expired_sources = []
            
            for source_name, session_data in sessions.items():
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if datetime.utcnow() > expires_at:
                    expired_sources.append(source_name)
            
            # Delete expired sessions
            for source_name in expired_sources:
                del sessions[source_name]
            
            if expired_sources:
                await self._save_sessions(sessions)
                self.logger.info(f"Cleaned up {len(expired_sources)} expired sessions")
            
            return len(expired_sources)
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    async def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all saved sessions with metadata."""
        try:
            sessions = await self._load_sessions()
            
            result = {}
            for source_name, session_data in sessions.items():
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                saved_at = datetime.fromisoformat(session_data['saved_at'])
                
                result[source_name] = {
                    'saved_at': saved_at.isoformat(),
                    'expires_at': expires_at.isoformat(),
                    'is_expired': datetime.utcnow() > expires_at,
                    'days_until_expiry': max(0, (expires_at - datetime.utcnow()).days)
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get all sessions: {e}")
            return {}
    
    async def _load_sessions(self) -> Dict[str, Any]:
        """Load sessions from file."""
        try:
            if not self.session_file.exists():
                return {}
            
            with open(self.session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to load sessions: {e}")
            return {}
    
    async def _save_sessions(self, sessions: Dict[str, Any]) -> None:
        """Save sessions to file."""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save sessions: {e}")
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        try:
            all_sessions = await self.get_all_sessions()
            
            total_sessions = len(all_sessions)
            active_sessions = sum(1 for s in all_sessions.values() if not s['is_expired'])
            expired_sessions = total_sessions - active_sessions
            
            # Calculate average age
            if active_sessions > 0:
                total_age = sum(
                    (datetime.utcnow() - datetime.fromisoformat(s['saved_at'])).days
                    for s in all_sessions.values()
                    if not s['is_expired']
                )
                avg_age_days = total_age / active_sessions
            else:
                avg_age_days = 0
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'expired_sessions': expired_sessions,
                'average_age_days': avg_age_days,
                'storage_file': str(self.session_file),
                'max_session_age_days': self.max_session_age_days
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get session stats: {e}")
            return {
                'total_sessions': 0,
                'active_sessions': 0,
                'expired_sessions': 0,
                'average_age_days': 0,
                'storage_file': str(self.session_file),
                'max_session_age_days': self.max_session_age_days
            }

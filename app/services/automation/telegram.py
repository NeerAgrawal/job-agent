# -*- coding: utf-8 -*-
"""Telegram bot service for daily job digest delivery."""

import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import aiohttp
from app.core.logging import logger
from app.core.config.settings import settings


@dataclass
class TelegramMessage:
    """Telegram message structure."""
    text: str
    parse_mode: str = "Markdown"
    disable_web_page_preview: bool = False


class TelegramService:
    """Telegram bot service for sending daily job digests."""
    
    def __init__(self):
        self.logger = logger.bind(service="telegram")
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.enabled = bool(self.bot_token and self.chat_id)
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.max_message_length = 4096  # Telegram message limit
        self.retry_attempts = 3
        self.retry_delay = 2  # seconds
        
    def is_enabled(self) -> bool:
        """Check if Telegram service is properly configured."""
        return self.enabled
    
    async def send_message(self, message: TelegramMessage) -> bool:
        """Send a message to Telegram with retry logic."""
        if not self.enabled:
            self.logger.warning("Telegram service not configured, skipping message")
            return False
        
        for attempt in range(self.retry_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.api_url}/sendMessage"
                    payload = {
                        "chat_id": self.chat_id,
                        "text": message.text,
                        "parse_mode": message.parse_mode,
                        "disable_web_page_preview": message.disable_web_page_preview
                    }
                    
                    async with session.post(url, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            self.logger.info(f"Telegram message sent successfully: {result.get('message_id', 'unknown')}")
                            return True
                        else:
                            error_text = await response.text()
                            self.logger.error(f"Telegram API error (attempt {attempt + 1}): {response.status} - {error_text}")
                            
            except Exception as e:
                self.logger.error(f"Telegram send error (attempt {attempt + 1}): {e}")
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
        
        self.logger.error("Failed to send Telegram message after all retries")
        return False
    
    async def send_long_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a long message by splitting it into chunks."""
        if not self.enabled:
            return False
        
        # Split message into chunks if needed
        chunks = self._split_message(text)
        
        for i, chunk in enumerate(chunks):
            message = TelegramMessage(
                text=chunk,
                parse_mode=parse_mode,
                disable_web_page_preview=(i > 0)  # Disable preview for subsequent chunks
            )
            
            success = await self.send_message(message)
            if not success:
                self.logger.error(f"Failed to send message chunk {i + 1}/{len(chunks)}")
                return False
            
            # Add small delay between chunks to avoid rate limiting
            if i < len(chunks) - 1:
                await asyncio.sleep(1)
        
        return True
    
    def _split_message(self, text: str) -> List[str]:
        """Split a long message into chunks within Telegram limits."""
        if len(text) <= self.max_message_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        lines = text.split('\n')
        for line in lines:
            # If adding this line would exceed the limit, start a new chunk
            if len(current_chunk) + len(line) + 1 > self.max_message_length:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = line
                else:
                    # Line itself is too long, split it
                    while len(line) > self.max_message_length:
                        chunks.append(line[:self.max_message_length])
                        line = line[self.max_message_length:]
                    current_chunk = line
            else:
                if current_chunk:
                    current_chunk += '\n' + line
                else:
                    current_chunk = line
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def test_connection(self) -> bool:
        """Test Telegram bot connection."""
        if not self.enabled:
            self.logger.warning("Telegram service not configured")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/getMe"
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        bot_info = result.get('result', {})
                        self.logger.info(f"Telegram bot connected: @{bot_info.get('username', 'unknown')}")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Telegram connection test failed: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Telegram connection test error: {e}")
            return False
    
    async def send_test_message(self) -> bool:
        """Send a test message to verify Telegram delivery."""
        if not self.enabled:
            return False
        
        test_message = TelegramMessage(
            text="🤖 *PM Job Agent Test*\n\n✅ Telegram integration is working!\n📅 Daily digest delivery ready.",
            parse_mode="Markdown"
        )
        
        return await self.send_message(test_message)
    
    def format_job_digest(self, jobs: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
        """Format job digest for Telegram delivery."""
        if not jobs:
            return "📊 *Daily PM Job Digest*\n\n❌ No new jobs found today."
        
        # Header
        digest = f"📊 *Daily PM Job Digest*\n"
        digest += f"📅 {summary.get('date', 'Today')}\n"
        digest += f"🎯 {len(jobs)} top opportunities\n\n"
        
        # Jobs
        for i, job in enumerate(jobs[:10], 1):  # Max 10 jobs
            digest += f"*{i}. {job.get('title', 'Unknown')}*\n"
            digest += f"🏢 {job.get('company', 'Unknown')}\n"
            digest += f"📍 {job.get('location', 'Unknown')}\n"
            digest += f"⭐ Score: {job.get('final_score', 0):.1f}\n"
            digest += f"🎯 {job.get('pm_category', 'PM')}\n"
            
            # Salary if available
            salary = job.get('salary', 'Not specified')
            if salary and salary != 'Not specified':
                digest += f"💰 {salary}\n"
            
            # Why matched (truncated)
            reason = job.get('relevance_reason', 'No reason provided')
            if len(reason) > 50:
                reason = reason[:47] + "..."
            digest += f"📝 {reason}\n"
            
            # Direct URL
            job_url = job.get('job_url', '')
            if job_url:
                digest += f"🔗 [Apply]({job_url})\n"
            
            digest += "\n"
        
        # Footer
        digest += f"📈 *Summary*\n"
        digest += f"🔍 Jobs analyzed: {summary.get('total_analyzed', 0)}\n"
        digest += f"🎯 Shortlisted: {summary.get('shortlist_count', 0)}\n"
        digest += f"⭐ Avg score: {summary.get('avg_score', 0):.1f}\n\n"
        
        digest += "💼 *Daily PM Opportunities* - Powered by AI"
        
        return digest

"""
Универсальный клиент для транскрибации аудио через различные провайдеры
"""
import os
import logging
import aiohttp
import asyncio
from typing import Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class TranscriptionClient:
    """Клиент для транскрибации аудио через различные API"""
    
    def __init__(self):
        self.provider = os.getenv("TRANSCRIPTION_PROVIDER", "whisper_local").lower()
        
        # Локальный Whisper
        self.whisper_url = os.getenv("WHISPER_API_URL", "http://whisper:9000")
        
        # OpenAI Whisper API
        self.openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # AssemblyAI
        self.assemblyai_key = os.getenv("ASSEMBLYAI_API_KEY")
        self.assemblyai_url = "https://api.assemblyai.com/v2"
        
        logger.info(f"Initialized transcription client with provider: {self.provider}")
    
    async def transcribe(self, audio_data: bytes, filename: str = "audio.ogg") -> Optional[str]:
        """
        Транскрибирует аудио используя выбранный провайдер
        
        Args:
            audio_data: Байты аудио файла
            filename: Имя файла (для определения формата)
        
        Returns:
            Транскрибированный текст или None при ошибке
        """
        try:
            if self.provider == "openai":
                return await self._transcribe_openai(audio_data, filename)
            elif self.provider == "assemblyai":
                return await self._transcribe_assemblyai(audio_data)
            else:  # whisper_local (по умолчанию)
                return await self._transcribe_whisper_local(audio_data)
        except Exception as e:
            logger.error(f"Transcription error with {self.provider}: {e}")
            return None
    
    async def _transcribe_whisper_local(self, audio_data: bytes) -> Optional[str]:
        """Транскрибация через локальный Whisper сервер"""
        try:
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field('audio_file', audio_data, filename='audio.ogg', content_type='audio/ogg')
                
                async with session.post(
                    f"{self.whisper_url}/asr",
                    data=form,
                    params={'task': 'transcribe', 'output': 'txt'},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        text = await response.text()
                        return text.strip()
                    else:
                        logger.error(f"Whisper local error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Whisper local transcription error: {e}")
            return None
    
    async def _transcribe_openai(self, audio_data: bytes, filename: str) -> Optional[str]:
        """Транскрибация через OpenAI Whisper API"""
        if not self.openai_client:
            logger.error("OpenAI client not initialized")
            return None
        
        try:
            # Создаем временный файл-подобный объект
            from io import BytesIO
            audio_file = BytesIO(audio_data)
            audio_file.name = filename
            
            # Вызываем OpenAI Whisper API
            transcript = await self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            
            return transcript.strip() if transcript else None
        except Exception as e:
            logger.error(f"OpenAI Whisper API error: {e}")
            return None
    
    async def _transcribe_assemblyai(self, audio_data: bytes) -> Optional[str]:
        """Транскрибация через AssemblyAI"""
        if not self.assemblyai_key:
            logger.error("AssemblyAI API key not set")
            return None
        
        try:
            headers = {"authorization": self.assemblyai_key}
            
            async with aiohttp.ClientSession() as session:
                # Шаг 1: Загружаем аудио файл
                async with session.post(
                    f"{self.assemblyai_url}/upload",
                    headers=headers,
                    data=audio_data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        logger.error(f"AssemblyAI upload error: {response.status}")
                        return None
                    
                    upload_response = await response.json()
                    audio_url = upload_response.get("upload_url")
                
                if not audio_url:
                    logger.error("AssemblyAI: No upload URL received")
                    return None
                
                # Шаг 2: Запускаем транскрибацию
                async with session.post(
                    f"{self.assemblyai_url}/transcript",
                    headers=headers,
                    json={"audio_url": audio_url},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.error(f"AssemblyAI transcript request error: {response.status}")
                        return None
                    
                    transcript_response = await response.json()
                    transcript_id = transcript_response.get("id")
                
                if not transcript_id:
                    logger.error("AssemblyAI: No transcript ID received")
                    return None
                
                # Шаг 3: Ждем завершения транскрибации (polling)
                max_attempts = 60  # Максимум 60 попыток (2 минуты)
                for attempt in range(max_attempts):
                    await asyncio.sleep(2)  # Ждем 2 секунды между запросами
                    
                    async with session.get(
                        f"{self.assemblyai_url}/transcript/{transcript_id}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status != 200:
                            logger.error(f"AssemblyAI polling error: {response.status}")
                            continue
                        
                        result = await response.json()
                        status = result.get("status")
                        
                        if status == "completed":
                            return result.get("text", "").strip()
                        elif status == "error":
                            logger.error(f"AssemblyAI transcription error: {result.get('error')}")
                            return None
                        # Если status == "queued" или "processing", продолжаем ждать
                
                logger.error("AssemblyAI: Transcription timeout")
                return None
                
        except Exception as e:
            logger.error(f"AssemblyAI transcription error: {e}")
            return None
    
    def get_provider_info(self) -> dict:
        """Возвращает информацию о текущем провайдере"""
        providers = {
            "whisper_local": {
                "name": "Local Whisper",
                "cost": "Free",
                "quality": "Good",
                "speed": "Medium"
            },
            "openai": {
                "name": "OpenAI Whisper API",
                "cost": "$0.006/min",
                "quality": "Excellent",
                "speed": "Fast"
            },
            "assemblyai": {
                "name": "AssemblyAI",
                "cost": "$0.00025/sec",
                "quality": "Excellent",
                "speed": "Fast"
            }
        }
        return providers.get(self.provider, providers["whisper_local"])

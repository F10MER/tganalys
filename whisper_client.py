import aiohttp
import logging
from config import WHISPER_API_URL

logger = logging.getLogger(__name__)


async def transcribe_audio(audio_file_path: str, language: str = "ru") -> str:
    """
    Транскрибация аудио файла через локальный Whisper API
    
    Args:
        audio_file_path: Путь к аудио файлу
        language: Язык аудио (по умолчанию русский)
    
    Returns:
        Текст транскрибации
    """
    try:
        async with aiohttp.ClientSession() as session:
            with open(audio_file_path, 'rb') as audio_file:
                form_data = aiohttp.FormData()
                form_data.add_field('audio_file', audio_file, filename='voice.ogg')
                form_data.add_field('task', 'transcribe')
                form_data.add_field('language', language)
                form_data.add_field('output', 'txt')
                
                async with session.post(
                    f"{WHISPER_API_URL}/asr",
                    data=form_data,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status == 200:
                        result = await response.text()
                        logger.info(f"Transcription successful: {result[:100]}...")
                        return result.strip()
                    else:
                        error_text = await response.text()
                        logger.error(f"Whisper API error: {response.status} - {error_text}")
                        return f"Ошибка транскрибации: {response.status}"
    
    except aiohttp.ClientError as e:
        logger.error(f"Network error during transcription: {e}")
        return f"Ошибка сети: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {e}")
        return f"Неожиданная ошибка: {str(e)}"

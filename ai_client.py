"""
Универсальный AI клиент с поддержкой нескольких провайдеров:
- OpenAI (GPT-4, GPT-4o-mini)
- OpenRouter (Claude, Gemini, Llama и др.)
- AgentRouter (интеллектуальная маршрутизация)
"""

from openai import AsyncOpenAI
import logging
from typing import List, Dict
from config import (
    AI_PROVIDER,
    OPENAI_API_KEY,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    AGENTROUTER_API_KEY
)

logger = logging.getLogger(__name__)


class AIClient:
    """Универсальный клиент для работы с разными AI провайдерами"""
    
    def __init__(self):
        self.provider = AI_PROVIDER.lower()
        self.client = None
        self.model = None
        
        if self.provider == "openai":
            self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            self.model = "gpt-4o-mini"
            logger.info("Initialized OpenAI client")
            
        elif self.provider == "openrouter":
            self.client = AsyncOpenAI(
                api_key=OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1"
            )
            self.model = OPENROUTER_MODEL
            logger.info(f"Initialized OpenRouter client with model: {self.model}")
            
        elif self.provider == "agentrouter":
            self.client = AsyncOpenAI(
                api_key=AGENTROUTER_API_KEY,
                base_url="https://api.agentrouter.ai/v1"
            )
            self.model = "auto"  # AgentRouter автоматически выбирает модель
            logger.info("Initialized AgentRouter client")
            
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
    
    async def chat_completion(
        self, 
        system_prompt: str, 
        user_message: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """
        Универсальный метод для получения ответа от AI
        
        Args:
            system_prompt: Системный промпт
            user_message: Сообщение пользователя
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
        
        Returns:
            Ответ от AI
        """
        try:
            # Для OpenRouter добавляем дополнительные заголовки
            extra_headers = {}
            if self.provider == "openrouter":
                extra_headers = {
                    "HTTP-Referer": "https://github.com/F10MER/tg-analys",
                    "X-Title": "Telegram Analysis Bot"
                }
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                extra_headers=extra_headers if extra_headers else None
            )
            
            result = response.choices[0].message.content
            logger.info(f"AI completion successful via {self.provider}")
            return result
            
        except Exception as e:
            logger.error(f"AI API error ({self.provider}): {e}")
            return f"Ошибка анализа ({self.provider}): {str(e)}"


# Глобальный экземпляр клиента
ai_client = AIClient()


async def analyze_messages(messages: List[Dict], analysis_type: str = "summary") -> str:
    """
    Анализ сообщений с помощью AI
    
    Args:
        messages: Список сообщений для анализа
        analysis_type: Тип анализа (summary, insights, topics, sentiment)
    
    Returns:
        Результат анализа
    """
    # Формируем текст из сообщений
    messages_text = "\n".join([
        f"[{msg.get('message_date', 'Unknown')}] {msg.get('message_text', msg.get('transcription', ''))}"
        for msg in messages
        if msg.get('message_text') or msg.get('transcription')
    ])
    
    if not messages_text:
        return "Нет сообщений для анализа"
    
    # Определяем промпт в зависимости от типа анализа
    prompts = {
        "summary": "Создай краткое резюме этой переписки. Выдели основные темы и ключевые моменты.",
        "insights": "Проанализируй эту переписку и выдели ключевые инсайты, важные идеи и выводы.",
        "topics": "Определи основные темы, которые обсуждаются в этой переписке. Сгруппируй их по категориям.",
        "sentiment": "Проанализируй тональность этой переписки. Определи общее настроение и эмоциональную окраску.",
    }
    
    system_prompt = prompts.get(analysis_type, prompts["summary"])
    user_message = f"Переписка:\n\n{messages_text}"
    
    return await ai_client.chat_completion(system_prompt, user_message)


async def custom_analysis(messages: List[Dict], custom_prompt: str) -> str:
    """
    Кастомный анализ с пользовательским запросом
    
    Args:
        messages: Список сообщений
        custom_prompt: Пользовательский запрос
    
    Returns:
        Результат анализа
    """
    messages_text = "\n".join([
        f"{msg.get('message_text', msg.get('transcription', ''))}"
        for msg in messages
        if msg.get('message_text') or msg.get('transcription')
    ])
    
    if not messages_text:
        return "Нет сообщений для анализа"
    
    system_prompt = "Ты помощник для анализа переписок. Отвечай на вопросы пользователя на основе предоставленных сообщений."
    user_message = f"Переписка:\n\n{messages_text}\n\nВопрос: {custom_prompt}"
    
    return await ai_client.chat_completion(system_prompt, user_message)

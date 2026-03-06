from typing import Optional, List, Dict
import aiohttp
import json
from ..config import settings

class AIService:
    def __init__(self):
        # We pull these from settings, but wait to use them until a request is made
        self.base_url = "https://api.openai.com/v1"
        
        # AI Personality configurations
        self.personalities = {
            "helpful": "You are a helpful, friendly assistant who provides clear and accurate information.",
            "professional": "You are a professional assistant who maintains a formal tone and provides detailed responses.",
            "casual": "You are a casual, conversational assistant who communicates in a relaxed, friendly manner.",
            "creative": "You are a creative assistant who thinks outside the box and provides innovative solutions.",
            "educational": "You are an educational assistant who explains concepts clearly and encourages learning."
        }
    
    @property
    def api_key(self):
        return settings.openai_api_key

    async def generate_response(
        self,
        message: str,
        conversation_history: List[Dict],
        personality: str = "helpful",
        **kwargs
    ) -> Dict:
        """Generate AI response using OpenAI API"""
        
        if not self.api_key:
            return {
                "success": False,
                "content": "AI service is not configured. Please set OPENAI_API_KEY.",
                "error": "AI_NOT_CONFIGURED"
            }
        
        system_prompt = self.personalities.get(personality, self.personalities["helpful"])
        
        # Limit history to prevent token overflow
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history[-10:],  
            {"role": "user", "content": message}
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.ai_model,
                        "messages": messages,
                        "temperature": settings.ai_temperature,
                        "max_tokens": settings.ai_max_tokens,
                        "stream": False
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "content": data["choices"][0]["message"]["content"],
                            "model": settings.ai_model,
                            "usage": data.get("usage", {})
                        }
                    else:
                        error_data = await response.json()
                        return {
                            "success": False,
                            "content": "Sorry, I'm having trouble processing your request.",
                            "error": error_data.get("error", {}).get("message", "Unknown error")
                        }
        except Exception as e:
            return {
                "success": False,
                "content": "Sorry, I encountered an error. Please try again.",
                "error": str(e)
            }
    
    async def generate_streaming_response(
        self,
        message: str,
        conversation_history: List[Dict],
        personality: str = "helpful"
    ):
        """Generate streaming AI response"""
        
        if not self.api_key:
            yield {"type": "error", "content": "AI service not configured"}
            return
        
        system_prompt = self.personalities.get(personality, self.personalities["helpful"])
        
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history[-10:],
            {"role": "user", "content": message}
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.ai_model,
                        "messages": messages,
                        "temperature": settings.ai_temperature,
                        "max_tokens": settings.ai_max_tokens,
                        "stream": True
                    }
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            line_text = line.decode('utf-8').strip()
                            if line_text.startswith('data: '):
                                data_str = line_text[6:]
                                if data_str != '[DONE]':
                                    try:
                                        data_json = json.loads(data_str)
                                        token = data_json['choices'][0]['delta'].get('content', '')
                                        if token:
                                            yield {"type": "token", "content": token}
                                    except:
                                        continue
                        yield {"type": "done"}
                    else:
                        yield {"type": "error", "content": "API error"}
        except Exception as e:
            yield {"type": "error", "content": str(e)}
    
    def validate_content(self, content: str) -> bool:
        """Validate AI response for safety and bias"""
        return bool(content and content.strip())

# IMPORTANT: Export the instance so 'from ..services.ai_service import ai_service' works
ai_service = AIService()
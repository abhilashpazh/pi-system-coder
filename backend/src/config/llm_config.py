"""
LLM Configuration Module for PI System Code Generation Pipeline

Supports both Gemini and OpenAI APIs based on MODEL_TYPE environment variable.
"""

import os
import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Enumeration of supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"


class LLMConfig:
    """Configuration manager for LLM providers"""
    
    def __init__(self):
        self.provider: Optional[LLMProvider] = None
        self.api_key: Optional[str] = None
        self.model: Optional[str] = None
        self.genai = None
        self.openai = None
        
        self._initialize()
    
    def _initialize(self):
        """Initialize LLM configuration based on environment variables"""
        # Read MODEL_TYPE from environment
        model_type = os.getenv("MODEL_TYPE", "GEMINI").upper()
        
        if model_type == "GEMINI":
            self._init_gemini()
        elif model_type == "OPENAI":
            self._init_openai()
        else:
            logger.warning(f"Unknown MODEL_TYPE: {model_type}. Defaulting to GEMINI.")
            self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini API configuration"""
        try:
            from google import generativeai as genai
            self.genai = genai
            self.provider = LLMProvider.GEMINI
            
            # Get API key
            self.api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
            self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
            
            if self.api_key:
                try:
                    self.genai.configure(api_key=self.api_key)
                    logger.info("Successfully configured Gemini API")
                except Exception as e:
                    logger.error(f"Failed to configure Gemini API: {e}")
            else:
                logger.warning("No Gemini API key found in environment variables")
                
        except ImportError:
            logger.error("google-generativeai not installed. Cannot use Gemini API.")
    
    def _init_openai(self):
        """Initialize OpenAI API configuration"""
        try:
            import openai
            self.openai = openai
            self.provider = LLMProvider.OPENAI
            
            # Get API key
            self.api_key = os.getenv("OPENAI_API_KEY", "")
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
            
            if self.api_key:
                self.openai.api_key = self.api_key
                logger.info("Successfully configured OpenAI API")
            else:
                logger.warning("No OpenAI API key found in environment variables")
                
        except ImportError:
            logger.error("openai not installed. Cannot use OpenAI API.")
    
    def generate_content(
        self, 
        prompt: str, 
        temperature: float = 0.7, 
        max_tokens: int = 2000
    ) -> str:
        """
        Generate content using the configured LLM provider.
        
        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text content
            
        Raises:
            Exception: If LLM is not configured or generation fails
        """
        if self.provider == LLMProvider.GEMINI:
            return self._generate_gemini(prompt, temperature, max_tokens)
        elif self.provider == LLMProvider.OPENAI:
            return self._generate_openai(prompt, temperature, max_tokens)
        else:
            raise Exception("No LLM provider configured")
    
    def _generate_gemini(
        self, 
        prompt: str, 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """Generate content using Gemini API"""
        if not self.genai:
            raise Exception("Gemini API not configured")
        
        model = self.genai.GenerativeModel(self.model)
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
        )
        return response.text.strip()
    
    def _generate_openai(
        self, 
        prompt: str, 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """Generate content using OpenAI API"""
        if not self.openai:
            raise Exception("OpenAI API not configured")
        
        # For OpenAI, we need to use the chat completions endpoint
        response = self.openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()


# Global LLM configuration instance
_llm_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    """
    Get the global LLM configuration instance.
    Creates it if it doesn't exist.
    
    Returns:
        LLMConfig instance
    """
    global _llm_config
    if _llm_config is None:
        _llm_config = LLMConfig()
    return _llm_config


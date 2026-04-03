import os
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

def summarize_error(service_name: str, message: str, raw_error: str) -> str:
    """Uses Gemini API to interpret the raw error and provide a human summary."""
    fallback_key = os.getenv("GEMINI_API_KEY_FALLBACK")
    if not fallback_key:
        logger.error("No GEMINI_API_KEY_FALLBACK set.")
        return "No AI summary available (API key missing)."
        
    try:
        genai.configure(api_key=fallback_key)
        # using flash as it's cheap and fast enough for summarization
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=
            "You are an expert DevOps engineer monitoring a production system. "
            "You will be given an error log. Briefly summarize the root cause in 1-2 sentences "
            "and suggest an immediate action. Do not use markdown formatting like asterisks or bold text."
        )
        
        prompt = f"Service: {service_name}\nHeadline: {message}\nRaw Stacktrace:\n{raw_error}"
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Failed to summarize error with Gemini: {e}")
        return f"AI summarization failed. Check raw error."

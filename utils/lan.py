from deep_translator import GoogleTranslator
import streamlit as st

def t(text: str) -> str:
    """Translate static UI text into user’s chosen language."""
    lang = st.session_state.get('lang', 'en')
    if lang == 'en':
        return text
    try:
        return GoogleTranslator(text, source='en', target=lang).translate(text)
    except Exception:
        return text

def back_to_english(text: str) -> str:
    """Convert user input (any language) into English for LLM processing."""
    lang = st.session_state.get('lang', 'en')
    if lang == 'en':
        return text
    try:
        return GoogleTranslator(source=lang, target='en').translate(text)
    except Exception:
        return text

def to_user_language(text: str) -> str:
    """Convert LLM’s English output into user’s chosen language."""
    lang = st.session_state.get('lang', 'en')
    if lang == 'en':
        return text
    try:
        return GoogleTranslator(source='en', target=lang).translate(text)
    except Exception:
        return text

from config.db_connection import get_connection
import streamlit as st
from langchain_huggingface import HuggingFaceEndpoint,ChatHuggingFace 
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from deep_translator import GoogleTranslator
from utils.lan import to_user_language,back_to_english,t 

load_dotenv()
conn=get_connection()
cursor=conn.cursor()
llm=HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.3",
                        task="text-generation")
model=ChatHuggingFace(llm=llm)



languages = {
    'Afrikaans': 'af',
    'Albanian': 'sq',
    'Amharic': 'am',
    'Arabic': 'ar',
    'Armenian': 'hy',
    'Azerbaijani': 'az',
    'Basque': 'eu',
    'Belarusian': 'be',
    'Bengali': 'bn',
    'Bosnian': 'bs',
    'Bulgarian': 'bg',
    'Catalan': 'ca',
    'Cebuano': 'ceb',
    'Chinese (Simplified)': 'zh-CN',
    'Chinese (Traditional)': 'zh-TW',
    'Corsican': 'co',
    'Croatian': 'hr',
    'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'English': 'en',
    'Esperanto': 'eo',
    'Estonian': 'et',
    'Filipino': 'tl',
    'Finnish': 'fi',
    'French': 'fr',
    'Frisian': 'fy',
    'Galician': 'gl',
    'Georgian': 'ka',
    'German': 'de',
    'Greek': 'el',
    'Gujarati': 'gu',
    'Haitian Creole': 'ht',
    'Hausa': 'ha',
    'Hawaiian': 'haw',
    'Hebrew': 'he',
    'Hindi': 'hi',
    'Hmong': 'hmn',
    'Hungarian': 'hu',
    'Icelandic': 'is',
    'Igbo': 'ig',
    'Indonesian': 'id',
    'Irish': 'ga',
    'Italian': 'it',
    'Japanese': 'ja',
    'Javanese': 'jw',
    'Kannada': 'kn',
    'Kazakh': 'kk',
    'Khmer': 'km',
    'Korean': 'ko',
    'Kurdish (Kurmanji)': 'ku',
    'Kyrgyz': 'ky',
    'Lao': 'lo',
    'Latin': 'la',
    'Latvian': 'lv',
    'Lithuanian': 'lt',
    'Luxembourgish': 'lb',
    'Macedonian': 'mk',
    'Malagasy': 'mg',
    'Malay': 'ms',
    'Malayalam': 'ml',
    'Maltese': 'mt',
    'Maori': 'mi',
    'Marathi': 'mr',
    'Mongolian': 'mn',
    'Myanmar (Burmese)': 'my',
    'Nepali': 'ne',
    'Norwegian': 'no',
    'Pashto': 'ps',
    'Persian': 'fa',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'Punjabi': 'pa',
    'Romanian': 'ro',
    'Russian': 'ru',
    'Samoan': 'sm',
    'Scots Gaelic': 'gd',
    'Serbian': 'sr',
    'Sesotho': 'st',
    'Shona': 'sn',
    'Sindhi': 'sd',
    'Sinhala': 'si',
    'Slovak': 'sk',
    'Slovenian': 'sl',
    'Somali': 'so',
    'Spanish': 'es',
    'Sundanese': 'su',
    'Swahili': 'sw',
    'Swedish': 'sv',
    'Tajik': 'tg',
    'Tamil': 'ta',
    'Telugu': 'te',
    'Thai': 'th',
    'Turkish': 'tr',
    'Ukrainian': 'uk',
    'Urdu': 'ur',
    'Uzbek': 'uz',
    'Vietnamese': 'vi',
    'Welsh': 'cy',
    'Xhosa': 'xh',
    'Yiddish': 'yi',
    'Yoruba': 'yo',
    'Zulu': 'zu'
}


#Load local FAISS index
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.load_local("faiss_index", embeddings=embeddings,allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})  # top 3 chunks


# def t(text: str) -> str:
#     """Translate static UI text into user’s chosen language."""
#     lang = st.session_state.get('lang', 'en')
#     if lang == 'en':
#         return text
#     try:
#         return GoogleTranslator(text, source='en', target=lang).translate(text)
#     except Exception:
#         return text

# def back_to_english(text: str) -> str:
#     """Convert user input (any language) into English for LLM processing."""
#     lang = st.session_state.get('lang', 'en')
#     if lang == 'en':
#         return text
#     try:
#         return GoogleTranslator(source=lang, target='en').translate(text)
#     except Exception:
#         return text

# def to_user_language(text: str) -> str:
#     """Convert LLM’s English output into user’s chosen language."""
#     lang = st.session_state.get('lang', 'en')
#     if lang == 'en':
#         return text
#     try:
#         return GoogleTranslator(source='en', target=lang).translate(text)
#     except Exception:
#         return text



def get_relevant_guidelines(user_prompt):
    # Retrieve top chunks based on user prompt
    docs = retriever.get_relevant_documents(user_prompt)
    guideline_texts = "\n\n".join([doc.page_content for doc in docs])
    return guideline_texts

def logout_button():
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

def get_latest_summaries(user_id):
    query = """
    SELECT r1.report_type, r1.report_data
    FROM reports r1
    INNER JOIN (
        SELECT report_type, MAX(report_date) AS max_date
        FROM reports
        WHERE user_id = ?
        GROUP BY report_type
    ) r2
    ON r1.report_type = r2.report_type AND r1.report_date = r2.max_date
    WHERE r1.user_id = ?
    """
    cursor.execute(query, (user_id, user_id))
    rows = cursor.fetchall()
    return {row[0]: row[1] for row in rows}

def get_user_health_profile(user_id):
    query = """
    SELECT weight, height, blood_group, blood_pressure, heart_rate, chronic_diseases,
           family_history, allergies, medications, diet, water_intake, sleep, smoking, alcohol
    FROM user_health_profile
    WHERE user_id = ?
    """
    cursor.execute(query, (user_id,))
    row = cursor.fetchone()
    if not row:
        return None
    keys = ['weight', 'height', 'blood_group', 'blood_pressure', 'heart_rate',
            'chronic_diseases', 'family_history', 'allergies', 'medications',
            'diet', 'water_intake', 'sleep', 'smoking', 'alcohol']
    return dict(zip(keys, row))

def generate_diet_prompt(health_profile, summaries):
    summary_str = "\n\n".join([f"{k} Report Summary:\n{v}" for k, v in summaries.items()])
    health_str = "\n".join([f"{k.replace('_', ' ').capitalize()}: {v}" for k, v in health_profile.items()])
    
    # 🔥 New: Retrieve guidelines
    query_for_rag = f"{health_str}\n\n{summary_str}"
    guidelines = get_relevant_guidelines(query_for_rag)

    prompt = f"""You are a medical diet assistant.

Use the following clinical diet guidelines to give recommendations:

=== CLINICAL GUIDELINES ===
{guidelines}

=== USER MEDICAL REPORT SUMMARIES ===
{summary_str}

=== USER HEALTH PROFILE ===
{health_str}

Now, generate a **detailed daily diet plan** for:
- Breakfast
- Lunch
- Snacks
- Dinner

For each meal, list recommended foods and explain briefly why they are good. 
Also mention **foods to avoid** and **foods to prefer** with reasoning.

Finally, at the very end, provide a **concise summary table** of the meal plan without explanations. 
The table should only include the recommended foods for each meal, structured like this:

| Meal      | Recommended Foods |
|-----------|------------------|
| Breakfast | ...              |
| Lunch     | ...              |
| Snacks    | ...              |
| Dinner    | ...              |

Make sure the recommendations are medically sound and personalized based on the above inputs.
"""

    return prompt


# -------------------------
# Streamlit UI
# -------------------------

def main():
 st.set_page_config(page_title="Personlized Diet Suggestion", page_icon="🍽️", layout="wide")
 
 st.sidebar.subheader("🌐 " + "Choose Language")
 lang_choice = st.sidebar.selectbox("Language", list(languages.keys()))
 st.session_state['lang'] = languages[lang_choice]

 st.title(to_user_language("🩺 Personalized Diet Suggestion"))

 user_id = st.session_state.get("user_id", None)
 if not user_id:
    st.warning(to_user_language("User not logged in. Please login to view your diet suggestions."))
    return

 if st.button(to_user_language("Generate Diet Plan")):
    health_profile = get_user_health_profile(user_id)
    if not health_profile:
        st.error(to_user_language("User health profile not found."))
    else:
        summaries = get_latest_summaries(user_id)
        if not summaries:
            st.warning(to_user_language("No report summaries found for this user."))
        else:
            prompt = generate_diet_prompt(health_profile, summaries)
            with st.spinner(to_user_language("Generating diet suggestion...")):
                response = model.invoke(prompt)
            
            st.subheader(to_user_language("Recommended Diet Plan 🍽️"))
            st.markdown(to_user_language(response.content))



if __name__ == "__main__":
    main()
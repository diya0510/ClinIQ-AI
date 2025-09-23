from config.db_connection import get_connection
import streamlit as st
from langchain_huggingface import HuggingFaceEndpoint,ChatHuggingFace
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from utils.lan import to_user_language,back_to_english,t


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


load_dotenv()
conn=get_connection()
cursor=conn.cursor()
llm=HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.3",
                        task="text-generation")
model=ChatHuggingFace(llm=llm)


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

def generate_guidance_prompt(health_profile, summaries):
    summary_str = "\n\n".join([f"{k} Report Summary:\n{v}" for k, v in summaries.items()])
    health_str = "\n".join([f"{k.replace('_', ' ').capitalize()}: {v}" for k, v in health_profile.items()])

    prompt = f"""
You are an expert medical advisor and preventive healthcare assistant.

A user has shared their detailed medical report summaries and personal health profile. Your task is to perform the following:

1. **Risk Prediction**:
   - Analyze the user's medical reports and health profile to identify potential **future diseases or complications** they might be at risk for.
   - Give reasoning based on data like age,gender,blood pressure, heart rate, chronic diseases, and report summaries.

2. **Preventive Measures & Lifestyle Recommendations**:
   - For each risk, suggest **preventive actions**, **foods to avoid**, **dietary changes**, **hydration**, and **stress management techniques**.
   - Mention daily/weekly **exercise routines** suitable for the person’s current condition (consider age, existing diseases, weight, etc.).
   - Specify how much sleep they should ideally get and if any habits like smoking/alcohol should be reduced or stopped.

3. **Consequences if not followed**:
   - Based on the current data, what can happen in the future if the suggested plan is not followed (brief summary).

Use the sections below to extract the necessary information.

=== USER MEDICAL REPORT SUMMARIES ===
{summary_str}

=== USER HEALTH PROFILE ===
{health_str}

Generate a complete, actionable and structured health advisory with clear headings. Be medically grounded yet easy to understand for the user.
"""

    return prompt

# -------------------------
# Streamlit UI
# -------------------------

def main():
 
 st.set_page_config(page_title="Personlized Future Guidance", page_icon="🧑‍⚕️", layout="wide")

 st.sidebar.subheader("🌐 " + "Choose Language")
 lang_choice = st.sidebar.selectbox("Language", list(languages.keys()))
 st.session_state['lang'] = languages[lang_choice]

 st.title(to_user_language("🧑‍⚕️ Personalized Future Guidance"))

 user_id = st.session_state.get("user_id", None)
 if not user_id:
    st.warning(to_user_language("User not logged in. Please login to view your diet suggestions."))
    return

 if st.button(to_user_language("Generate Future Guidance")):
    health_profile = get_user_health_profile(user_id)
    if not health_profile:
        st.error(to_user_language("User health profile not found."))
    else:
        summaries = get_latest_summaries(user_id)
        if not summaries:
            st.warning(to_user_language("No report summaries found for this user."))
        else:
            prompt = generate_guidance_prompt(health_profile, summaries)
            with st.spinner(to_user_language("Generating Future Guidance...")):
                response = model.invoke(prompt)
            st.subheader(to_user_language("Personalized Future Guidance"))
            st.markdown(to_user_language(response.content))



if __name__ == "__main__":
    main()
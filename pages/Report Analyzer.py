from langchain_huggingface import ChatHuggingFace,HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import streamlit as st
import tempfile
from config.db_connection import get_connection
from langchain_community.document_loaders import PyPDFLoader  
from langchain_core.output_parsers import StrOutputParser
from utils.ocr import extract_text_from_report,generate_summary

load_dotenv()
conn=get_connection()
cursor=conn.cursor()
llm=HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.3",
                        task="text-generation")
model=ChatHuggingFace(llm=llm)


def summarizer(path):
    text=extract_text_from_report(path)
    # summary=generate_summary(text)
    prompt_template=PromptTemplate(template="""You are a medical insights assistant.  
Your task is to analyze the following medical report and generate structured insights.  
Be precise, medically relevant, and avoid guessing beyond the data provided.  
Output must be clear, structured, and divided into the following sections:  

Medical Report:
{{medical_report_text}}

Instructions:  
1. **Summary of Key Findings**  
   - Highlight main observations from the report  
   - Mention abnormal values with reference ranges if given  
   - Flag any critical results  

2. **Doctor-Oriented Interpretation**  
   - Provide possible clinical implications of the findings  
   - Link abnormal results to potential medical conditions  
   - Mention clinical significance  

3. **Patient-Friendly Explanation**  
   - Translate medical terms into simple, easy-to-understand language  
   - Clearly state whether results are normal, borderline, or concerning  
   - Give context in everyday terms (e.g., diet, lifestyle, symptoms)  

4. **Next Steps / Recommendations**  
   - Suggest possible further tests, follow-ups, or precautions  
   - Include lifestyle or preventive suggestions if applicable  
   - Indicate urgency (routine / follow-up soon / immediate attention)  

Make sure explanations are concise, medically sound, and well-structured.  
""",input_variables=["medical_report_text"])
    
    prompt=prompt_template.format(input={"medical_report_text":text})
    results=model.invoke(prompt)
    return results.content

def main():
    st.set_page_config(page_title="Report Analyzer", page_icon="📊", layout="wide")
    st.title("📊 Report Analyzer")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded_file is not None:
        st.success(f"✅ Uploaded: {uploaded_file.name}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_path = temp_file.name
        
        with st.spinner("🧠 Analyzing the report and generating summary..."):
            try:
                summary = summarizer(temp_path)  # ✅ Call summarizer with temp_path
                st.markdown("### 📝 Summary & Suggestions:")
                st.write(summary)
            except Exception as e:
                st.error(f"❌ Error during summarization: {str(e)}")

main()
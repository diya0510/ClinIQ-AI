import re
import easyocr
from pdf2image import convert_from_path
import numpy as np
from PIL import Image
import os
from config.db_connection import get_connection
from datetime import datetime
from langchain.prompts import PromptTemplate
import json
from langchain_huggingface import ChatHuggingFace,HuggingFaceEndpoint
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate

load_dotenv()


def generate_summary(report_data):
    llm=HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.3",
                        task="text-generation")
    model=ChatHuggingFace(llm=llm)
    summary_prompt = PromptTemplate.from_template("""
    You are a medical assistant AI.

    The following is the raw medical report texts from a user. Summarize the overall findings, trends, or any red flags. Provide a clean and professional medical summary.

    Reports:
    {report_data}

    --- Medical Summary ---
    """)
    summary_chain = summary_prompt | model
    summary_response = summary_chain.invoke({"report_data": report_data})
    summary_text = summary_response.content.strip()

    return summary_text


def extract_text_from_report(pdf_path):
    # Convert PDF to list of PIL images
    pages = convert_from_path(pdf_path,
                              poppler_path = r"C:\\Users\\Diya\Downloads\\Release-24.08.0-0\\poppler-24.08.0\\Library\\bin")

    reader = easyocr.Reader(['en'])
    all_text = []

    for i, page in enumerate(pages):
        # Convert PIL image to numpy array
        image_np = np.array(page)

        # Use EasyOCR to extract text
        result = reader.readtext(image_np, detail=0)
        page_text = " ".join(result)

        all_text.append(f"--- Page {i+1} ---\n{page_text}")

    return "\n\n".join(all_text)



def report_insertion(user_id,ocr_text,summary):
    conn=get_connection()
    cursor=conn.cursor()
    llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.2",temperature=0.5,
    max_length=1024,
    task="text-generation"
    )

    model=ChatHuggingFace(llm=llm)
    prompt = PromptTemplate(
        input_variables=["ocr"],
        template="""
You are a medical report data extractor.

Given this OCR medical report text:
{ocr}

Extract the following JSON object:

{{
  "report_type": "...",
  "report_date": "YYYY-MM-DD",
  "parameters": [
    {{
      "parameter_name": "...",
      "parameter_value": float,
      "unit": "...",
      "low_range": float,
      "high_range": float
    }},
    ...
  ]
}}
Only return valid JSON. Do not add comments or explanations.
"""
    )
    try:
        # 3. Call LLM
        formatted_input = prompt.format(ocr=ocr_text)
        result = model.invoke(formatted_input)

        # 4. Clean and parse JSON
        text_output = result.content
        json_data = json.loads(text_output)

        report_type = json_data['report_type']
        report_date = json_data['report_date']
        full_text = ocr_text
        # 5. Insert into reports table
        cursor.execute("""
            INSERT INTO reports (user_id, report_type, report_date, report_data)
            OUTPUT INSERTED.report_id
            VALUES (?, ?, ?, ?)
        """, (user_id, report_type, report_date, summary))
        report_id = cursor.fetchone()[0]

        # 6. Insert each parameter
        for param in json_data['parameters']:
            cursor.execute("""
                INSERT INTO report_parameters (
                    report_id, parameter_name, paramter_value, unit, low_range, high_range
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                param['parameter_name'],
                param['parameter_value'],
                param['unit'],
                param['low_range'],
                param['high_range']
            ))

        conn.commit()
        print("✅ Report and parameters inserted successfully.")

    except Exception as e:
        print("❌ Error processing report:", str(e))
        conn.rollback()
    finally:
        cursor.close()
        conn.close()



# Example usage
def extract_and_store(user_id,path):
    pdf_path=path
    text=extract_text_from_report(pdf_path)
    summary=generate_summary(text)
    report_insertion(user_id,text,summary)




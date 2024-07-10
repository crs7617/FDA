import streamlit as st
import PyPDF2
import google.generativeai as genai
import io
import csv
import tabula
import pandas as pd
import json

# Configure Gemini API
genai.configure(api_key='AIzaSyDl7dAKwIs2KvwzC9x5o6quwgUGcdX3p6k')
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_tables_from_pdf(pdf_file):
    # Extract tables from PDF
    tables = tabula.read_pdf(pdf_file, pages='all', multiple_tables=True)
    
    # Convert tables to CSV
    csv_data = []
    for i, table in enumerate(tables):
        csv_buffer = io.StringIO()
        table.to_csv(csv_buffer, index=False)
        csv_data.append(csv_buffer.getvalue())
    
    return csv_data

def csv_to_dict(csv_string):
    reader = csv.DictReader(io.StringIO(csv_string))
    return [row for row in reader]

st.title('Financial Document Analyzer')

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    csv_data = extract_tables_from_pdf(uploaded_file)
    
    if not csv_data:
        st.error("No tables could be extracted from the document.")
    else:
        st.subheader('Extracted CSV Data')
        for i, csv_string in enumerate(csv_data):
            st.write(f"Table {i+1}:")
            df = pd.read_csv(io.StringIO(csv_string))
            st.dataframe(df)
        
        # Convert CSV to dict for easier processing
        financial_data = [csv_to_dict(csv_string) for csv_string in csv_data]
        
        # Add a text input for the user to enter a custom prompt
        user_prompt = st.text_input("Enter your financial analysis question:", 
                                    "Calculate the total assets and liabilities, then provide a brief analysis of the company's financial health.")
        
        # Add a button to trigger the AI analysis
        if st.button("Run AI Analysis"):
            # Use Gemini API for analysis and calculations
            prompt = f"""
            Given the following financial data extracted from CSV tables:
            {json.dumps(financial_data, indent=2)}
            
            Please perform the following task:
            {user_prompt}
            
            Provide your answer in JSON format with two keys:
            1. 'calculations': containing any numerical results
            2. 'analysis': containing your text analysis
            
            Ensure all numerical values in the 'calculations' are actual numbers, not strings.
            """
            
            try:
                response = model.generate_content(prompt)
                
                # Parse the JSON response
                result = json.loads(response.text)
                
                st.subheader('AI Analysis Results')
                
                if 'calculations' in result:
                    st.subheader('Calculations')
                    st.json(result['calculations'])
                
                if 'analysis' in result:
                    st.subheader('Analysis')
                    st.write(result['analysis'])
                
            except json.JSONDecodeError:
                st.error("The AI response was not in the expected JSON format. Here's the raw response:")
                st.write(response.text)
            except Exception as e:
                st.error(f"An error occurred during AI analysis: {str(e)}")
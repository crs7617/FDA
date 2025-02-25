import streamlit as st
import PyPDF2
import re
import google.generativeai as genai
import io

# Configure Gemini API
genai.configure(api_key='AIzaSyDl7dAKwIs2KvwzC9x5o6quwgUGcdX3p6k')
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_financial_data(text):
    data = {}

    assets_match = re.search(r'Total Assets:?\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)', text, re.IGNORECASE)
    liabilities_match = re.search(r'Total Liabilities:?\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)', text, re.IGNORECASE)
    current_liabilities_match = re.search(r'Current Liabilities:?\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)', text, re.IGNORECASE)
    net_cash_match = re.search(r'Net cash generated from operating activities\s*\(A\):?\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)', text, re.IGNORECASE)
    total_income_match = re.search(r'Total comprehensive income for the year:?\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)', text, re.IGNORECASE)
    
    if assets_match:
        data['total_assets'] = float(assets_match.group(1).replace(',', ''))
    else:
        st.warning("Couldn't find Total Assets in the document.")
        data['total_assets'] = 0

    if liabilities_match:
        data['total_liabilities'] = float(liabilities_match.group(1).replace(',', ''))
    else:
        st.warning("Couldn't find Total Liabilities in the document.")
        data['total_liabilities'] = 0

    if current_liabilities_match:
        data['current_liabilities'] = float(current_liabilities_match.group(1).replace(',', ''))
    else:
        st.warning("Couldn't find Current Liabilities in the document.")
        data['current_liabilities'] = 0

    if net_cash_match:
        data['net_cash_from_operations'] = float(net_cash_match.group(1).replace(',', ''))
    else:
        st.warning("Couldn't find Net cash generated from operating activities (A) in the document.")
        data['net_cash_from_operations'] = 0

    if total_income_match:
        data['total_comprehensive_income'] = float(total_income_match.group(1).replace(',', ''))
    else:
        st.warning("Couldn't find Total comprehensive income for the year in the document.")
        data['total_comprehensive_income'] = 0

    return data

def calculate_financials(data):
    equity = data['total_assets'] - data['total_liabilities']
    try:
        debt_to_equity_ratio = data['total_liabilities'] / equity if equity != 0 else None
    except ZeroDivisionError:
        debt_to_equity_ratio = None
        st.warning("Cannot calculate debt-to-equity ratio (division by zero).")
    
    cash_vs_income_difference = data['net_cash_from_operations'] - data['total_comprehensive_income']
    
    return {
        'equity': equity,
        'debt_to_equity_ratio': debt_to_equity_ratio,
        'cash_vs_income_difference': cash_vs_income_difference
    }

st.title('Financial Document Analyzer')

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    
    text = extract_text_from_pdf(io.BytesIO(bytes_data))
    
    st.subheader('Extracted Text')
    st.text(text)
    
    financial_data = extract_financial_data(text)
    
    if financial_data['total_assets'] == 0 and financial_data['total_liabilities'] == 0:
        st.error("No financial data could be extracted from the document.")
    else:
        calculations = calculate_financials(financial_data)
        
        st.subheader('Extracted Financial Data')
        st.json(financial_data)
        
        st.subheader('Calculations')
        st.json(calculations)
        
        st.subheader('Cash Flow vs Income Analysis')
        if calculations['cash_vs_income_difference'] > 0:
            st.write(f"Net cash from operations exceeds total comprehensive income by ${calculations['cash_vs_income_difference']:.2f}")
        elif calculations['cash_vs_income_difference'] < 0:
            st.write(f"Total comprehensive income exceeds net cash from operations by ${-calculations['cash_vs_income_difference']:.2f}")
        else:
            st.write("Net cash from operations equals total comprehensive income.")
        
        prompt = f"""Given the following financial data: {financial_data}, {calculations}, 
        and the cash flow vs income analysis, provide a brief analysis of the company's financial health. 
        Consider the relationship between net cash from operations and total comprehensive income."""
        response = model.generate_content(prompt)
        
        st.subheader('AI Analysis')
        st.write(response.text)
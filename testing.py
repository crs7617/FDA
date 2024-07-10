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
    patterns = {
        'total_assets': r'Total Assets:?\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)',
        'total_liabilities': r'Total Liabilities:?\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)',
        'cash_balance': r'Net Cash generated from operating activities (A):?\s*\$?(\(?\d+(?:,\d{3})*(?:\.\d+)?\)?)',
        'current_liabilities': r'Current Liabilities:?\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)',
        'total_profits': r'Total comprehensive income for the year:?\s*\$?(\(?\d+(?:,\d{3})*(?:\.\d+)?\)?)'
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '')
            try:
                if value.startswith('(') and value.endswith(')'):
                    data[key] = -float(value[1:-1])
                elif value.startswith('('):  # Handle cases where the closing parenthesis is missing
                    data[key] = -float(value[1:])
                else:
                    data[key] = float(value)
            except ValueError:
                st.warning(f"Couldn't convert {key.replace('_', ' ').title()} value to a number: {value}")
                data[key] = 0
        else:
            if key == 'cash_balance':
                st.warning("Couldn't find Net Cash generated from operating activities in the document.")
            elif key == 'total_profits':
                st.warning("Couldn't find Total comprehensive income for the year in the document.")
            else:
                st.warning(f"Couldn't find {key.replace('_', ' ').title()} in the document.")
            data[key] = 0
    return data
     
def calculate_financials(data):
    equity = data['total_assets'] - data['total_liabilities']
    try:
        debt_to_equity_ratio = data['total_liabilities'] / equity if equity != 0 else None
    except ZeroDivisionError:
        debt_to_equity_ratio = None
        st.warning("Cannot calculate debt-to-equity ratio (division by zero).")
    
    net_cash_flow = data['cash_balance'] - data['current_liabilities']
    
    return {
        'equity': equity,
        'debt_to_equity_ratio': debt_to_equity_ratio,
        'net_cash_flow': net_cash_flow
    }
def compare_net_cash_flow_to_profits(net_cash_flow, total_profits):
    if net_cash_flow < 0 and total_profits < 0:
        return f"Both net cash flow (${net_cash_flow:.2f}) and total profits (${total_profits:.2f}) are negative."
    elif net_cash_flow < 0:
        return f"Net cash flow is negative (${net_cash_flow:.2f}), while total profits are ${total_profits:.2f}."
    elif total_profits < 0:
        return f"Total profits are negative (${total_profits:.2f}), while net cash flow is ${net_cash_flow:.2f}."
    
    difference = net_cash_flow - total_profits
    if net_cash_flow > total_profits:
        return f"Net cash flow (${net_cash_flow:.2f}) is ${difference:.2f} higher than total profits (${total_profits:.2f})."
    elif net_cash_flow < total_profits:
        return f"Net cash flow (${net_cash_flow:.2f}) is ${-difference:.2f} lower than total profits (${total_profits:.2f})."
    else:
        return f"Net cash flow is equal to total profits (${net_cash_flow:.2f})."
        
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
        
        st.subheader('Net Cash Flow Analysis')
        net_cash_flow_comparison = compare_net_cash_flow_to_profits(calculations['net_cash_flow'], financial_data['total_profits'])
        st.write(net_cash_flow_comparison)
        
        prompt = f"Given the following financial data: {financial_data}, {calculations}, and the net cash flow analysis: {net_cash_flow_comparison}, provide a brief analysis of the company's financial health."
        response = model.generate_content(prompt)
        
        st.subheader('AI Analysis')
        st.write(response.text)
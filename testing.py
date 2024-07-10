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
    cash_balance_match = re.search(r'Net Cash generated from operating activities:?\s*\$?(\(?\d+(?:,\d{3})*(?:\.\d+)?\)?)', text, re.IGNORECASE)
    current_liabilities_match = re.search(r'Current Liabilities:?\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)', text, re.IGNORECASE)
    total_profits_match = re.search(r'Total comprehensive income for the year:?\s*\$?(\(?\d+(?:,\d{3})*(?:\.\d+)?\)?)', text, re.IGNORECASE)
    
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

    if cash_balance_match:
        cash_balance = cash_balance_match.group(1).replace(',', '')
        if cash_balance.startswith('(') and cash_balance.endswith(')'):
            data['cash_balance'] = -float(cash_balance[1:-1])
        else:
            data['cash_balance'] = float(cash_balance)
    else:
        st.warning("Couldn't find Net Cash generated from operating activities in the document.")
        data['cash_balance'] = 0

    if current_liabilities_match:
        data['current_liabilities'] = float(current_liabilities_match.group(1).replace(',', ''))
    else:
        st.warning("Couldn't find Current Liabilities in the document.")
        data['current_liabilities'] = 0

    if total_profits_match:
        total_profits = total_profits_match.group(1).replace(',', '')
        if total_profits.startswith('(') and total_profits.endswith(')'):
            data['total_profits'] = -float(total_profits[1:-1])
        else:
            data['total_profits'] = float(total_profits)
    else:
        st.warning("Couldn't find Total comprehensive income for the year in the document.")
        data['total_profits'] = 0

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
    if net_cash_flow < 0 or total_profits < 0:
        return "Cannot compare net cash flow to profits due to negative values."
    
    difference = net_cash_flow - total_profits
    if net_cash_flow > total_profits:
        return f"Net cash flow is ${difference:.2f} higher than total profits."
    elif net_cash_flow < total_profits:
        return f"Net cash flow is ${-difference:.2f} lower than total profits."
    else:
        return "Net cash flow is equal to total profits."

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
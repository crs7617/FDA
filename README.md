# Financial Document Analyzer

A Streamlit application to extract and analyze financial data from PDF documents using Python and AI.

## Features

- **PDF Upload**: Upload a PDF file to extract financial data.
- **Text Extraction**: Extract text from PDF files.
- **Financial Data Extraction**: Identify key financial metrics such as Total Assets, Total Liabilities, Current Liabilities, Net Cash from Operations, and Total Comprehensive Income.
- **Financial Calculations**: Calculate equity, debt-to-equity ratio, and cash vs income difference.
- **AI Analysis**: Generate a brief analysis of the company's financial health using the Google Generative AI model.

## Installation

To run this application, you'll need to have Python installed. You can install the required dependencies using pip:

```bash
pip install streamlit PyPDF2 google.generativeai

Usage
Clone the repository:

bash
Copy code
git clone https://github.com/yourusername/financial-document-analyzer.git
cd financial-document-analyzer
Run the Streamlit application:

bash
Copy code
streamlit run app.py
Upload a PDF file containing financial data.

View the extracted text and financial data, and see the AI-generated analysis.

Limitations
The application currently works only for a limited number of balance sheets and financial documents.
This is a basic prototype and may not handle all types of financial documents or data formats.
Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

License
This project is licensed under the MIT License.

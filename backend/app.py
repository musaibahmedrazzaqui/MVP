import os
import json
import tempfile
import csv
import base64
import pytesseract
import boto3
from PIL import Image
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import openai
from textractprettyprinter.t_pretty_print_expense import get_string
from textractprettyprinter.t_pretty_print_expense import Textract_Expense_Pretty_Print, Pretty_Print_Table_Format
from dotenv import load_dotenv
app = Flask(__name__)
CORS(app)

# Load OpenAI API key from the config file
with open('config.txt', 'r') as config_file:
    api_key = config_file.read().strip()

openai.api_key = api_key
# Load AWS credentials from environment variables
load_dotenv()
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")

# Initialize AWS Textract client with credentials
textract = boto3.client("textract", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,region_name=aws_region)

# Define a function to perform OCR using Tesseract
def perform_ocr(image_path):
    try:
        # Perform OCR using Tesseract on the provided image
        ocr_result = pytesseract.image_to_string(Image.open(image_path), lang="eng")

        return ocr_result
    except Exception as e:
        print("OCR Error:", str(e))
        return None

# Define a function to generate text using OpenAI's GPT-3
def generate_text(ocr_text):
    try:
        # Create the initial prompt with the OCR text
        initial_prompt = f"""
Extract the following information from the table:
- Invoice Number (Inv Number)
- Vendor Name
- Client Number
- Total Value
Then for each product, 
- Product Name
- UPC (Universal Product Code)
- Quantity (QTY)
- Price per Case

OCR Text:
{ocr_text}

Please provide the extracted data as accurately as possible. Provide Vendor Name & Client Number from the top. Then Invoice Number, then each product's name and UPC, then
along with its price. Remember numbers in the format 02/223/22 are bogus and mean nothing.
Finally provide Total at the end of your response. 
"""

        # Send the initial prompt to ChatGPT
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=initial_prompt,
            max_tokens=700  # Adjust the max tokens as needed for longer responses
        )

        chat_gpt_response = response.choices[0].text.strip()
        return chat_gpt_response

    except Exception as e:
        print("GPT-3 Error:", str(e))
        return None

def save_uploaded_image_to_temp_file(image_file):
  """Saves an uploaded image file to a temporary file.

  Args:
    image_file: A file object containing the image.

  Returns:
    The path to the temporary file.
  """

  temp_image_path = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
  image_file.save(temp_image_path)
  return temp_image_path

@app.route('/upload/receipts', methods=['POST'])
def upload_receipts():
    try:
        # Check if the 'file' field is present in the POST request
        if 'file' not in request.files:
            return jsonify({'error': 'No image provided'}), 400

        image_file = request.files['file']

        # Check if the file is not empty
        if image_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Save the uploaded image to a temporary file
        temp_image_path = "temp_image.png"
        image_file.save(temp_image_path)

        # Perform OCR on the uploaded image using Tesseract
        ocr_text = perform_ocr(temp_image_path)

        # Generate text using GPT-3 based on the OCR result
        gpt3_response = generate_text(ocr_text)

        # Remove the temporary image file
        os.remove(temp_image_path)

        if gpt3_response:
            # Save the GPT-3 response to a text file
            response_file = "gpt3_response.txt"
            with open(response_file, 'w') as file:
                file.write(gpt3_response)

            # Return the generated text file as a response
            return send_file(response_file, as_attachment=True), 200

        else:
            return jsonify({'error': 'GPT-3 processing failed'}), 500

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/upload/invoices', methods=['POST'])
def upload_invoices():
    try:
        # Check if the 'file' field is present in the POST request
        if 'file' not in request.files:
            return jsonify({'error': 'No image provided'}), 400

        image_file = request.files['file']

        # Check if the file is not empty
        if image_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Save the uploaded image to a temporary file
        #temp_image_path = "temp_image.png"
        #image_file.save(temp_image_path)
        temp_image_path = save_uploaded_image_to_temp_file(image_file)
        
        # Use AWS Textract to analyze the image and extract tables
        response = textract.analyze_expense(
            Document={
                'Bytes': open(temp_image_path, 'rb').read()
            }
        )
        json_file_path = "textract_response.json"

# Write the Textract response to the JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(response, json_file, indent=4)
        
        # Extract table data from the Textract response
        pretty_printed_string = get_string(textract_json=response, output_type=[Textract_Expense_Pretty_Print.SUMMARY, Textract_Expense_Pretty_Print.LINEITEMGROUPS], table_format=Pretty_Print_Table_Format.csv)
        pretty_file = "pretty_file.csv"  # Change the file extension to .csv
        with open(pretty_file, 'w', newline='') as file:  # Set newline parameter to ensure proper line endings in CSV
            file.write(pretty_printed_string)
        #print(pretty_printed_string)
        # Remove the temporary image file
        #os.remove(temp_image_path)
        
        # Generate a CSV file from the extracted table data
        #csv_data = "\n".join([",".join(row) for row in tables])
        filename='invoice.csv'
        response = send_file(
            pretty_file,
            as_attachment=True,  # This forces the browser to download the fil  # Use attachment_filename to specify the filename
            mimetype='text/csv'
        )
    
    # Set the Content-Disposition header to ensure the correct filename
        #response.headers["Content-Disposition"] = f"attachment; filename='{filename}'"
    
        return response

    

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': 'Internal server error'}), 500
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

import os
import json
import tempfile
import csv
import base64
from doctr.io import DocumentFile
from PIL import Image
import cv2
import numpy as np
from doctr.models import ocr_predictor
import boto3
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
model = ocr_predictor(pretrained=True)
# Initialize AWS Textract client with credentials
textract = boto3.client("textract", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,region_name=aws_region)

# Define a function to perform OCR using Tesseract

def preprocess_image(image_path):
    # Load the image
    img = cv2.imread(image_path)

    # Perform preprocessing steps such as resizing, noise reduction, or other enhancements
    # Example preprocessing steps:
    # Resize the image
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=7.0, tileGridSize=(50, 50))
    cl_img = clahe.apply(gray)  # 'gray' is the grayscale image

    # Applying thresholding on the CLAHE enhanced image
    _, threshold = cv2.threshold(cl_img, 120, 255, cv2.THRESH_BINARY)
    # Apply thresholding or other image enhancement techniques as needed
    #_, threshold = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # Save the preprocessed image to a temporary file
    temp_preprocessed_image_path = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
    cv2.imwrite(temp_preprocessed_image_path, threshold)

    return temp_preprocessed_image_path

def read_text_file(file_path):
    try:
        with open(file_path, 'r') as file:
            ocr_results = file.read()
            return ocr_results
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
def using_doctr(image_path):
    doc = DocumentFile.from_images(image_path)
    result = model(doc)
    json_output = result.export()
    json_file_path = "feed.json"
    with open(json_file_path, 'w') as json_file:
        json.dump(json_output, json_file, indent=4)

    print(f"JSON data has been saved to {json_file_path}")
        # Read the JSON data from test.json
    with open('feed.json', 'r') as json_file:
        json_data = json.load(json_file)

    # Open a text file for writing
    with open('results.txt', 'w') as txt_file:
    # Initialize a dictionary to store words grouped by y coordinates
        words_by_y = {}

    # Iterate through pages
        for page in json_data['pages']:
        # Iterate through blocks in each page
            for block in page['blocks']:
            # Iterate through lines in each block
                for line in block['lines']:
                # Sort words by their y0 coordinate
                    words_in_line = sorted(line['words'], key=lambda w: w['geometry'][0][1])

                # Initialize a list to store words with the same y coordinates
                    words_with_equal_y = []

                # Iterate through words in the line
                    for word in words_in_line:
                        y_coord = round(word['geometry'][0][1], 2)  # Round y coordinate to 1 decimal place
                        if y_coord not in words_by_y:
                            words_by_y[y_coord] = []
                        words_by_y[y_coord].append(word)

    # Sort the words by y coordinate and write them to the text file with y coordinates
        sorted_y_coords = sorted(words_by_y.keys())
        for y_coord in sorted_y_coords:
            words_with_equal_y = words_by_y[y_coord]
            line_text = ' '.join(f'{w["value"]}' for w in words_with_equal_y)
            txt_file.write(line_text + '\n\n')
# Define a function to generate text using ChatGPT
def generate_text(ocr_text):
    try:
        # Create the initial prompt with the OCR text
        initial_prompt = f"""
Act like an Expert Data Analyst. Your job is to analyze data from raw text of invoices and provide key value pairs.
Extract the following information from the raw Text provided:
- Invoice Number (Inv Number)
- Vendor Name
- Client Number
- Total Value
Then for each product, 
- Product Name
- UPC (Universal Product Code)
- Quantity (QTY)
- Price per Case(this can also be named amount!)

Raw Text - line by line:
{ocr_text}

After analysing the raw text, Please provide the key value pairs as accurately as possible. 
Please format your response with respect to it's conversion to CSVs. 
"""

        # Send the initial prompt to ChatGPT
        response = openai.Completion.create(
             engine="text-davinci-003",
             prompt=initial_prompt,
             max_tokens=2048   #Adjust the max tokens as needed for longer responses
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
        temp_image_path = "temp_image.png"
        image_file.save(temp_image_path)
        temp_preprocessed_image_path = preprocess_image(temp_image_path)
        # Perform OCR on the uploaded image using Tesseract
        #ocr_text = perform_ocr(temp_image_path)
        print(temp_preprocessed_image_path)
        using_doctr(temp_preprocessed_image_path)
        file_path='results.txt'
        ocr_text=read_text_file(file_path)
        with open('ocr_text.txt', 'w') as file:
                file.write(ocr_text)
        # Generate text using GPT-4 based on the OCR result
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
@app.route('/',methods=['GET'])
def intialize():
    return jsonify({'MSG':'server started'})

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
        #temp_image_path = "temp_image.png"
        #image_file.save(temp_image_path)
        temp_image_path = save_uploaded_image_to_temp_file(image_file)
        temp_preprocessed_image_path = preprocess_image(temp_image_path)
        print(temp_preprocessed_image_path)
        # Use AWS Textract to analyze the image and extract tables
        response = textract.analyze_expense(
            Document={
                'Bytes': open(temp_preprocessed_image_path, 'rb').read()
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

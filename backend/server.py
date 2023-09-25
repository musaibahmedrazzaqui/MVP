from flask import Flask, jsonify, request
import logging
import requests
import io
from paddleocr import PaddleOCR

app = Flask(__name__)
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize PaddleOCR
ocr = PaddleOCR()

@app.route('/upload/receipts', methods=['POST'])
def upload_image():
    try:
        # Get the uploaded image file from the request
        uploaded_file = request.files['image']

        if not uploaded_file:
            return jsonify({'error': 'No image provided'}), 400

        # Read the image data
        image_data = uploaded_file.read()

        # Perform OCR using PaddleOCR
        result = ocr.ocr(image_data)

        # Extract recognized text from the OCR result
        ocr_text = '\n'.join([line[1][0] for line in result[0]])
        logger.info(ocr_text)
        return jsonify({'ocrResult': ocr_text}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Define a simple route
@app.route('/')
def hello():
    logger.debug("Debug message")
    logger.info("Info message")
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)

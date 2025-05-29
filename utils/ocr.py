import os
import cv2
import base64
import json
import pytesseract
import numpy as np
import logging
from PIL import Image
from openai import OpenAI

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def extract_text_from_image(image_path):
    """
    Extract text from a prescription image using OCR
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Extracted text from the image
    """
    try:
        # Read the image using OpenCV
        image = cv2.imread(image_path)
        if image is None:
            logging.error(f"Failed to load image from {image_path}")
            return "Error: Could not read image"
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to preprocess the image
        _, threshold = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Noise removal using median blur
        processed_img = cv2.medianBlur(threshold, 3)
        
        try:
            # Try to use Tesseract OCR first
            pytesseract.get_tesseract_version()
            text = pytesseract.image_to_string(processed_img)
            logging.debug(f"Successfully extracted text with Tesseract from image: {image_path}")
        except Exception as e:
            logging.warning(f"Tesseract not available or failed: {str(e)}")
            # If Tesseract fails, try OpenAI vision API
            text = analyze_prescription_with_ai(image_path)
            
        return text
    
    except Exception as e:
        logging.error(f"Error during OCR processing: {str(e)}")
        # If traditional OCR fails, try AI-based analysis
        return analyze_prescription_with_ai(image_path)

def analyze_prescription_with_ai(image_path):
    """
    Use OpenAI's vision capabilities to analyze prescription images
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Extracted text and analysis from the image
    """
    try:
        # Read image and convert to base64
        with open(image_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Call OpenAI API with the image
        response = openai_client.chat.completions.create(
            model="gpt-4o", # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "system",
                    "content": "You are a pharmaceutical assistant specializing in prescription analysis. "
                            "Extract all medications, dosages, frequencies, and special instructions from the "
                            "prescription image. Format your response as clear text with each medication on a new line. "
                            "Include patient information if visible."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this prescription image and extract all medications, dosages, and instructions:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        # Return the AI analysis
        analysis_text = response.choices[0].message.content
        logging.info("Successfully analyzed prescription with AI")
        return analysis_text
        
    except Exception as e:
        logging.error(f"Error during AI prescription analysis: {str(e)}")
        # Inform the user about the error rather than using fallbacks
        return f"Unable to analyze prescription image. Error: {str(e)}"
        
def extract_medications_from_text(text):
    """
    Extract medication information from prescription text
    
    Args:
        text (str): Text extracted from prescription image
        
    Returns:
        list: List of dictionaries with medication info
    """
    try:
        # Use AI to extract structured medication information
        response = openai_client.chat.completions.create(
            model="gpt-4o", # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "system",
                    "content": "You are a pharmaceutical assistant specializing in medication extraction. "
                            "Extract medications from the prescription text into structured data."
                },
                {
                    "role": "user",
                    "content": f"Extract all medications from this prescription text. Return a JSON object with a 'medications' "
                            f"array where each item has 'name', 'dosage', 'frequency', and 'instructions' fields:\n\n{text}"
                }
            ],
            response_format={"type": "json_object"}
        )
        
        # Get content from response
        content = response.choices[0].message.content
        
        # Parse JSON response if content exists
        if content is not None:
            try:
                result = json.loads(content)
                
                if isinstance(result, dict) and "medications" in result:
                    return result["medications"]
                    
                # If the model returned a JSON array directly instead of an object
                if isinstance(result, list):
                    return result
                    
                # If it returned an object with a different key
                for key, value in result.items():
                    if isinstance(value, list):
                        return value
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {e}")
        
        # If we reach here, either content was empty or didn't have expected structure
        logging.warning("AI returned unexpected format for medications")
        
        # Default empty list if nothing worked        
        return []
            
    except Exception as e:
        logging.error(f"Error extracting medications from text: {str(e)}")
        return []

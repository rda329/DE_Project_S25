import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np

def preprocess_image(image):
    # Convert to grayscale
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    
    # Increase resolution (magnification) - resize by a factor
    scale_factor = 3  # Increase this if needed (2 means double the size)
    gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
    
    # Apply additional preprocessing
    # 1. Thresholding to get binary image
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # 2. Denoising
    denoised = cv2.fastNlMeansDenoising(thresh, h=30)
    
    return denoised

def extract_raw_text(pdf_path, output_txt_path=None):
    # Convert PDF to images
    images = convert_from_path(pdf_path)
    
    full_text = ""
    
    for img in images:
        # Preprocess the image
        processed_img = preprocess_image(img)
        
        # Extract text from each processed image
        text = pytesseract.image_to_string(processed_img)
        full_text += text + "\n\n"  # Add spacing between pages
    
    # Save to text file if output path is provided
    if output_txt_path:
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
    
    return full_text

# Example usage
pdf_path = r"WebScraping\ScreenCaptures\yahoo_page_1.pdf"
output_txt_path = "extracted_text.txt"  # Output text file
raw_text = extract_raw_text(pdf_path, output_txt_path)
print("Text extraction completed!")
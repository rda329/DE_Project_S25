import pytesseract
from pdf2image import convert_from_path

def extract_raw_text(pdf_path, output_txt_path=None):
    # Convert PDF to images
    images = convert_from_path(pdf_path)
    
    full_text = ""
    
    for img in images:
        # Extract text from each image
        text = pytesseract.image_to_string(img)
        full_text += text + "\n\n"  # Add spacing between pages
    
    # Save to text file if output path is provided
    if output_txt_path:
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
    
    return full_text

# Example usage
pdf_path = r"C:\Users\rubie\Desktop\DE_Project_S25\ScreenCaptures\duckduckgo_page_1.pdf"
output_txt_path = "extracted_text.txt"  # Output text file
raw_text = extract_raw_text(pdf_path, output_txt_path)
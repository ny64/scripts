import os
import sys
import json
import base64
import urllib.request
from pathlib import Path
from pdf2image import convert_from_path

# Configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 4096

# Image format: PNG is best for slides (lossless, good for text/diagrams)
IMAGE_FORMAT = "PNG"
IMAGE_DPI = 300  # High DPI for better text recognition


def pdf_to_images(pdf_path, output_dir=None):
    """
    Convert PDF pages to images.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save images (optional, for debugging)
    
    Returns:
        List of PIL Image objects
    """
    print(f"Converting PDF to images: {pdf_path}")
    images = convert_from_path(pdf_path, dpi=IMAGE_DPI, fmt=IMAGE_FORMAT.lower())
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        for i, image in enumerate(images):
            image.save(output_dir / f"page_{i+1}.png")
    
    print(f"Converted {len(images)} pages")
    return images


def image_to_base64(image):
    """
    Convert PIL Image to base64 string.
    
    Args:
        image: PIL Image object
    
    Returns:
        Base64 encoded string
    """
    from io import BytesIO
    buffered = BytesIO()
    image.save(buffered, format=IMAGE_FORMAT)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def transcribe_image(image_base64, page_num):
    """
    Transcribe image to markdown/latex using Anthropic API.
    
    Args:
        image_base64: Base64 encoded image
        page_num: Page number (for display purposes)
    
    Returns:
        Transcribed text in markdown/latex format
    """
    print(f"Transcribing page {page_num}...")
    
    # Prompt designed to get direct output without preamble
    prompt = """Transcribe this slide to markdown/latex format. Include all text, equations, diagrams descriptions, and structure. Use LaTeX for mathematical equations (inline: $...$, display: $$...$$). Preserve the hierarchical structure with appropriate headers. Output ONLY the transcription without any introductory text or explanations."""
    
    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": f"image/{IMAGE_FORMAT.lower()}",
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json"
    }
    
    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        # Extract the text content from the response
        if 'content' in result and len(result['content']) > 0:
            return result['content'][0]['text']
        else:
            return f"Error: Unexpected response format for page {page_num}"
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return f"Error transcribing page {page_num}: {e.code} - {error_body}"
    except Exception as e:
        return f"Error transcribing page {page_num}: {str(e)}"


def process_pdf(pdf_path, output_path=None):
    """
    Process entire PDF: convert to images and transcribe each page.
    
    Args:
        pdf_path: Path to input PDF file
        output_path: Path to output markdown file (optional)
    """
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Convert PDF to images
    images = pdf_to_images(pdf_path)
    
    # Process each page
    all_transcriptions = []
    for i, image in enumerate(images, start=1):
        print(f"\nProcessing page {i}/{len(images)}")
        image_base64 = image_to_base64(image)
        transcription = transcribe_image(image_base64, i)
        
        # Add page separator
        page_content = f"# Page {i}\n\n{transcription}\n\n{'='*80}\n"
        all_transcriptions.append(page_content)
        
        # Print to console
        print(f"Page {i} transcription completed")
    
    # Combine all transcriptions
    full_output = "\n".join(all_transcriptions)
    
    # Save to file if output path specified
    if output_path:
        output_path = Path(output_path)
        output_path.write_text(full_output, encoding='utf-8')
        print(f"\nOutput saved to: {output_path}")
    else:
        # Default output file name
        output_path = pdf_path.with_suffix('.md')
        output_path.write_text(full_output, encoding='utf-8')
        print(f"\nOutput saved to: {output_path}")
    
    return full_output


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <pdf_file> [output_file]")
        print("\nExample: python script.py slides.pdf output.md")
        print("\nMake sure to set ANTHROPIC_API_KEY environment variable")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_pdf(pdf_file, output_file)
    print("\nProcessing complete!")


if __name__ == "__main__":
    main()


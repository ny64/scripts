import os
import sys
import json
import base64
import urllib.request
from pathlib import Path

# Configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 4096

def image_to_base64(image_path):
    """
    Convert image file to base64 string.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Base64 encoded string and media type
    """
    image_path = Path(image_path)
    
    # Determine media type from extension
    ext = image_path.suffix.lower()
    media_type_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    
    media_type = media_type_map.get(ext, 'image/png')
    
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    return image_data, media_type

def transcribe_image(image_path, output_path=None):
    """
    Transcribe image to markdown/latex using Anthropic API.
    
    Args:
        image_path: Path to the image file
        output_path: Path to output markdown file (optional)
    
    Returns:
        Transcribed text in markdown/latex format
    """
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    print(f"Converting image to base64: {image_path}")
    image_base64, media_type = image_to_base64(image_path)
    
    print("Transcribing image...")
    
    # Prompt designed to get direct output without preamble
    prompt = """Transcribe this slide/page to markdown/latex format. Include all text, equations, diagrams descriptions, and structure. Use LaTeX for mathematical equations (inline: $...$, display: $$...$$). Preserve the hierarchical structure with appropriate headers. Output ONLY the transcription without any introductory text or explanations."""
    
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
                            "media_type": media_type,
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
            transcription = result['content'][0]['text']
            
            # Save to file if output path specified
            if output_path:
                output_path = Path(output_path)
                output_path.write_text(transcription, encoding='utf-8')
                print(f"\nOutput saved to: {output_path}")
            else:
                # Default output file name
                output_path = image_path.with_suffix('.md')
                output_path.write_text(transcription, encoding='utf-8')
                print(f"\nOutput saved to: {output_path}")
            
            # Also print to console
            print("\n" + "="*80)
            print("TRANSCRIPTION:")
            print("="*80)
            print(transcription)
            print("="*80)
            
            return transcription
        else:
            error_msg = "Error: Unexpected response format"
            print(error_msg)
            return error_msg
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        error_msg = f"Error transcribing image: {e.code} - {error_body}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error transcribing image: {str(e)}"
        print(error_msg)
        return error_msg

def main():
    if len(sys.argv) < 2:
        print("Usage: python image2markdown.py <image_file> [output_file]")
        print("\nExample: python image2markdown.py slide.png output.md")
        print("\nSupported formats: PNG, JPG, JPEG, GIF, WEBP")
        print("\nMake sure to set ANTHROPIC_API_KEY environment variable")
        sys.exit(1)
    
    image_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    transcribe_image(image_file, output_file)
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()

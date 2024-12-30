from fastapi import APIRouter, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

router = APIRouter()

# Constants
UPLOAD_DIR = "uploads"
WATERMARKED_DIR = "watermarked"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def get_safe_filename(filename: str) -> str:
    """Generate a safe filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base, ext = os.path.splitext(filename)
    return f"{base}_{timestamp}{ext}"

@router.post("/watermark")
async def add_watermark(
    file: UploadFile,
    text: str = Form(...),
    opacity: int = Form(128),
    font_size: int = Form(40),
    watermark_count: int = Form(1)
):
    """Add watermark to an image."""
    # Validate file type
    if not file.filename or file.filename.split('.')[-1].lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")
   
    # Generate safe filenames
    safe_filename = get_safe_filename(file.filename)
    input_path = os.path.join(UPLOAD_DIR, safe_filename)
    output_path = os.path.join(WATERMARKED_DIR, f"watermarked_{safe_filename}")
   
    # Ensure directories exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(WATERMARKED_DIR, exist_ok=True)
   
    # Save uploaded file
    with open(input_path, "wb") as f:
        f.write(await file.read())
   
    try:
        # Open and prepare image
        with Image.open(input_path).convert("RGBA") as base:
            # Create watermark layer
            txt = Image.new("RGBA", base.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt)
           
            # Create font
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
           
            # Calculate text position
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
           
            # Limit watermark count
            watermark_count = max(1, min(watermark_count, 10))
           
            # Calculate positions for multiple watermarks
            positions = []
            for i in range(watermark_count):
                # More intelligent positioning
                x = int((base.width - text_width) * (0.2 + 0.3 * (i % 3)))
                y = int((base.height - text_height) * (0.2 + 0.3 * (i // 3)))
                positions.append((x, y))
           
            # Draw watermarks
            for pos in positions:
                draw.text(
                    pos,
                    text,
                    font=font,
                    fill=(255, 255, 255, opacity)
                )
           
            # Combine watermark with original image
            watermarked = Image.alpha_composite(base, txt)
            watermarked.convert("RGB").save(output_path, "JPEG", quality=95)
           
            return FileResponse(
                output_path,
                media_type="image/jpeg",
                filename=f"watermarked_{safe_filename}"
            )
   
    finally:
        # Remove input file
        if os.path.exists(input_path):
            os.remove(input_path)
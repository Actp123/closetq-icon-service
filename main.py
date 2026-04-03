import io
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from PIL import Image
import rembg

app = FastAPI()

@app.post("/icon")
async def process_icon(file: UploadFile = File(...)):
    """
    Process an uploaded image:
    - Remove background using rembg
    - Auto-crop the clothing item
    - Center on white background
    - Resize to 512x512
    - Return PNG bytes
    """
    # Read uploaded file
    contents = await file.read()
    input_image = Image.open(io.BytesIO(contents)).convert("RGBA")
    
    # Remove background
    output = rembg.remove(input_image)
    
    # Auto-crop to content
    bbox = output.getbbox()
    if bbox:
        cropped = output.crop(bbox)
    else:
        cropped = output
    
    # Get dimensions and calculate padding for centering on 512x512
    width, height = cropped.size
    max_dim = max(width, height)
    
    # Scale to fit in 512x512 with padding
    scale = 512 / max_dim if max_dim > 0 else 1
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    scaled = cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create white background and center the image
    final = Image.new("RGBA", (512, 512), (255, 255, 255, 255))
    x_offset = (512 - new_width) // 2
    y_offset = (512 - new_height) // 2
    final.paste(scaled, (x_offset, y_offset), scaled)
    
    # Convert to RGB for PNG output (remove alpha)
    final_rgb = Image.new("RGB", (512, 512), (255, 255, 255))
    final_rgb.paste(final, (0, 0), final)
    
    # Return PNG bytes
    output_buffer = io.BytesIO()
    final_rgb.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    
    return StreamingResponse(
        iter([output_buffer.getvalue()]),
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=icon.png"}
    )

@app.get("/health")
async def health():
    return {"status": "ok"}

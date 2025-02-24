# vision.py
import torch
import numpy as np
from io import BytesIO
from PIL import Image

# Load YOLOv5 model from torch.hub globally.
# Note: On first run, this will download the model weights.
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
model.eval()  # set model to evaluation mode

def count_products_in_image(image_bytes):
    """
    Count products in an image using YOLOv5.
    
    Args:
        image_bytes (bytes): The uploaded image in bytes.
        
    Returns:
        count (int): Estimated number of detected objects.
        processed_image (PIL.Image): Image with detections drawn for visualization.
    
    Note: For production, fine‑tune the model on your product images and filter detections
          to only count your target objects.
    """
    # Load image from bytes
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    # Convert image to numpy array
    img_np = np.array(image)
    
    # Perform inference
    results = model(img_np)
    
    # Render annotated image (results.render() returns list of numpy arrays)
    annotated_image_np = results.render()[0]
    annotated_image = Image.fromarray(annotated_image_np)
    
    # Extract detections from results.xyxy[0] (each detection: [x1, y1, x2, y2, conf, class])
    detections = results.xyxy[0]
    # For demonstration, count all detections.
    count = len(detections)
    
    return count, annotated_image

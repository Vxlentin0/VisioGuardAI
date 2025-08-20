from PIL import Image
from transformers import DetrImageProcessor, DetrForObjectDetection
import torch
import io

processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")

def detect_objects(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)

    target_sizes = torch.tensor([image.size[::-1]])
    results = processor.post_process_object_detection(outputs, target_sizes=target_sizes)[0]

    threshold = 0.9
    boxes = [
        {
            "label": model.config.id2label[int(score["label"])],
            "score": float(score["score"]),
            "box": [round(coord, 2) for coord in score["box"]]
        }
        for score in results if score["score"] > threshold
    ]
    return boxes
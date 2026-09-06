"""
Smart Shelf YOLOv8 Custom Training Script (Section 12 & 21)
Enables fine-tuning YOLOv8n on custom annotated retail shelf datasets.
"""

import os
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smartshelf.train")


def train_yolo(data_yaml: str, epochs: int = 25, img_size: int = 640, batch_size: int = 16, weights: str = "yolov8n.pt"):
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("Ultralytics library not installed. Please run: pip install ultralytics")
        return

    logger.info(f"Loading base weights: {weights}")
    model = YOLO(weights)

    logger.info(f"Starting fine-tuning on dataset configuration: {data_yaml}")
    logger.info(f"Parameters: epochs={epochs}, img_size={img_size}, batch_size={batch_size}")

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=img_size,
        batch=batch_size,
        project="models/custom",
        name="smart_shelf_retail",
        save=True,
        verbose=True
    )

    logger.info("Custom model training complete. Artifacts saved in models/custom/smart_shelf_retail/")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train custom YOLO model on shelf dataset")
    parser.add_argument("--data", type=str, default="datasets/dataset.yaml", help="Path to dataset.yaml")
    parser.add_argument("--epochs", type=int, default=25, help="Number of training epochs")
    parser.add_argument("--weights", type=str, default="yolov8n.pt", help="Initial weights checkpoint")
    args = parser.parse_args()

    train_yolo(args.data, epochs=args.epochs, weights=args.weights)

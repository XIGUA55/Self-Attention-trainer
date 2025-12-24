# PyTorch Training Script for YOLOv8
# Architecture: Transformer / CNN
# Base Ops: 15000

import torch
from cyber_focus import Trainer

def main():
    print("Initializing distributed backend...")
    model = Trainer(model_name="YOLOv8")
    model.fit()

if __name__ == "__main__":
    main()

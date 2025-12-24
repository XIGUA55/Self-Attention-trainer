# PyTorch Training Script for YOLOv8-Nano
# Architecture: Transformer / CNN
# Base Ops: 1200

import torch
from cyber_focus import Trainer

def main():
    print("Initializing distributed backend...")
    model = Trainer(model_name="YOLOv8-Nano")
    model.fit()

if __name__ == "__main__":
    main()

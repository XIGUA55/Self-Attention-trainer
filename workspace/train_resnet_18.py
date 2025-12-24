# PyTorch Training Script for ResNet-18
# Architecture: Transformer / CNN
# Base Ops: 800

import torch
from cyber_focus import Trainer

def main():
    print("Initializing distributed backend...")
    model = Trainer(model_name="ResNet-18")
    model.fit()

if __name__ == "__main__":
    main()

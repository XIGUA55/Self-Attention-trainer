# PyTorch Training Script for BERT-Base
# Architecture: Transformer / CNN
# Base Ops: 4500

import torch
from cyber_focus import Trainer

def main():
    print("Initializing distributed backend...")
    model = Trainer(model_name="BERT-Base")
    model.fit()

if __name__ == "__main__":
    main()

# PyTorch Training Script for GPT-2
# Architecture: Transformer / CNN
# Base Ops: 120000

import torch
from cyber_focus import Trainer

def main():
    print("Initializing distributed backend...")
    model = Trainer(model_name="GPT-2")
    model.fit()

if __name__ == "__main__":
    main()

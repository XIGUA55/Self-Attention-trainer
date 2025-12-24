# PyTorch Training Script for GPT-3-Small
# Architecture: Transformer / CNN
# Base Ops: 300000

import torch
from cyber_focus import Trainer

def main():
    print("Initializing distributed backend...")
    model = Trainer(model_name="GPT-3-Small")
    model.fit()

if __name__ == "__main__":
    main()

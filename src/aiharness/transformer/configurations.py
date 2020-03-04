from dataclasses import dataclass
from aiharness import harnessutils as utils
from aiharness.inspector import Inspector

import argparse


@dataclass()
class ModelConfig:
    pretrained_bert: bool = True
    attention_dropout: float = 0.1
    num_attention_heads: int = 16
    hidden_size: int = 1024
    intermediate_size: int = 4096
    num_layers: int = 24
    layernorm_epsilon: float = 1e-5
    hidden_dropout: float = 0.1
    max_position_embeddings: int = 512
    vocab_size: int = 30522


class Configurations:
    model: ModelConfig = ModelConfig()

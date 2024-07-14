import os


def load_models_from_config(config_file="models.conf"):
    config_path = os.path.join(os.path.dirname(__file__), config_file)

    try:
        with open(config_path) as f:
            models = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Config file {config_file} not found. Using default models.")
        models = [
            "llama3:latest",
            "mistral:latest",
            "tinyllama:latest",
        ]

    return models


LLM_MODELS = load_models_from_config()
DEFAULT_LLM_MODEL = LLM_MODELS[4] if len(LLM_MODELS) > 4 else LLM_MODELS[-1]

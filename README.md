# Chat Circuit

![](docs/img.png)

**Brief overview**

<blockquote class="twitter-tweet" data-media-max-width="560"><p lang="en" dir="ltr">🔍 Added a small feature to zoom in using mouse selection. Handy for looking at deep branches #ChatCircuit<br><br>👉 <a href="https://twitter.com/namuan_twt/status/1826620308507558383?ref_src=twsrc%5Etfw">August 22, 2024</a></blockquote>

### Short demos

**Re-run all nodes in a branch**
<blockquote class="twitter-tweet" data-media-max-width="560"><p lang="en" dir="ltr">Chat Circuit now makes it possible to re-run a branch of your conversation with LLM with a different prompt. It supports all local LLMs running on @ollama <br>💾 👉 <a href="https://twitter.com/namuan_twt/status/1820796082248458377?ref_src=twsrc%5Etfw">August 6, 2024</a></blockquote>

**Generate Follow up questions**
<blockquote class="twitter-tweet" data-media-max-width="560"><p lang="en" dir="ltr">Implemented this idea in chat circuit. Here is a quick demo of the application along with generating follow up questions using #LLM <a href="https://twitter.com/namuan_twt/status/1825849039348289574?ref_src=twsrc%5Etfw">August 20, 2024</a></blockquote>

**Zoom in/out**
<blockquote class="twitter-tweet" data-media-max-width="560"><p lang="en" dir="ltr">🔍 Added a small feature to zoom in using mouse selection. Handy for looking at deep branches #ChatCircuit<br><br>👉 <a href="https://twitter.com/namuan_twt/status/1826620308507558383?ref_src=twsrc%5Etfw">August 22, 2024</a></blockquote>

**Minimap Support**

<blockquote class="twitter-tweet" data-media-max-width="560"><p lang="en" dir="ltr">#ChatCircuit Added a mini-map with the help of Sonnet 3.5 in @poe_platform. <br><br>Would have taken me days if not weeks to do it without any help. 🙏<br><br>~ 99% of code is written by Claude <a href="https://twitter.com/namuan_twt/status/1838913082510225442?ref_src=twsrc%5Etfw">September 25, 2024</a></blockquote>

**Export to JSON Canvas Document**

<blockquote class="twitter-tweet" data-media-max-width="560"><p lang="en" dir="ltr">Added option to export to #JSON Canvas document that can be imported by any supported application like @obsdmd / @KinopioClub<br><br>👉 <a href="https://twitter.com/namuan_twt/status/1839415117353570323?ref_src=twsrc%5Etfw">September 26, 2024</a></blockquote>

### Features

**Multi-Branch Conversations**
Create and manage multiple conversation branches seamlessly.

**Contextual Forking**
Fork conversation branches with accurate context retention.

### Editor Features

**Save and Load Diagrams**

**Undo and Redo**

**Zoom and Pan**

![](docs/view-options.png)

**Re-run nodes in a branch**

It is possible to re-run all the nodes in a branch after changing the prompt it any node in the list.

![](docs/re-run-button.png)

### Supported Providers

Chat Circuit supports multiple LLM providers through a flexible, provider-based architecture:

#### Local Providers (OpenAI-compatible APIs)

| Provider | Default Endpoint | Environment Variable | Description |
|----------|------------------|---------------------|-------------|
| **Ollama** | `http://localhost:11434` | `OLLAMA_API_BASE` | Popular local LLM server |
| **LMStudio** | `http://localhost:1234/v1` | `LMSTUDIO_API_BASE` | Desktop app for running LLMs locally |
| **KoboldCpp** | `http://localhost:5001/v1` | `KOBOLDCPP_API_BASE` | Lightweight local inference server |

#### Cloud Providers

| Provider | Endpoint | Environment Variable | Description |
|----------|----------|---------------------|-------------|
| **OpenRouter** | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` | Access to multiple cloud LLMs (requires API key) |

All providers are auto-discovered at startup. The app will work with any combination of available providers.

**Quick Start:**

1. Start your preferred local provider (Ollama, LMStudio, or KoboldCpp)
2. Launch Chat Circuit - models will be automatically discovered
3. Select a model from the dropdown in any conversation node

**Configuring Provider Endpoints:**

You can configure provider endpoints in two ways:

1. **Via Configuration Dialog (Recommended)**: 
   - Open Configuration via menu: `Configuration > API Keys...` or press `Ctrl+,`
   - Enter custom endpoints for Ollama, LMStudio, and KoboldCpp
   - Settings are saved automatically and persist across sessions

2. **Via Environment Variables** (fallback if not set in UI):
   ```bash
   # Example: Run with custom endpoints via environment variables
   OLLAMA_API_BASE="http://192.168.1.100:11434" \
   LMSTUDIO_API_BASE="http://localhost:1234/v1" \
   KOBOLDCPP_API_BASE="http://localhost:5001/v1" \
   python3 main.py
   ```

See `provider-config.example.sh` for more detailed configuration examples.

**Configuration Priority**: UI Settings > Environment Variables > Defaults

### Running the Application

To run this application, follow these steps:

**Install dependencies**

```shell
python3 -m pip install -r requirements.txt
```

**Run application**
```shell
python3 main.py
```

### Model Discovery

This application discovers available LLM models dynamically from multiple providers:

- **Ollama**: Discovers local models from `Ollama` running at `http://localhost:11434` (configurable via `OLLAMA_API_BASE` env var).
- **LMStudio**: Discovers local models from `LMStudio` running at `http://localhost:1234` (configurable via `LMSTUDIO_API_BASE` env var).
- **KoboldCpp**: Discovers local models from `KoboldCpp` running at `http://localhost:5001` (configurable via `KOBOLDCPP_API_BASE` env var).
- **OpenRouter**: Discovers free models from `OpenRouter` when `OPENROUTER_API_KEY` is set (via Configuration dialog or env var).

All local providers (Ollama, LMStudio, KoboldCpp) use OpenAI-compatible APIs through LiteLLM.

**Provider Configuration:**

You can customize provider endpoints using environment variables:
```shell
export OLLAMA_API_BASE="http://localhost:11434"      # Default Ollama endpoint
export LMSTUDIO_API_BASE="http://localhost:1234/v1"  # Default LMStudio endpoint
export KOBOLDCPP_API_BASE="http://localhost:5001/v1" # Default KoboldCpp endpoint
export OPENROUTER_API_KEY="your-api-key"              # OpenRouter API key
```

If a provider fails to respond (e.g., server not running), the app shows a warning but continues with models from other providers.

If no models are discovered from any provider, the app shows an error; please ensure at least one provider is running.

### Running via Make

Prefer the provided make targets for development and running:

```shell
make install    # set up environment and pre-commit hooks
make check      # run linters/formatters and pre-commit checks
make run        # launch the application
```

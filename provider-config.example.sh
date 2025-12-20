# Chat Circuit - Provider Configuration Examples

# This file demonstrates how to configure different LLM providers
# Copy this to your shell profile or set before running the application

# =============================================================================
# OLLAMA (Local LLM Server)
# =============================================================================
# Default: http://localhost:11434
# Set this if your Ollama server runs on a different host or port
# export OLLAMA_API_BASE="http://localhost:11434"

# Example: Remote Ollama server
# export OLLAMA_API_BASE="http://192.168.1.100:11434"

# =============================================================================
# LMSTUDIO (Local LLM Server with OpenAI-compatible API)
# =============================================================================
# Default: http://localhost:1234/v1
# Set this if your LMStudio server runs on a different host or port
# export LMSTUDIO_API_BASE="http://localhost:1234/v1"

# Example: Remote LMStudio server
# export LMSTUDIO_API_BASE="http://192.168.1.100:1234/v1"

# Example: Different port
# export LMSTUDIO_API_BASE="http://localhost:8080/v1"

# =============================================================================
# KOBOLDCPP (Local LLM Server with OpenAI-compatible API)
# =============================================================================
# Default: http://localhost:5001/v1
# Set this if your KoboldCpp server runs on a different host or port
# export KOBOLDCPP_API_BASE="http://localhost:5001/v1"

# Example: Remote KoboldCpp server
# export KOBOLDCPP_API_BASE="http://192.168.1.100:5001/v1"

# Example: Different port
# export KOBOLDCPP_API_BASE="http://localhost:5002/v1"

# =============================================================================
# OPENROUTER (Cloud API Service)
# =============================================================================
# Required for OpenRouter support
# Get your API key from https://openrouter.ai/keys
# export OPENROUTER_API_KEY="your-api-key-here"

# Alternative: Set via Configuration dialog in the app (Ctrl+,)

# =============================================================================
# Usage Examples
# =============================================================================

# Run with custom Ollama endpoint:
# OLLAMA_API_BASE="http://192.168.1.100:11434" python3 main.py

# Run with multiple providers configured:
# OLLAMA_API_BASE="http://localhost:11434" \
# LMSTUDIO_API_BASE="http://localhost:1234/v1" \
# KOBOLDCPP_API_BASE="http://localhost:5001/v1" \
# OPENROUTER_API_KEY="your-key" \
# python3 main.py

# =============================================================================
# Provider Model Prefixes
# =============================================================================
# The application automatically discovers models and prefixes them:
# - Ollama models: ollama_chat/llama3:latest
# - LMStudio models: lmstudio/model-name
# - KoboldCpp models: koboldcpp/model-name
# - OpenRouter models: openrouter/google/gemma-7b-it:free

# =============================================================================
# Testing Provider Connectivity
# =============================================================================

# Test Ollama:
# curl http://localhost:11434/api/tags

# Test LMStudio:
# curl http://localhost:1234/v1/models

# Test KoboldCpp:
# curl http://localhost:5001/v1/models

# Test OpenRouter (requires API key):
# curl -H "Authorization: Bearer YOUR-KEY" https://openrouter.ai/api/v1/models

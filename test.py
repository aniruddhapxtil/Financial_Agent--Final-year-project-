import google.generativeai as genai

# Add your API key
genai.configure(api_key="AIzaSyBWqrdhEApdFUuaDSyA4gA5WvbI7eYWi2k")

# List all available models
for model in genai.list_models():
    if "generateContent" in model.supported_generation_methods:
        print(model.name)

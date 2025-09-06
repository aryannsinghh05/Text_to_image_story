from transformers import pipeline

# Local text generation pipeline
generator = pipeline("text2text-generation", model="google/flan-t5-small")

# Test prompt
prompt = "Write a short fantasy story about a magical sword."
result = generator(prompt, max_length=100)

print("✅ Success! Local model responded.")
print("Generated Text:\n", result[0]["generated_text"])

from groq import Groq

client = Groq(
    api_key=".............................................."
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": "Bonjour"
        }
    ]
)

print(response.choices[0].message.content)



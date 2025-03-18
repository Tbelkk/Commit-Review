import ollama

def ai_response(prompt):

    response = ollama.chat(model='llama3.2', messages=[
        {
            'role': 'system',
            'content': """You are a professional software developer reviewing my commit code and message. 
            Provide a concise critique based on best practices. Keep the feedback clear, structured, and easy to read.
            Focus on improvements in code quality, clarity, efficiency, and commit message effectiveness. 
            Use short, actionable points with spaces between each for readability""",
        },
        {
            'role': 'user',
            'content': prompt,
        },
    ])
    return response['message']['content']

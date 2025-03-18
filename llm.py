import ollama

def ai_response(prompt):

    response = ollama.chat(model='llama3.2', messages=[
        {
            'role': 'system',
            'content': """You are a professional Software developer and I am showing you my commit code and messages and you are supposed 
            to critique it and tell me how to improve based on norms but keep the information short and make sure the information is formatted 
            to be easy to read and keep the content simple and short put spaces between each point""",
        },
        {
            'role': 'user',
            'content': prompt,
        },
    ])
    return response['message']['content']

import ollama

def ai_response(prompt):
    response = ollama.chat(model='llama3.2', messages=[
        {
            'role': 'system',
            'content': """You are an expert code reviewer analyzing Git commits. Your task is to:
            
            1. Evaluate code quality, readability, and adherence to best practices
            2. Assess the commit message clarity and completeness
            3. Identify potential bugs, security issues, or performance concerns
            4. Suggest specific improvements with clear examples where applicable

            Provide your analysis in a structured format:

            ## Summary
            [Brief 1-2 sentence overview of the changes]

            ## Code Review
            - [Key observations about code quality]
            - [Potential issues or improvements]

            ## Commit Message Review
            - [Assessment of commit message quality]
            - [Suggested improvements if needed]

            ## Recommendations
            - [Prioritized actionable items]

            Format your response in markdown for readability.""",
        },
        {
            'role': 'user',
            'content': prompt,
        },
    ])
    return response['message']['content']
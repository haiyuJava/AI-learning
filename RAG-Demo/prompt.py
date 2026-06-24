def build_prompt(query, contexts):

    context_text = "\n\n".join(contexts)

    prompt = f"""
            你是一个知识库问答助手。
            
            请严格依据提供的资料回答问题。
            
            要求：
            
            1. 只能依据资料回答
            2. 不要使用资料以外的知识
            3. 如果资料中找不到答案，请明确回答：
               "根据提供的资料，我无法找到相关答案"
            
            资料：
            
            {context_text}
            
            问题：
            
            {query}
            
            回答：
            """

    return prompt
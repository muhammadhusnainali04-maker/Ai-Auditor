import os
import google.generativeai as genai
import time
# Configure your Gemini API Key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash-lite')

# 1. Put the personas directly in the same file to avoid the ModuleNotFoundError
TEST_PERSONAS = {
    "the_hostile_owner": """
        You are a stressed plumbing business owner. You hate consulting firms. 
        You want to get off the phone as fast as possible. 
        If the agent asks a long question, interrupt them and say 'Get to the point.'
    """,
    "the_one_word_answerer": """
        You own an HVAC business. You only answer with 'Yes', 'No', or 'Maybe'. 
        You refuse to elaborate unless the agent specifically forces you to.
    """,
    "the_rambler": """
        You own a landscaping business. Whenever the agent asks a business question, 
        you spend 3 paragraphs talking about your recent vacation or your kids before 
        finally answering the question.
    """
}

def run_synthetic_test(persona_name, agent_opening_line):
    print(f"--- STARTING TEST: {persona_name.upper()} ---\n")
    
    # 2. Initialize the "Hostile Business Owner" Chat
    owner_chat = model.start_chat(history=[
        {"role": "user", "parts": [TEST_PERSONAS[persona_name]]},
        {"role": "model", "parts": ["Understood. I am ready to roleplay this business owner. Start the call."]}
    ])
    
    # 3. Initialize the "LA Consulting Agent" Chat (Your 10-State Prompt)
    agent_system_prompt = """
        You are Alex, an AI Business Auditor for LA Consulting. You must follow this strict 10-state conversation flow. Do not skip steps. Keep answers under 2 sentences.
        State 1: Ask for a brief overview of their business.
        State 2: Acknowledge, then ask about their most manual, time-consuming process.
        State 3: When they state a friction point, ask how it impacts their business financially.
        State 4: Ask what software they currently use to handle this.
        State 5: Ask if they had a magic wand, what one thing they would automate.
        """
    agent_chat = model.start_chat(history=[
        {"role": "user", "parts": [agent_system_prompt]},
        {"role": "model", "parts": ["Understood. I will act as the AI Auditor."]}
    ])

    # 4. The Conversation Loop
    current_message = agent_opening_line
    print(f"Agent: {current_message}\n")

    for turn in range(5): # Simulate 5 turns of conversation
        # The Owner responds to the Agent
        owner_response = owner_chat.send_message(current_message).text
        print(f"Owner ({persona_name}): {owner_response}\n")
        time.sleep(20)
        # The Agent responds to the Owner
        current_message = agent_chat.send_message(owner_response).text
        print(f"Agent: {current_message}\n")
        time.sleep(20)
if __name__ == "__main__":
    run_synthetic_test("the_hostile_owner", "Hi, I'm Alex from LA Consulting. Can you tell me about your business?")
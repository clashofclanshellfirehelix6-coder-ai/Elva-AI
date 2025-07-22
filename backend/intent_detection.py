import os
import json
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

load_dotenv()
logger = logging.getLogger(__name__)

# Setup LLM connection (Groq + LLaMA3)
llm = ChatOpenAI(
    temperature=0,
    openai_api_key=os.getenv("GROQ_API_KEY"),
    model="llama3-8b-8192",
    base_url="https://api.groq.com/openai/v1"
)

# --- INTENT DETECTION PROMPT ---
intent_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI assistant that detects user intent and extracts structured JSON for different tasks.

CRITICAL INSTRUCTIONS:
- Respond with ONLY valid JSON, no additional text or explanations
- All JSON must be complete and properly formatted
- Do not add any text before or after the JSON
- For all intents except general_chat, populate ALL fields with realistic content

You can detect the following intents:
1. send_email
2. create_event
3. add_todo
4. set_reminder
5. linkedin_post
6. gmail_check_inbox
7. gmail_unread_count
8. gmail_search
9. gmail_send
10. gmail_mark_read
11. general_chat

Examples of COMPLETE JSON responses:

For "Send an email to John about the meeting":
{{
  "intent": "send_email",
  "recipient_name": "John",
  "recipient_email": "",
  "subject": "Meeting Update",
  "body": "Hi John,\\\\n\\\\nI wanted to update you about our upcoming meeting. Please let me know if you have any questions.\\\\n\\\\nBest regards"
}}

For "Create a team meeting for tomorrow at 2pm":
{{
  "intent": "create_event",
  "event_title": "Team Meeting",
  "date": "tomorrow",
  "time": "2:00 PM",
  "participants": ["team@company.com"],
  "location": "Conference Room"
}}

For "Remind me to call the client":
{{
  "intent": "set_reminder",
  "reminder_text": "Call client about project status",
  "reminder_time": "",
  "reminder_date": "today"
}}

For "Add finish the report to my todo list":
{{
  "intent": "add_todo",
  "task": "Finish the quarterly report",
  "due_date": ""
}}

For "Post about AI on LinkedIn":
{{
  "intent": "linkedin_post",
  "topic": "Artificial Intelligence",
  "category": "Technology",
  "post_content": "Excited to share insights about AI advancements! #AI #Technology"
}}

For "Check my Gmail inbox" or "Show me my emails":
{{
  "intent": "gmail_check_inbox",
  "max_results": 10,
  "query": ""
}}

For "How many unread emails do I have?":
{{
  "intent": "gmail_unread_count"
}}

For "Search for emails from John":
{{
  "intent": "gmail_search",
  "query": "from:john",
  "max_results": 10
}}

For "Send an email via Gmail to sarah@example.com about meeting":
{{
  "intent": "gmail_send",
  "to": "sarah@example.com",
  "subject": "Meeting Discussion",
  "body": "Hi Sarah, I wanted to discuss our upcoming meeting..."
}}

For "Mark these emails as read":
{{
  "intent": "gmail_mark_read",
  "message_ids": []
}}

For anything else:
{{
  "intent": "general_chat",
  "message": "original user message"
}}

REMEMBER: Return ONLY the JSON object, nothing else."""),
    ("user", "{input}")
])

# --- FRIENDLY DRAFT PROMPT ---
friendly_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a friendly assistant that converts structured intent data into human-friendly messages.

Respond based on intent type:

- send_email → Draft a friendly email
- linkedin_post → Draft a professional LinkedIn post
- create_event / add_todo / set_reminder → Summarize task or reminder
- general_chat → Return the user message

Return plain text.

Examples:

Input: {{"intent": "send_email", "recipient_name": "Priya", "subject": "AI Update", "body": "Here's the latest..."}}
Output: ✉️ Here's a draft email to Priya:
Subject: AI Update
Body: Here's the latest...

Input: {{"intent": "set_reminder", "reminder_text": "Meeting with HR", "reminder_time": "10 AM", "reminder_date": "tomorrow"}}
Output: ⏰ I'll remind you about "Meeting with HR" at 10 AM tomorrow.
"""),
    ("user", "{input_json}")
])

# --- GENERAL CHAT PROMPT ---
general_chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are Elva AI – a friendly and helpful assistant."),
    ("user", "{input}")
])

def detect_intent(user_input: str) -> dict:
    try:
        chain = intent_prompt | llm
        response = chain.invoke({"input": user_input})
        logger.info(f"LLM response for intent detection: {response.content}")
        
        # Extract JSON from the response (LLM might add extra text)
        content = response.content.strip()
        
        # Find the first { and last } to extract JSON
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx + 1]
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON decode error: {json_err}")
                logger.error(f"Problematic JSON: {json_str}")
                
                # Try to fix escaped newlines and other issues
                try:
                    # The JSON might have properly escaped newlines like \\n that need to be double-escaped for JSON parsing
                    # Let's try parsing as-is first, then try fixes
                    import ast
                    # Try using ast.literal_eval for more robust parsing
                    result = ast.literal_eval(json_str)
                    if isinstance(result, dict):
                        return result
                except:
                    pass
                
                # If still failing, treat as general chat but return a better error
                return {
                    "intent": "general_chat", 
                    "message": user_input,
                    "error": f"JSON parsing failed: {str(json_err)}"
                }
        else:
            # If no JSON found, treat as general chat
            return {
                "intent": "general_chat",
                "message": user_input
            }
            
    except Exception as e:
        logger.error(f"Intent detection error: {e}")
        return {
            "intent": "general_chat",
            "message": user_input,
            "error": str(e)
        }

def generate_friendly_draft(intent_data: dict) -> str:
    try:
        chain = friendly_prompt | llm
        response = chain.invoke({"input_json": json.dumps(intent_data)})
        return response.content
    except Exception as e:
        logger.error(f"Draft generation error: {e}")
        return "⚠️ Could not generate a friendly message."

def handle_general_chat(user_input: str) -> str:
    try:
        chain = general_chat_prompt | llm
        response = chain.invoke({"input": user_input})
        return response.content
    except Exception as e:
        return "🤖 Sorry, I couldn't answer that."

def format_intent_for_webhook(intent_data: dict, user_id: str, session_id: str) -> dict:
    from datetime import datetime
    return {
        "user_id": user_id,
        "session_id": session_id,
        "intent": intent_data.get("intent"),
        "data": intent_data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
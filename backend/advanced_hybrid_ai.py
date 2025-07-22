import os
import json
import asyncio
import logging
import uuid
import re
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()
logger = logging.getLogger(__name__)

class ModelChoice(Enum):
    GROQ = "groq"
    CLAUDE = "claude"
    BOTH_SEQUENTIAL = "both_sequential"  # Use both models in sequence
    HYBRID_PARALLEL = "hybrid_parallel"  # Use both models and merge results

@dataclass
class TaskClassification:
    """Advanced task classification with multiple dimensions"""
    primary_intent: str
    emotional_complexity: str  # low, medium, high
    professional_tone_required: bool
    creative_requirement: str  # none, low, medium, high
    technical_complexity: str  # simple, moderate, complex
    response_length: str  # short, medium, long
    user_engagement_level: str  # informational, conversational, interactive
    context_dependency: str  # none, session, historical
    reasoning_type: str  # logical, emotional, creative, analytical

@dataclass
class RoutingDecision:
    """Routing decision with explanation"""
    primary_model: ModelChoice
    confidence: float  # 0.0 to 1.0
    reasoning: str
    fallback_model: Optional[ModelChoice] = None
    use_context_enhancement: bool = False

class AdvancedHybridAI:
    """
    Advanced Hybrid AI system with sophisticated task classification and routing
    """
    
    def __init__(self):
        # Initialize models
        self.groq_llm = ChatOpenAI(
            temperature=0,
            openai_api_key=os.getenv("GROQ_API_KEY"),
            model="llama3-8b-8192",
            base_url="https://api.groq.com/openai/v1"
        )
        
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not self.claude_api_key:
            logger.error("CLAUDE_API_KEY not found in environment variables")
        
        # Conversation history for context-aware routing
        self.conversation_history = {}
        
        # Advanced routing configuration
        self.routing_rules = self._initialize_routing_rules()
        
    def is_direct_automation_intent(self, intent: str) -> bool:
        """Check if an intent should bypass AI response generation and go directly to automation"""
        direct_automation_intents = [
            "check_linkedin_notifications",
            "scrape_price", 
            "scrape_product_listings",
            "linkedin_job_alerts",
            "check_website_updates",
            "monitor_competitors", 
            "scrape_news_articles",
            # Gmail direct automation intents
            "gmail_check_inbox",
            "gmail_unread_count"
        ]
        return intent in direct_automation_intents

    def get_automation_status_message(self, intent: str) -> str:
        """Get appropriate status message for automation intent"""
        status_messages = {
            "check_linkedin_notifications": "🔔 Checking LinkedIn notifications...",
            "scrape_price": "💰 Searching for current prices...",
            "scrape_product_listings": "🛒 Scraping product listings...",
            "linkedin_job_alerts": "💼 Checking LinkedIn job alerts...",
            "check_website_updates": "🔍 Monitoring website updates...",
            "monitor_competitors": "📊 Analyzing competitor data...",
            "scrape_news_articles": "📰 Gathering latest news...",
            # Gmail status messages
            "gmail_check_inbox": "📧 Checking Gmail inbox...",
            "gmail_unread_count": "📬 Counting unread emails..."
        }
        return status_messages.get(intent, "🔍 Searching the web...")

    def _initialize_routing_rules(self) -> Dict[str, Any]:
        """Initialize sophisticated routing rules"""
        return {
            # Intent-based primary routing
            "intent_routing": {
                "general_chat": {"model": ModelChoice.CLAUDE, "confidence": 0.9},
                "send_email": {"model": ModelChoice.BOTH_SEQUENTIAL, "confidence": 0.85},
                "linkedin_post": {"model": ModelChoice.BOTH_SEQUENTIAL, "confidence": 0.85},
                "create_event": {"model": ModelChoice.BOTH_SEQUENTIAL, "confidence": 0.8},
                "add_todo": {"model": ModelChoice.CLAUDE, "confidence": 0.7},
                "set_reminder": {"model": ModelChoice.CLAUDE, "confidence": 0.7},
                "complex_analysis": {"model": ModelChoice.GROQ, "confidence": 0.8},
                "creative_writing": {"model": ModelChoice.BOTH_SEQUENTIAL, "confidence": 0.9},
                "technical_explanation": {"model": ModelChoice.GROQ, "confidence": 0.8},
                # New web automation intents
                "web_scraping": {"model": ModelChoice.GROQ, "confidence": 0.9},
                "linkedin_insights": {"model": ModelChoice.GROQ, "confidence": 0.85},
                "email_automation": {"model": ModelChoice.GROQ, "confidence": 0.8},
                "price_monitoring": {"model": ModelChoice.GROQ, "confidence": 0.8},
                "data_extraction": {"model": ModelChoice.GROQ, "confidence": 0.85},
                
                # Direct automation intents (bypass AI response/approval)
                "check_linkedin_notifications": {"model": ModelChoice.GROQ, "confidence": 0.9, "direct_automation": True},
                "scrape_price": {"model": ModelChoice.GROQ, "confidence": 0.9, "direct_automation": True},
                "scrape_product_listings": {"model": ModelChoice.GROQ, "confidence": 0.9, "direct_automation": True},
                "linkedin_job_alerts": {"model": ModelChoice.GROQ, "confidence": 0.9, "direct_automation": True},
                "check_website_updates": {"model": ModelChoice.GROQ, "confidence": 0.8, "direct_automation": True},
                "monitor_competitors": {"model": ModelChoice.GROQ, "confidence": 0.8, "direct_automation": True},
                "scrape_news_articles": {"model": ModelChoice.GROQ, "confidence": 0.8, "direct_automation": True}
            },
            
            # Gmail integration intents
            "gmail_check_inbox": {"model": ModelChoice.GROQ, "confidence": 0.9, "direct_automation": True},
            "gmail_unread_count": {"model": ModelChoice.GROQ, "confidence": 0.9, "direct_automation": True},
            "gmail_search": {"model": ModelChoice.GROQ, "confidence": 0.8},
            "gmail_send": {"model": ModelChoice.GROQ, "confidence": 0.8},
            "gmail_mark_read": {"model": ModelChoice.GROQ, "confidence": 0.8},
            
            # Emotional complexity routing
            "emotional_routing": {
                "high": ModelChoice.CLAUDE,  # High emotional intelligence needed
                "medium": ModelChoice.CLAUDE,  # Some emotional awareness needed
                "low": ModelChoice.GROQ       # Minimal emotional processing
            },
            
            # Professional tone routing
            "professional_routing": {
                "business_formal": ModelChoice.CLAUDE,  # Professional but warm
                "technical_formal": ModelChoice.GROQ,   # Precise and structured
                "casual_friendly": ModelChoice.CLAUDE   # Conversational and warm
            },
            
            # Creative requirement routing
            "creative_routing": {
                "high": ModelChoice.CLAUDE,      # High creativity needed
                "medium": ModelChoice.CLAUDE,    # Some creativity helpful
                "low": ModelChoice.GROQ,         # Minimal creativity needed
                "none": ModelChoice.GROQ         # No creativity required
            }
        }

    async def analyze_task_classification(self, user_input: str, session_id: str) -> TaskClassification:
        """
        Advanced task classification using AI analysis
        """
        logger.info(f"🔍 Advanced Task Classification: {user_input[:50]}...")
        
        # Use Groq for quick classification analysis
        classification_prompt = f"""Analyze this user message and classify it across multiple dimensions. Return ONLY a JSON object.

User Message: "{user_input}"

Classify across these dimensions:
{{
  "primary_intent": "one of: general_chat, send_email, create_event, add_todo, set_reminder, linkedin_post, complex_analysis, creative_writing, technical_explanation, web_scraping, linkedin_insights, email_automation, price_monitoring, data_extraction",
  "emotional_complexity": "one of: low, medium, high",
  "professional_tone_required": true or false,
  "creative_requirement": "one of: none, low, medium, high",
  "technical_complexity": "one of: simple, moderate, complex",
  "response_length": "one of: short, medium, long",
  "user_engagement_level": "one of: informational, conversational, interactive", 
  "context_dependency": "one of: none, session, historical",
  "reasoning_type": "one of: logical, emotional, creative, analytical"
}}

Examples:
- "Send a professional email to my boss" → high professional_tone, low creative_requirement, medium emotional_complexity
- "I'm feeling stressed about work" → high emotional_complexity, conversational engagement, emotional reasoning
- "Explain quantum computing" → technical_explanation intent, complex technical_complexity, logical reasoning
- "Write a creative story about AI" → creative_writing intent, high creative_requirement, creative reasoning"""

        try:
            response = await self._get_groq_response(classification_prompt)
            
            # Extract and parse JSON
            content = response.strip()
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx + 1]
                classification_data = json.loads(json_str)
                
                return TaskClassification(
                    primary_intent=classification_data.get("primary_intent", "general_chat"),
                    emotional_complexity=classification_data.get("emotional_complexity", "medium"),
                    professional_tone_required=classification_data.get("professional_tone_required", False),
                    creative_requirement=classification_data.get("creative_requirement", "none"),
                    technical_complexity=classification_data.get("technical_complexity", "simple"),
                    response_length=classification_data.get("response_length", "medium"),
                    user_engagement_level=classification_data.get("user_engagement_level", "conversational"),
                    context_dependency=classification_data.get("context_dependency", "none"),
                    reasoning_type=classification_data.get("reasoning_type", "emotional")
                )
                
        except Exception as e:
            logger.error(f"Classification error: {e}")
            
        # Fallback classification
        return TaskClassification(
            primary_intent="general_chat",
            emotional_complexity="medium",
            professional_tone_required=False,
            creative_requirement="low",
            technical_complexity="simple",
            response_length="medium",
            user_engagement_level="conversational",
            context_dependency="none",
            reasoning_type="emotional"
        )

    def _calculate_routing_decision(self, classification: TaskClassification, session_id: str) -> RoutingDecision:
        """
        Calculate optimal routing decision based on sophisticated analysis
        """
        factors = []
        
        # Intent-based scoring
        intent_rule = self.routing_rules["intent_routing"].get(classification.primary_intent, 
                                                              {"model": ModelChoice.CLAUDE, "confidence": 0.5})
        primary_model = intent_rule["model"]
        base_confidence = intent_rule["confidence"]
        factors.append(f"Intent '{classification.primary_intent}' suggests {primary_model.value}")
        
        # Emotional complexity adjustment
        if classification.emotional_complexity == "high":
            if primary_model != ModelChoice.CLAUDE:
                primary_model = ModelChoice.CLAUDE
                base_confidence = min(base_confidence + 0.2, 1.0)
                factors.append("High emotional complexity → Claude")
        elif classification.emotional_complexity == "low" and classification.reasoning_type == "logical":
            if primary_model == ModelChoice.CLAUDE:
                primary_model = ModelChoice.GROQ
                base_confidence = min(base_confidence + 0.1, 1.0)
                factors.append("Low emotion + logical reasoning → Groq")
        
        # Professional tone with creativity
        if classification.professional_tone_required and classification.creative_requirement in ["medium", "high"]:
            primary_model = ModelChoice.BOTH_SEQUENTIAL
            base_confidence = min(base_confidence + 0.15, 1.0)
            factors.append("Professional + Creative → Sequential (Groq→Claude)")
        
        # Technical complexity considerations
        if classification.technical_complexity == "complex" and classification.reasoning_type == "analytical":
            if primary_model == ModelChoice.CLAUDE:
                primary_model = ModelChoice.GROQ
                base_confidence = min(base_confidence + 0.1, 1.0)
                factors.append("Complex technical analysis → Groq")
        
        # Response length and engagement
        if classification.response_length == "long" and classification.user_engagement_level == "conversational":
            if primary_model == ModelChoice.GROQ:
                primary_model = ModelChoice.CLAUDE
                base_confidence = min(base_confidence + 0.1, 1.0)
                factors.append("Long conversational response → Claude")
        
        # Context dependency
        if classification.context_dependency in ["session", "historical"]:
            # Check if we have conversation history
            if session_id in self.conversation_history:
                base_confidence = min(base_confidence + 0.05, 1.0)
                factors.append("Context available → Enhanced confidence")
        
        # Creative requirement override (but preserve sequential routing for specific intents)
        if classification.creative_requirement == "high":
            if primary_model != ModelChoice.CLAUDE and primary_model != ModelChoice.BOTH_SEQUENTIAL:
                primary_model = ModelChoice.CLAUDE
                base_confidence = min(base_confidence + 0.15, 1.0)
                factors.append("High creativity requirement → Claude")
            elif primary_model == ModelChoice.BOTH_SEQUENTIAL:
                # Keep sequential routing for intents that need content synchronization
                factors.append("High creativity with sequential routing preserved")
        
        # Determine fallback
        fallback_model = None
        if primary_model == ModelChoice.CLAUDE:
            fallback_model = ModelChoice.GROQ
        elif primary_model == ModelChoice.GROQ:
            fallback_model = ModelChoice.CLAUDE
            
        reasoning = " | ".join(factors)
        
        return RoutingDecision(
            primary_model=primary_model,
            confidence=base_confidence,
            reasoning=reasoning,
            fallback_model=fallback_model,
            use_context_enhancement=classification.context_dependency != "none"
        )

    def _update_conversation_history(self, session_id: str, user_input: str, classification: TaskClassification):
        """Update conversation history for context-aware routing"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
            
        self.conversation_history[session_id].append({
            "message": user_input,
            "classification": classification,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Keep only last 10 messages for performance
        if len(self.conversation_history[session_id]) > 10:
            self.conversation_history[session_id] = self.conversation_history[session_id][-10:]

    async def _get_context_enhanced_prompt(self, user_input: str, session_id: str) -> str:
        """Generate context-enhanced prompt using conversation history"""
        if session_id not in self.conversation_history or not self.conversation_history[session_id]:
            return user_input
            
        recent_context = self.conversation_history[session_id][-3:]  # Last 3 messages
        
        context_summary = "Recent conversation context:\n"
        for i, ctx in enumerate(recent_context, 1):
            context_summary += f"{i}. User: {ctx['message'][:100]}...\n"
        
        enhanced_prompt = f"{context_summary}\nCurrent request: {user_input}"
        return enhanced_prompt

    async def _get_claude_response(self, prompt: str, system_message: str = None, enhanced_context: bool = False) -> str:
        """Enhanced Claude response with better error handling"""
        try:
            session_id = f"elva_claude_enhanced_{uuid.uuid4().hex[:8]}"
            
            default_system = "You are Elva AI – a sophisticated, emotionally intelligent assistant that provides warm, professional, and contextually aware responses."
            
            claude_chat = LlmChat(
                api_key=self.claude_api_key,
                session_id=session_id,
                system_message=system_message or default_system
            ).with_model("anthropic", "claude-3-5-sonnet-20241022").with_max_tokens(4096)
            
            user_message = UserMessage(text=prompt)
            response = await claude_chat.send_message(user_message)
            return response
            
        except Exception as e:
            logger.error(f"Enhanced Claude API error: {e}")
            return await self._get_groq_response(prompt, system_message)

    async def _get_groq_response(self, prompt: str, system_message: str = None) -> str:
        """Enhanced Groq response with better error handling"""
        try:
            if system_message:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_message),
                    ("user", "{input}")
                ])
            else:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("user", "{input}")
                ])
            
            chain = prompt_template | self.groq_llm
            response = chain.invoke({"input": prompt})
            return response.content
            
        except Exception as e:
            logger.error(f"Enhanced Groq API error: {e}")
            return "⚠️ I'm experiencing technical difficulties with my reasoning engine. Please try again."

    async def _execute_sequential_routing(self, user_input: str, classification: TaskClassification, session_id: str) -> Tuple[dict, str]:
        """Execute sequential routing: Groq → Claude with content synchronization"""
        logger.info("🔄 Sequential Routing: Groq → Claude (Content Synchronized)")
        
        # Step 1: Groq for intent detection and basic structure
        intent_data = await self._groq_intent_detection(user_input)
        
        # Step 2: Claude for content generation with explicit content extraction
        enhanced_prompt = user_input
        if classification.context_dependency != "none":
            enhanced_prompt = await self._get_context_enhanced_prompt(user_input, session_id)
        
        # Generate Claude response with content extraction instructions
        system_message = self._generate_claude_system_message_with_extraction(classification, intent_data)
        claude_response = await self._get_claude_response(enhanced_prompt, system_message)
        
        # Step 3: Extract the actual content from Claude's response and synchronize with intent_data
        synchronized_intent_data = await self._synchronize_content_fields(intent_data, claude_response, classification)
        
        return synchronized_intent_data, claude_response

    def _generate_claude_system_message_with_extraction(self, classification: TaskClassification, intent_data: dict) -> str:
        """Generate system message for Claude with content extraction requirements"""
        base_message = "You are Elva AI – a sophisticated AI assistant."
        
        # Add personality based on classification
        if classification.emotional_complexity == "high":
            base_message += " You are particularly empathetic and emotionally intelligent."
        
        if classification.professional_tone_required:
            base_message += " Maintain a professional yet warm tone in your responses."
        
        if classification.creative_requirement in ["medium", "high"]:
            base_message += " Feel free to be creative and engaging in your responses."
        
        # Add intent-specific guidance with content extraction
        intent = intent_data.get("intent", "general_chat")
        if intent == "send_email":
            base_message += """ 
            
CRITICAL: When drafting emails, structure your response EXACTLY as follows:

✉️ Here's a draft email for [recipient]:

Subject: [exact subject line]
Body: [exact email content that will be used]

The content you write for Subject and Body will be used EXACTLY as written in the approval modal. Make sure the body is complete and ready to send."""
            
        elif intent == "linkedin_post":
            base_message += """ 
            
CRITICAL: When creating LinkedIn posts, structure your response EXACTLY as follows:

📱 Here's an engaging LinkedIn post for you:

[exact post content including hashtags and formatting - this exact text will be used]

The post content you generate will be used EXACTLY as written in the approval modal. Make it complete and ready to post."""
            
        elif intent == "creative_writing":
            base_message += """ 
            
CRITICAL: When creating creative content, provide the exact content that will be used.

✨ Here's your creative content:

[exact content that will be used - make it complete and ready to use]

The content you generate will be used EXACTLY as written in the approval modal."""
            
        elif intent in ["add_todo", "set_reminder"]:
            base_message += " Be encouraging and supportive when helping with task management. Provide clear, actionable descriptions."
        
        return base_message

    async def _synchronize_content_fields(self, intent_data: dict, claude_response: str, classification: TaskClassification) -> dict:
        """Synchronize content fields between Claude response and intent data to ensure unified content"""
        intent = intent_data.get("intent", "general_chat")
        
        try:
            if intent == "send_email":
                # Extract subject and body from Claude's response for perfect synchronization
                subject_match = re.search(r'Subject:\s*(.+)', claude_response)
                # Enhanced body extraction - capture everything after "Body:" until next section or end
                body_match = re.search(r'Body:\s*(.*?)(?:\n\nThe content|$)', claude_response, re.DOTALL)
                
                if subject_match:
                    extracted_subject = subject_match.group(1).strip()
                    intent_data["subject"] = extracted_subject
                    logger.info(f"📧 Subject synchronized: {extracted_subject}")
                    
                if body_match:
                    extracted_body = body_match.group(1).strip()
                    intent_data["body"] = extracted_body
                    logger.info(f"📧 Body synchronized: {len(extracted_body)} characters")
                    
            elif intent == "linkedin_post" or intent == "creative_writing":
                # Enhanced LinkedIn post content extraction with multiple fallback patterns
                content_patterns = [
                    # Pattern 1: Content after 📱 emoji with various formats
                    r'📱.*?:\s*\n+(.*?)(?:\n\n(?:This|Feel free|Let me know)|$)',
                    # Pattern 2: Content after "Here's" with various formats  
                    r'Here\'s.*?:\s*\n+(.*?)(?:\n\n(?:This|Feel free|Let me know)|$)',
                    # Pattern 3: Quoted content anywhere in response
                    r'"([^"]{50,})"',  # Look for substantial quoted content (50+ chars)
                    # Pattern 4: Content between blank lines (main content block)
                    r'\n\n([^"]+?)\n\n',
                    # Pattern 5: Everything after first sentence if it's an intro
                    r'^[^.!?]+[.!?]\s*\n+(.*?)(?:\n\nThis|$)',
                ]
                
                extracted_content = None
                for i, pattern in enumerate(content_patterns, 1):
                    match = re.search(pattern, claude_response, re.DOTALL | re.IGNORECASE)
                    if match:
                        candidate_content = match.group(1).strip()
                        # Validate content quality (not just intro text)
                        if len(candidate_content) > 20 and not candidate_content.lower().startswith(('here', 'i\'ve', 'let me')):
                            extracted_content = candidate_content
                            logger.info(f"📱 Pattern {i} matched for {intent}")
                            break
                
                # Final fallback: Extract main content block (skip first line if it's intro)
                if not extracted_content:
                    lines = [line.strip() for line in claude_response.split('\n') if line.strip()]
                    if len(lines) > 1:
                        # Skip intro line, take substantial content
                        content_lines = []
                        start_found = False
                        for line in lines[1:]:  # Skip first line
                            # Stop at explanatory text
                            if any(phrase in line.lower() for phrase in ['this should', 'feel free', 'let me know', 'hope this']):
                                break
                            # Skip emoji lines or short connector lines
                            if len(line) > 10 and not line.startswith('📱') and not line.startswith('✨'):
                                content_lines.append(line)
                                start_found = True
                            elif start_found and line:  # Include short lines within content
                                content_lines.append(line)
                        
                        if content_lines:
                            extracted_content = '\n'.join(content_lines).strip()
                            logger.info(f"📱 Fallback extraction for {intent}")
                
                # Store the unified content
                if extracted_content:
                    # Clean up extracted content
                    extracted_content = extracted_content.replace('""', '"').strip()
                    
                    if intent == "linkedin_post":
                        intent_data["post_content"] = extracted_content
                        logger.info(f"🎯 LinkedIn post content unified: {len(extracted_content)} characters")
                    elif intent == "creative_writing":
                        intent_data["content"] = extracted_content
                        logger.info(f"🎯 Creative content unified: {len(extracted_content)} characters")
                else:
                    logger.warning(f"⚠️ Could not extract unified content for {intent}, using original")
                        
            elif intent == "set_reminder":
                # Extract reminder details with better pattern matching
                reminder_patterns = [
                    r'remind you[^"]*"([^"]+)"',
                    r'reminder[^:]*:\s*"([^"]+)"',
                    r'reminder[^:]*:\s*([^"]+?)(?:\n|$)'
                ]
                
                for pattern in reminder_patterns:
                    reminder_match = re.search(pattern, claude_response, re.IGNORECASE)
                    if reminder_match:
                        intent_data["reminder_text"] = reminder_match.group(1).strip()
                        logger.info(f"⏰ Reminder text synchronized")
                        break
                    
            elif intent == "add_todo":
                # Extract task details with better pattern matching
                task_patterns = [
                    r'task[^"]*"([^"]+)"',
                    r'todo[^:]*:\s*"([^"]+)"',
                    r'todo[^:]*:\s*([^"]+?)(?:\n|$)'
                ]
                
                for pattern in task_patterns:
                    task_match = re.search(pattern, claude_response, re.IGNORECASE)
                    if task_match:
                        intent_data["task"] = task_match.group(1).strip()
                        logger.info(f"✅ Task text synchronized")
                        break
            
            logger.info(f"🔗 Content Synchronized: {intent} - All fields unified with Claude response")
            return intent_data
            
        except Exception as e:
            logger.error(f"Content synchronization error: {e}")
            # Return original intent data if synchronization fails
            return intent_data

    def _generate_claude_system_message(self, classification: TaskClassification, intent_data: dict) -> str:
        """Generate contextual system message for Claude based on classification"""
        base_message = "You are Elva AI – a sophisticated AI assistant."
        
        # Add personality based on classification
        if classification.emotional_complexity == "high":
            base_message += " You are particularly empathetic and emotionally intelligent."
        
        if classification.professional_tone_required:
            base_message += " Maintain a professional yet warm tone in your responses."
        
        if classification.creative_requirement in ["medium", "high"]:
            base_message += " Feel free to be creative and engaging in your responses."
        
        # Add intent-specific guidance
        intent = intent_data.get("intent", "general_chat")
        if intent == "send_email":
            base_message += " When drafting emails, focus on clarity, professionalism, and appropriate tone."
        elif intent == "linkedin_post":
            base_message += " For LinkedIn posts, create engaging professional content that encourages interaction."
        elif intent in ["add_todo", "set_reminder"]:
            base_message += " Be encouraging and supportive when helping with task management."
        
        return base_message

    async def _groq_intent_detection(self, user_input: str) -> dict:
        """Groq-specific intent detection with enhanced prompting"""
        system_message = """You are an AI assistant specialized in intent detection. Extract structured JSON data.

CRITICAL INSTRUCTIONS:
- Return ONLY valid JSON
- All JSON must be complete and properly formatted  
- For all intents except general_chat, populate ALL fields with realistic content

Intent types: send_email, create_event, add_todo, set_reminder, linkedin_post, creative_writing, web_scraping, linkedin_insights, email_automation, price_monitoring, data_extraction, check_linkedin_notifications, scrape_price, scrape_product_listings, linkedin_job_alerts, check_website_updates, monitor_competitors, scrape_news_articles, general_chat

Example JSON responses:

Send email: {{"intent": "send_email", "recipient_name": "Name", "subject": "Subject", "body": "Content"}}
Create event: {{"intent": "create_event", "event_title": "Title", "date": "Date", "time": "Time"}}
Add todo: {{"intent": "add_todo", "task": "Task description", "due_date": "Date"}}
Set reminder: {{"intent": "set_reminder", "reminder_text": "Text", "reminder_date": "Date"}}
LinkedIn post: {{"intent": "linkedin_post", "topic": "Topic", "post_content": "Content"}}
Creative writing: {{"intent": "creative_writing", "content": "Creative content", "topic": "Topic"}}

Web automation (traditional): 
Web scraping: {{"intent": "web_scraping", "url": "target URL", "data_type": "type of data to extract", "selectors": {{"field": "css_selector"}}}}
LinkedIn insights: {{"intent": "linkedin_insights", "insight_type": "notifications/profile_views/connections", "email": "linkedin_email", "password": "password"}}
Email automation: {{"intent": "email_automation", "provider": "outlook/yahoo/gmail", "email": "email", "password": "password", "action": "check_inbox/send_email"}}
Price monitoring: {{"intent": "price_monitoring", "product_url": "URL", "product_name": "Name", "price_selector": "CSS selector"}}
Data extraction: {{"intent": "data_extraction", "url": "URL", "data_fields": ["field1", "field2"], "selectors": {{"field": "selector"}}}}

Direct automation (no approval needed):
Check LinkedIn notifications: {{"intent": "check_linkedin_notifications", "account_type": "personal/business"}}
Scrape price: {{"intent": "scrape_price", "product": "product name", "platform": "amazon/flipkart/ebay", "search_query": "search terms"}}
Scrape product listings: {{"intent": "scrape_product_listings", "category": "category", "platform": "website", "filters": {{"price_range": "range", "brand": "brand"}}}}
LinkedIn job alerts: {{"intent": "linkedin_job_alerts", "job_title": "title", "location": "location"}}
Check website updates: {{"intent": "check_website_updates", "website": "website_name", "section": "section to monitor"}}
Monitor competitors: {{"intent": "monitor_competitors", "company": "company_name", "data_type": "pricing/products/news"}}
Scrape news articles: {{"intent": "scrape_news_articles", "topic": "news topic", "source": "news source"}}

General chat: {{"intent": "general_chat", "message": "original message"}}

Return ONLY the JSON object."""

        try:
            response = await self._get_groq_response(user_input, system_message)
            
            # Enhanced JSON extraction
            content = response.strip()
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx + 1]
                return json.loads(json_str)
            else:
                return {"intent": "general_chat", "message": user_input}
                
        except Exception as e:
            logger.error(f"Enhanced intent detection error: {e}")
            return {"intent": "general_chat", "message": user_input, "error": str(e)}

    async def process_message(self, user_input: str, session_id: str) -> Tuple[dict, str, RoutingDecision]:
        """
        Main processing function with advanced routing
        """
        logger.info(f"🚀 Advanced Hybrid Processing: {user_input[:50]}...")
        
        # Step 1: Advanced task classification
        classification = await self.analyze_task_classification(user_input, session_id)
        
        # Step 2: Calculate routing decision
        routing_decision = self._calculate_routing_decision(classification, session_id)
        
        # Step 3: Update conversation history
        self._update_conversation_history(session_id, user_input, classification)
        
        logger.info(f"🧠 Classification: {classification.primary_intent} | Routing: {routing_decision.primary_model.value} | Confidence: {routing_decision.confidence:.2f}")
        logger.info(f"💡 Reasoning: {routing_decision.reasoning}")
        
        # Step 4: Execute routing decision
        try:
            if routing_decision.primary_model == ModelChoice.BOTH_SEQUENTIAL:
                intent_data, response_text = await self._execute_sequential_routing(user_input, classification, session_id)
            elif routing_decision.primary_model == ModelChoice.CLAUDE:
                # Claude for warm, contextual responses
                enhanced_prompt = user_input
                if routing_decision.use_context_enhancement:
                    enhanced_prompt = await self._get_context_enhanced_prompt(user_input, session_id)
                
                system_message = self._generate_claude_system_message(classification, {"intent": classification.primary_intent})
                response_text = await self._get_claude_response(enhanced_prompt, system_message)
                intent_data = {"intent": classification.primary_intent, "message": user_input}
            else:  # Groq
                intent_data = await self._groq_intent_detection(user_input)
                if intent_data.get("intent") == "general_chat":
                    # Fallback to Claude for general chat
                    response_text = await self._get_claude_response(user_input)
                else:
                    # Use Groq for structured response
                    response_text = f"I've analyzed your request: {intent_data.get('intent')}. Here are the details I extracted: {json.dumps(intent_data, indent=2)}"
            
            return intent_data, response_text, routing_decision
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            # Fallback to simple routing
            if routing_decision.fallback_model:
                try:
                    if routing_decision.fallback_model == ModelChoice.CLAUDE:
                        response_text = await self._get_claude_response(user_input)
                        intent_data = {"intent": "general_chat", "message": user_input}
                    else:
                        intent_data = await self._groq_intent_detection(user_input) 
                        response_text = f"Structured analysis: {json.dumps(intent_data, indent=2)}"
                    
                    return intent_data, response_text, routing_decision
                except Exception as fallback_error:
                    logger.error(f"Fallback error: {fallback_error}")
            
            # Ultimate fallback
            return (
                {"intent": "general_chat", "message": user_input, "error": str(e)},
                "I apologize, but I'm experiencing some technical difficulties. Please try again.",
                routing_decision
            )

    def get_routing_stats(self, session_id: str) -> dict:
        """Get routing statistics for this session"""
        if session_id not in self.conversation_history:
            return {"total_messages": 0, "routing_decisions": []}
            
        history = self.conversation_history[session_id]
        return {
            "total_messages": len(history),
            "recent_classifications": [
                {
                    "intent": h["classification"].primary_intent,
                    "emotional_complexity": h["classification"].emotional_complexity,
                    "professional_tone": h["classification"].professional_tone_required
                } for h in history[-5:]  # Last 5 messages
            ]
        }

# Global instance
advanced_hybrid_ai = AdvancedHybridAI()

# Compatibility functions for existing API
async def detect_intent(user_input: str) -> dict:
    """Enhanced intent detection with sophisticated routing"""
    session_id = "legacy_session"  # For backward compatibility
    intent_data, _, routing_decision = await advanced_hybrid_ai.process_message(user_input, session_id)
    
    # Add routing metadata
    intent_data["_routing_info"] = {
        "model_used": routing_decision.primary_model.value,
        "confidence": routing_decision.confidence,
        "reasoning": routing_decision.reasoning
    }
    
    return intent_data

async def generate_friendly_draft(intent_data: dict) -> str:
    """Enhanced draft generation with contextual awareness"""
    session_id = "legacy_session"
    
    # Create a mock user input from intent data
    user_input = f"Generate a friendly response for: {intent_data.get('intent', 'general task')}"
    
    # Use the advanced system
    _, response_text, _ = await advanced_hybrid_ai.process_message(user_input, session_id)
    return response_text

async def handle_general_chat(user_input: str) -> str:
    """Enhanced general chat with emotional intelligence"""
    session_id = "legacy_session"
    _, response_text, _ = await advanced_hybrid_ai.process_message(user_input, session_id)
    return response_text

def format_intent_for_webhook(intent_data: dict, user_id: str, session_id: str) -> dict:
    """Format intent data for webhook"""
    from datetime import datetime
    return {
        "user_id": user_id,
        "session_id": session_id,
        "intent": intent_data.get("intent"),
        "data": intent_data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "routing_info": intent_data.get("_routing_info", {})
    }
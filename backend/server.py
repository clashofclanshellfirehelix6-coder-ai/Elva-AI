from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import json

# Import our enhanced hybrid AI system
from advanced_hybrid_ai import detect_intent, generate_friendly_draft, handle_general_chat, advanced_hybrid_ai
from webhook_handler import send_approved_action
from playwright_service import playwright_service, AutomationResult
from direct_automation_handler import direct_automation_handler

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str = "default_user"
    message: str
    response: str
    intent_data: Optional[dict] = None
    approved: Optional[bool] = None
    n8n_response: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str = "default_user"

class ChatResponse(BaseModel):
    id: str
    message: str
    response: str
    intent_data: Optional[dict] = None
    needs_approval: bool = False
    timestamp: datetime

class ApprovalRequest(BaseModel):
    session_id: str
    message_id: str
    approved: bool
    edited_data: Optional[dict] = None

class WebAutomationRequest(BaseModel):
    session_id: str
    automation_type: str  # "web_scraping", "linkedin_insights", "email_automation", "price_monitoring"
    parameters: dict

# Helper functions
def convert_objectid_to_str(doc):
    """Convert MongoDB ObjectId to string for JSON serialization"""
    if isinstance(doc, dict):
        new_doc = {}
        for key, value in doc.items():
            if key == '_id':
                # Skip MongoDB's _id field
                continue
            elif hasattr(value, 'binary') or str(type(value)) == "<class 'bson.objectid.ObjectId'>":
                # This is likely an ObjectId
                new_doc[key] = str(value)
            elif isinstance(value, dict):
                new_doc[key] = convert_objectid_to_str(value)
            elif isinstance(value, list):
                new_doc[key] = [convert_objectid_to_str(item) if isinstance(item, dict) else str(item) if hasattr(item, 'binary') else item for item in value]
            else:
                new_doc[key] = value
        return new_doc
    elif hasattr(doc, 'binary') or str(type(doc)) == "<class 'bson.objectid.ObjectId'>":
        return str(doc)
    else:
        return doc

# Routes
@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(f"🚀 Advanced Hybrid AI Chat: {request.message}")
        
        # Use advanced hybrid processing with sophisticated routing
        intent_data, response_text, routing_decision = await advanced_hybrid_ai.process_message(
            request.message, 
            request.session_id
        )
        
        logger.info(f"🧠 Advanced Routing: {routing_decision.primary_model.value} (confidence: {routing_decision.confidence:.2f})")
        logger.info(f"💡 Routing Logic: {routing_decision.reasoning}")
        
        # Check if this is a direct automation intent
        intent = intent_data.get("intent", "general_chat")
        is_direct_automation = advanced_hybrid_ai.is_direct_automation_intent(intent)
        
        if is_direct_automation:
            # Handle direct automation - bypass AI response generation and approval modal
            logger.info(f"🔄 Direct automation detected: {intent}")
            
            # Process the automation directly
            automation_result = await direct_automation_handler.process_direct_automation(intent_data)
            
            # Set response text to the automation result
            response_text = automation_result["message"]
            
            # Update intent data with automation results
            intent_data.update({
                "automation_result": automation_result["data"],
                "automation_success": automation_result["success"],
                "execution_time": automation_result["execution_time"],
                "direct_automation": True
            })
            
            # No approval needed for direct automation
            needs_approval = False
            
            logger.info(f"✅ Direct automation completed: {intent} - Success: {automation_result['success']}")
            
        else:
            # Traditional flow for non-direct automation intents
            web_automation_intents = ["web_scraping", "linkedin_insights", "email_automation", "price_monitoring", "data_extraction"]
            needs_approval = intent_data.get("intent") not in ["general_chat"]
            
            # For web automation intents, check if we have required credentials
            if intent_data.get("intent") in web_automation_intents:
                # Check if this is a web automation request that can be executed directly
                if intent_data.get("intent") == "web_scraping" and intent_data.get("url"):
                    # Execute web scraping directly if we have URL and selectors
                    try:
                        automation_result = await playwright_service.extract_dynamic_data(
                            intent_data.get("url"),
                            intent_data.get("selectors", {}),
                            intent_data.get("wait_for_element")
                        )
                        
                        # Update response with automation results
                        if automation_result.success:
                            response_text += f"\n\n🔍 **Web Scraping Results:**\n{json.dumps(automation_result.data, indent=2)}"
                            intent_data["automation_result"] = automation_result.data
                            intent_data["automation_success"] = True
                            needs_approval = False  # No approval needed for successful scraping
                        else:
                            response_text += f"\n\n⚠️ **Scraping Error:** {automation_result.message}"
                            intent_data["automation_error"] = automation_result.message
                            
                    except Exception as e:
                        logger.error(f"Direct web scraping error: {e}")
                        response_text += f"\n\n❌ **Automation Error:** {str(e)}"
        
        # Save to database
        chat_msg = ChatMessage(
            session_id=request.session_id,
            user_id=request.user_id,
            message=request.message,
            response=response_text,
            intent_data=intent_data
        )
        await db.chat_messages.insert_one(chat_msg.dict())
        
        return ChatResponse(
            id=chat_msg.id,
            message=request.message,
            response=response_text,
            intent_data=intent_data,
            needs_approval=needs_approval,
            timestamp=chat_msg.timestamp
        )
        
    except Exception as e:
        logger.error(f"💥 Advanced Hybrid Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/approve")
async def approve_action(request: ApprovalRequest):
    try:
        logger.info(f"Received approval request: {request}")
        
        # Get the message from database
        message = await db.chat_messages.find_one({"id": request.message_id})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        if not request.approved:
            # Update message in database with rejection
            await db.chat_messages.update_one(
                {"id": request.message_id},
                {"$set": {"approved": False}}
            )
            return {"success": True, "message": "Action cancelled"}
        
        # Use edited data if provided, otherwise use original intent data
        final_data = request.edited_data if request.edited_data else message["intent_data"]
        logger.info(f"Sending to n8n with data: {final_data}")
        
        # Send to n8n using our webhook handler
        n8n_response = await send_approved_action(
            final_data, 
            message["user_id"], 
            message["session_id"]
        )
        
        # Update message in database with approval status and n8n response
        await db.chat_messages.update_one(
            {"id": request.message_id},
            {"$set": {
                "approved": request.approved, 
                "n8n_response": n8n_response,
                "edited_data": request.edited_data
            }}
        )
        
        return {
            "success": True,
            "message": "Action executed successfully!" if n8n_response.get("success") else "Action sent but n8n had issues",
            "n8n_response": n8n_response
        }
        
    except HTTPException:
        # Re-raise HTTPException to preserve status code
        raise
    except Exception as e:
        logger.error(f"Approval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        logger.info(f"Getting chat history for session: {session_id}")
        
        messages = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(1000)
        
        # Convert ObjectIds to strings for JSON serialization
        serializable_messages = [convert_objectid_to_str(msg) for msg in messages]
        
        return {"messages": serializable_messages}
    except Exception as e:
        logger.error(f"History error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    try:
        logger.info(f"Clearing chat history for session: {session_id}")
        
        result = await db.chat_messages.delete_many({"session_id": session_id})
        return {
            "success": True, 
            "message": f"Cleared {result.deleted_count} messages from chat history"
        }
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/routing-stats/{session_id}")
async def get_routing_stats(session_id: str):
    try:
        stats = advanced_hybrid_ai.get_routing_stats(session_id)
        return {
            "session_id": session_id,
            "routing_statistics": stats,
            "advanced_features": {
                "task_classification": "multi-dimensional analysis",
                "routing_logic": "context-aware with fallback",
                "conversation_history": "last 10 messages tracked",
                "supported_routing": ["sequential", "claude_primary", "groq_primary", "context_enhanced"]
            }
        }
    except Exception as e:
        logger.error(f"Routing stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/automation-status/{intent}")
async def get_automation_status(intent: str):
    """Get automation status message for a specific intent"""
    try:
        status_message = advanced_hybrid_ai.get_automation_status_message(intent)
        is_direct = advanced_hybrid_ai.is_direct_automation_intent(intent)
        
        return {
            "intent": intent,
            "status_message": status_message,
            "is_direct_automation": is_direct,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Automation status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/web-automation")
async def execute_web_automation(request: WebAutomationRequest):
    """
    Execute web automation tasks using Playwright
    """
    try:
        logger.info(f"🌐 Web Automation Request: {request.automation_type}")
        
        result = None
        
        if request.automation_type == "web_scraping" or request.automation_type == "data_extraction":
            # Extract dynamic data from websites
            url = request.parameters.get("url")
            selectors = request.parameters.get("selectors", {})
            wait_for_element = request.parameters.get("wait_for_element")
            
            if not url or not selectors:
                raise HTTPException(status_code=400, detail="URL and selectors are required for web scraping")
            
            result = await playwright_service.extract_dynamic_data(url, selectors, wait_for_element)
            
        elif request.automation_type == "linkedin_insights":
            # Scrape LinkedIn insights
            email = request.parameters.get("email")
            password = request.parameters.get("password")
            insight_type = request.parameters.get("insight_type", "notifications")
            
            if not email or not password:
                raise HTTPException(status_code=400, detail="LinkedIn email and password are required")
            
            result = await playwright_service.scrape_linkedin_insights(email, password, insight_type)
            
        elif request.automation_type == "email_automation":
            # Automate email interactions
            provider = request.parameters.get("provider")
            email = request.parameters.get("email")
            password = request.parameters.get("password")
            action = request.parameters.get("action", "check_inbox")
            
            if not all([provider, email, password]):
                raise HTTPException(status_code=400, detail="Provider, email, and password are required")
            
            result = await playwright_service.automate_email_interaction(
                provider, email, password, action, **request.parameters.get("action_params", {})
            )
            
        elif request.automation_type == "price_monitoring":
            # Monitor e-commerce prices
            product_url = request.parameters.get("product_url")
            price_selector = request.parameters.get("price_selector")
            product_name = request.parameters.get("product_name")
            
            if not product_url or not price_selector:
                raise HTTPException(status_code=400, detail="Product URL and price selector are required")
            
            result = await playwright_service.monitor_ecommerce_price(product_url, price_selector, product_name)
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported automation type: {request.automation_type}")
        
        # Save automation result to database
        automation_record = {
            "id": str(uuid.uuid4()),
            "session_id": request.session_id,
            "automation_type": request.automation_type,
            "parameters": request.parameters,
            "result": result.data if result else {},
            "success": result.success if result else False,
            "message": result.message if result else "Unknown error",
            "execution_time": result.execution_time if result else 0,
            "timestamp": datetime.utcnow()
        }
        
        await db.automation_logs.insert_one(automation_record)
        
        return {
            "success": result.success if result else False,
            "data": result.data if result else {},
            "message": result.message if result else "Automation failed",
            "execution_time": result.execution_time if result else 0,
            "automation_id": automation_record["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web automation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/gmail-automation")
async def execute_gmail_automation(request: dict):
    """
    Execute Gmail automation tasks
    """
    try:
        action = request.get("action")
        params = request.get("parameters", {})
        
        if action == "check_inbox":
            result = gmail_service.get_inbox_messages(
                max_results=params.get("max_results", 10),
                query=params.get("query")
            )
        elif action == "unread_count":
            result = gmail_service.get_unread_count()
        elif action == "search":
            result = gmail_service.search_emails(
                query=params.get("query", ""),
                max_results=params.get("max_results", 10)
            )
        elif action == "send":
            result = gmail_service.send_email(
                to=params.get("to"),
                subject=params.get("subject"),
                body=params.get("body"),
                cc=params.get("cc"),
                bcc=params.get("bcc")
            )
        elif action == "mark_read":
            result = gmail_service.mark_as_read(params.get("message_ids", []))
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported Gmail action: {action}")
        
        return result
        
    except Exception as e:
        logger.error(f"Gmail automation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/gmail-auth-status")
async def get_gmail_auth_status():
    """Check Gmail authentication status"""
    try:
        if gmail_service.service:
            profile = gmail_service.get_user_profile()
            return {
                "authenticated": True,
                "email_address": profile.get("email_address"),
                "status": "Connected to Gmail API"
            }
        else:
            return {
                "authenticated": False,
                "status": "Gmail API not authenticated. Please run authentication flow."
            }
    except Exception as e:
        return {
            "authenticated": False,
            "status": f"Authentication check failed: {str(e)}"
        }

@api_router.get("/automation-history/{session_id}")
async def get_automation_history(session_id: str):
    """Get automation history for a session"""
    try:
        logger.info(f"Getting automation history for session: {session_id}")
        
        automation_logs = await db.automation_logs.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).to_list(50)  # Get latest 50 records
        
        # Convert ObjectIds to strings for JSON serialization
        serializable_logs = [convert_objectid_to_str(log) for log in automation_logs]
        
        return {"automation_history": serializable_logs}
    except Exception as e:
        logger.error(f"Automation history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
async def root():
    return {"message": "Elva AI Backend is running! 🤖✨", "version": "1.0"}

@api_router.get("/")
async def root():
    return {"message": "Elva AI Backend with Advanced Hybrid Routing! 🤖✨🧠", "version": "2.0"}

# Health check endpoint - Enhanced for advanced hybrid system
@api_router.get("/health")
async def health_check():
    try:
        # Test MongoDB connection
        await db.command("ping")
        
        health_status = {
            "status": "healthy",
            "mongodb": "connected",
            "advanced_hybrid_ai_system": {
                "version": "2.0",
                "groq_api_key": "configured" if os.getenv("GROQ_API_KEY") else "missing",
                "claude_api_key": "configured" if os.getenv("CLAUDE_API_KEY") else "missing",
                "groq_model": "llama3-8b-8192",
                "claude_model": "claude-3-5-sonnet-20241022",
                "sophisticated_features": {
                    "task_classification": [
                        "primary_intent", "emotional_complexity", "professional_tone", 
                        "creative_requirement", "technical_complexity", "response_length",
                        "user_engagement_level", "context_dependency", "reasoning_type"
                    ],
                    "routing_strategies": [
                        "intent_based", "emotional_routing", "professional_routing",
                        "creative_routing", "sequential_execution", "context_enhancement"
                    ],
                    "advanced_capabilities": [
                        "conversation_history_tracking", "context_aware_responses",
                        "fallback_mechanisms", "confidence_scoring", "routing_explanation"
                    ]
                },
                "routing_models": {
                    "claude_tasks": ["high_emotional", "creative_content", "conversational", "professional_warm"],
                    "groq_tasks": ["logical_reasoning", "structured_analysis", "technical_complex", "intent_detection"],
                    "sequential_tasks": ["professional_emails", "linkedin_posts", "complex_creative"],
                    "web_automation_tasks": ["web_scraping", "linkedin_insights", "email_automation", "price_monitoring", "data_extraction"],
                    "gmail_integration_tasks": ["gmail_check_inbox", "gmail_unread_count", "gmail_search", "gmail_send", "gmail_mark_read"]
                }
            },
            "n8n_webhook": "configured" if os.getenv("N8N_WEBHOOK_URL") else "missing",
            "playwright_service": {
                "status": "available",
                "browser": "chromium",
                "capabilities": [
                    "dynamic_data_extraction", "linkedin_insights_scraping", 
                    "email_automation", "price_monitoring", "stealth_mode"
                ]
            },
            "gmail_service": {
                "status": "available" if gmail_service.service else "not_authenticated",
                "authenticated": bool(gmail_service.service),
                "capabilities": [
                    "inbox_checking", "email_sending", "email_search", 
                    "unread_count", "mark_as_read", "oauth2_authentication"
                ]
            }
        }
        
        return health_status
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    # Close Playwright service
    await playwright_service.close()
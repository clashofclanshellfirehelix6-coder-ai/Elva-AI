import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from playwright_service import playwright_service

logger = logging.getLogger(__name__)

class DirectAutomationHandler:
    """
    Handler for direct automation intents that bypass AI response generation
    and modal approval, providing immediate automation results
    """
    
    def __init__(self):
        self.automation_templates = {
            "check_linkedin_notifications": {
                "success_template": "🔔 **LinkedIn Notifications** ({count} new)\n{notifications}",
                "error_template": "❌ Unable to check LinkedIn notifications: {error}",
                "automation_type": "linkedin_insights"
            },
            "scrape_price": {
                "success_template": "💰 **Price Check Results**\n🏷️ **{product}**: {price}\n📊 Platform: {platform}",
                "error_template": "❌ Unable to find price for {product}: {error}",
                "automation_type": "price_monitoring"
            },
            "scrape_product_listings": {
                "success_template": "🛒 **Product Listings** ({count} found)\n{listings}",
                "error_template": "❌ Unable to scrape product listings: {error}",
                "automation_type": "data_extraction"
            },
            "linkedin_job_alerts": {
                "success_template": "💼 **Job Alerts** ({count} new opportunities)\n{jobs}",
                "error_template": "❌ Unable to check job alerts: {error}",
                "automation_type": "linkedin_insights"
            },
            "check_website_updates": {
                "success_template": "🔍 **Website Updates**\n📝 **{website}**: {changes}",
                "error_template": "❌ Unable to check website updates: {error}",
                "automation_type": "web_scraping"
            },
            "monitor_competitors": {
                "success_template": "📊 **Competitor Analysis**\n🏢 **{company}**: {insights}",
                "error_template": "❌ Unable to monitor competitor data: {error}",
                "automation_type": "data_extraction"
            },
            "scrape_news_articles": {
                "success_template": "📰 **Latest News** ({count} articles)\n{articles}",
                "error_template": "❌ Unable to scrape news articles: {error}",
                "automation_type": "web_scraping"
            },
            
            # Gmail automation templates
            "gmail_check_inbox": {
                "success_template": "📧 **Gmail Inbox** ({count} messages)\n{messages}",
                "error_template": "❌ Unable to check Gmail inbox: {error}",
                "automation_type": "gmail_integration"
            },
            "gmail_unread_count": {
                "success_template": "📬 **Unread Emails**: {unread_count} messages",
                "error_template": "❌ Unable to get unread count: {error}",
                "automation_type": "gmail_integration"
            }
        }
    
    async def process_direct_automation(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process direct automation intent and return formatted result
        
        Args:
            intent_data: Intent data from AI detection
            
        Returns:
            Dict containing automation result and formatting info
        """
        intent = intent_data.get("intent")
        template_info = self.automation_templates.get(intent)
        
        if not template_info:
            return {
                "success": False,
                "message": f"❌ Unknown automation intent: {intent}",
                "execution_time": 0,
                "data": {}
            }
        
        logger.info(f"🤖 Processing direct automation: {intent}")
        start_time = datetime.now()
        
        try:
            # Route to appropriate automation handler
            automation_type = template_info["automation_type"]
            
            if automation_type == "linkedin_insights":
                result = await self._handle_linkedin_automation(intent, intent_data)
            elif automation_type == "price_monitoring":
                result = await self._handle_price_automation(intent, intent_data)
            elif automation_type == "data_extraction":
                result = await self._handle_data_extraction(intent, intent_data)
            elif automation_type == "web_scraping":
                result = await self._handle_web_scraping(intent, intent_data)
            elif automation_type == "gmail_integration":
                result = await self._handle_gmail_automation(intent, intent_data)
            else:
                result = {"success": False, "data": {}, "message": "Unknown automation type"}
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Format result using template
            if result["success"]:
                formatted_message = self._format_success_result(intent, result["data"], template_info)
            else:
                formatted_message = template_info["error_template"].format(
                    error=result.get("message", "Unknown error"),
                    **intent_data
                )
            
            return {
                "success": result["success"],
                "message": formatted_message,
                "execution_time": execution_time,
                "data": result["data"],
                "automation_intent": intent
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Direct automation error for {intent}: {e}")
            
            error_message = template_info["error_template"].format(
                error=str(e),
                **intent_data
            )
            
            return {
                "success": False,
                "message": error_message,
                "execution_time": execution_time,
                "data": {},
                "automation_intent": intent
            }
    
    async def _handle_linkedin_automation(self, intent: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LinkedIn-related automation"""
        try:
            if intent == "check_linkedin_notifications":
                # For demo purposes, simulate notification check
                # In production, this would use playwright_service.scrape_linkedin_insights
                mock_notifications = [
                    {"type": "connection", "name": "John Doe", "message": "wants to connect"},
                    {"type": "message", "name": "Sarah Smith", "message": "sent you a message"},
                    {"type": "post_like", "name": "Mike Johnson", "message": "liked your post"}
                ]
                
                return {
                    "success": True,
                    "data": {
                        "count": len(mock_notifications),
                        "notifications": mock_notifications
                    },
                    "message": "Notifications retrieved successfully"
                }
            
            elif intent == "linkedin_job_alerts":
                # For demo purposes, simulate job alerts
                mock_jobs = [
                    {
                        "title": "Senior Software Engineer", 
                        "company": "Tech Corp", 
                        "location": "Remote",
                        "posted": "2 days ago"
                    },
                    {
                        "title": "Full Stack Developer", 
                        "company": "StartupX", 
                        "location": "New York",
                        "posted": "1 day ago"
                    }
                ]
                
                return {
                    "success": True,
                    "data": {
                        "count": len(mock_jobs),
                        "jobs": mock_jobs
                    },
                    "message": "Job alerts retrieved successfully"
                }
            
            return {"success": False, "data": {}, "message": "LinkedIn automation not implemented"}
            
        except Exception as e:
            return {"success": False, "data": {}, "message": str(e)}
    
    async def _handle_price_automation(self, intent: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle price monitoring automation"""
        try:
            product = intent_data.get("product", "Unknown Product")
            platform = intent_data.get("platform", "amazon")
            
            # For demo purposes, simulate price check
            # In production, this would use playwright_service.monitor_ecommerce_price
            mock_prices = {
                "amazon": "$299.99",
                "flipkart": "₹24,999",
                "ebay": "$279.95"
            }
            
            price = mock_prices.get(platform.lower(), "$0.00")
            
            return {
                "success": True,
                "data": {
                    "product": product,
                    "price": price,
                    "platform": platform.title(),
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "message": "Price retrieved successfully"
            }
            
        except Exception as e:
            return {"success": False, "data": {}, "message": str(e)}
    
    async def _handle_data_extraction(self, intent: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data extraction automation"""
        try:
            if intent == "scrape_product_listings":
                category = intent_data.get("category", "electronics")
                platform = intent_data.get("platform", "amazon")
                
                # For demo purposes, simulate product listings
                mock_listings = [
                    {
                        "name": "Gaming Laptop X1",
                        "price": "$1,299.99",
                        "rating": "4.5/5",
                        "reviews": "1,234"
                    },
                    {
                        "name": "Professional Laptop Pro",
                        "price": "$899.99", 
                        "rating": "4.3/5",
                        "reviews": "856"
                    },
                    {
                        "name": "Budget Laptop Lite",
                        "price": "$499.99",
                        "rating": "4.1/5", 
                        "reviews": "423"
                    }
                ]
                
                return {
                    "success": True,
                    "data": {
                        "count": len(mock_listings),
                        "listings": mock_listings,
                        "category": category,
                        "platform": platform
                    },
                    "message": "Product listings retrieved successfully"
                }
            
            elif intent == "monitor_competitors":
                company = intent_data.get("company", "Unknown Company")
                data_type = intent_data.get("data_type", "pricing")
                
                # For demo purposes, simulate competitor analysis
                mock_insights = {
                    "pricing": "Competitor reduced prices by 15% this week",
                    "products": "2 new products launched in Q1",
                    "marketing": "Increased social media activity by 40%"
                }
                
                insights = mock_insights.get(data_type, "No insights available")
                
                return {
                    "success": True,
                    "data": {
                        "company": company,
                        "insights": insights,
                        "data_type": data_type,
                        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "message": "Competitor analysis completed"
                }
            
            return {"success": False, "data": {}, "message": "Data extraction not implemented"}
            
        except Exception as e:
            return {"success": False, "data": {}, "message": str(e)}
    
    async def _handle_web_scraping(self, intent: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle web scraping automation"""
        try:
            if intent == "check_website_updates":
                website = intent_data.get("website", "Unknown Website")
                section = intent_data.get("section", "homepage")
                
                # For demo purposes, simulate website update check
                mock_changes = [
                    "New blog post published: 'AI Trends 2025'",
                    "Product pricing updated in shop section",
                    "2 new team member profiles added"
                ]
                
                return {
                    "success": True,
                    "data": {
                        "website": website,
                        "changes": "\n".join([f"• {change}" for change in mock_changes]),
                        "section": section,
                        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "message": "Website updates retrieved successfully"
                }
            
            elif intent == "scrape_news_articles":
                topic = intent_data.get("topic", "technology")
                source = intent_data.get("source", "tech news")
                
                # For demo purposes, simulate news scraping
                mock_articles = [
                    {
                        "title": "AI Revolution in Healthcare: New Breakthrough",
                        "source": "Tech Times",
                        "published": "2 hours ago"
                    },
                    {
                        "title": "Quantum Computing Achieves Major Milestone", 
                        "source": "Science Daily",
                        "published": "4 hours ago"
                    },
                    {
                        "title": "Green Technology Investments Surge in 2025",
                        "source": "Clean Energy News",
                        "published": "6 hours ago"
                    }
                ]
                
                return {
                    "success": True,
                    "data": {
                        "count": len(mock_articles),
                        "articles": mock_articles,
                        "topic": topic,
                        "source": source
                    },
                    "message": "News articles retrieved successfully"
                }
            
            return {"success": False, "data": {}, "message": "Web scraping not implemented"}
            
        except Exception as e:
            return {"success": False, "data": {}, "message": str(e)}
    
    async def _handle_gmail_automation(self, intent: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Gmail-related automation"""
        try:
            from gmail_service import gmail_service
            
            if intent == "gmail_check_inbox":
                # Check Gmail inbox
                max_results = intent_data.get("max_results", 10)
                query = intent_data.get("query")
                
                # Authenticate if not already done
                if not gmail_service.service:
                    auth_success = gmail_service.authenticate()
                    if not auth_success:
                        return {
                            "success": False,
                            "data": {},
                            "message": "Gmail authentication failed. Please set up Gmail API credentials."
                        }
                
                # Get inbox messages
                result = gmail_service.get_inbox_messages(max_results=max_results, query=query)
                
                if result["success"]:
                    return {
                        "success": True,
                        "data": {
                            "count": result["count"],
                            "messages": result["messages"],
                            "total_in_inbox": result.get("total_in_inbox", 0)
                        },
                        "message": result["message"]
                    }
                else:
                    return {
                        "success": False,
                        "data": {},
                        "message": result.get("error", "Failed to check Gmail inbox")
                    }
            
            elif intent == "gmail_unread_count":
                # Get unread count
                if not gmail_service.service:
                    auth_success = gmail_service.authenticate()
                    if not auth_success:
                        return {
                            "success": False,
                            "data": {},
                            "message": "Gmail authentication failed. Please set up Gmail API credentials."
                        }
                
                result = gmail_service.get_unread_count()
                
                if result["success"]:
                    return {
                        "success": True,
                        "data": {
                            "unread_count": result["unread_count"]
                        },
                        "message": result["message"]
                    }
                else:
                    return {
                        "success": False,
                        "data": {},
                        "message": result.get("error", "Failed to get unread count")
                    }
            
            return {"success": False, "data": {}, "message": "Gmail automation not implemented"}
            
        except Exception as e:
            logger.error(f"Gmail automation error: {e}")
            return {"success": False, "data": {}, "message": str(e)}
    
    def _format_success_result(self, intent: str, data: Dict[str, Any], template_info: Dict[str, str]) -> str:
        """Format successful automation result using template"""
        try:
            if intent == "check_linkedin_notifications":
                notifications_text = "\n".join([
                    f"• **{notif['name']}** {notif['message']}" 
                    for notif in data.get("notifications", [])
                ])
                return template_info["success_template"].format(
                    count=data.get("count", 0),
                    notifications=notifications_text
                )
            
            elif intent == "scrape_price":
                return template_info["success_template"].format(**data)
            
            elif intent == "scrape_product_listings":
                listings_text = "\n".join([
                    f"• **{listing['name']}** - {listing['price']} ⭐ {listing['rating']} ({listing['reviews']} reviews)"
                    for listing in data.get("listings", [])
                ])
                return template_info["success_template"].format(
                    count=data.get("count", 0),
                    listings=listings_text
                )
            
            elif intent == "linkedin_job_alerts":
                jobs_text = "\n".join([
                    f"• **{job['title']}** at {job['company']} ({job['location']}) - {job['posted']}"
                    for job in data.get("jobs", [])
                ])
                return template_info["success_template"].format(
                    count=data.get("count", 0),
                    jobs=jobs_text
                )
            
            elif intent == "check_website_updates":
                return template_info["success_template"].format(**data)
            
            elif intent == "monitor_competitors":
                return template_info["success_template"].format(**data)
            
            elif intent == "scrape_news_articles":
                articles_text = "\n".join([
                    f"• **{article['title']}** ({article['source']}) - {article['published']}"
                    for article in data.get("articles", [])
                ])
                return template_info["success_template"].format(
                    count=data.get("count", 0),
                    articles=articles_text
                )
            
            return f"✅ Automation completed successfully\n{data}"
            
        except Exception as e:
            logger.error(f"Template formatting error: {e}")
            return f"✅ Automation completed successfully\n{data}"
    
    def _format_gmail_success_result(self, intent: str, data: Dict[str, Any], template_info: Dict[str, str]) -> str:
        """Format Gmail automation success result"""
        try:
            if intent == "gmail_check_inbox":
                messages_text = "\n".join([
                    f"• **{msg['subject']}** from {msg['sender']} {'🔴' if msg.get('is_unread') else ''}\n  {msg['body_preview'][:100]}..."
                    for msg in data.get("messages", [])[:5]  # Show first 5 messages
                ])
                return template_info["success_template"].format(
                    count=data.get("count", 0),
                    messages=messages_text
                )
            
            elif intent == "gmail_unread_count":
                return template_info["success_template"].format(**data)
            
            return f"✅ Gmail automation completed successfully\n{data}"
            
        except Exception as e:
            logger.error(f"Gmail template formatting error: {e}")
            return f"✅ Gmail automation completed successfully\n{data}"

# Global instance
direct_automation_handler = DirectAutomationHandler()
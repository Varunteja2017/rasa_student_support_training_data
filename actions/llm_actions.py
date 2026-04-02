import os
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from groq import Groq
from dotenv import load_dotenv
import yaml
import requests

# Load environment variables
load_dotenv()

def load_responses_from_domain():
    """
    Load responses from domain.yml file
    """
    try:
        domain_path = os.path.join(os.path.dirname(__file__), '..', 'domain.yml')
        with open(domain_path, 'r', encoding='utf-8') as file:
            domain_data = yaml.safe_load(file)
            return domain_data.get('responses', {})
    except Exception as e:
        print(f"Error loading domain.yml: {e}")
        return {}

def get_intent_response_text(intent: str, responses: Dict) -> str:
    """
    Get response text for a specific intent from domain.yml responses
    """
    # Map intent names to response names (utter_<intent_name>)
    response_key = f"utter_{intent}"
    
    response_data = responses.get(response_key, [])
    if response_data and len(response_data) > 0:
        return response_data[0].get('text', '')
    
    return ""

def get_llm_response(user_query: str, intent: str = "", ticket_data: Dict = None, conversation_history: List = None, language: str = "en") -> str:
    """Get intelligent response from Groq LLM using answers from domain.yml with conversation memory"""
    
    # Initialize Groq client with API key
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        if language == "te":
            return "నేను ప్రస్తుతం కనెక్ట్ చేయడంలో సమస్య ఎదుర్కొంటున్నాను. దయచేసి కళాశాల కార్యాలయాన్ని 8466997201 లేదా principal@cbit.ac.in వద్ద సంప్రదించండి."
        return "I'm having trouble connecting right now. Please contact the college office at 8466997201 or email principal@cbit.ac.in for assistance."
    
    groq_client = Groq(api_key=api_key)
    
    # Load responses from domain.yml
    responses = load_responses_from_domain()
    
    # Get the answer text for this intent from domain.yml
    context = get_intent_response_text(intent, responses)
    
    # Add ticket data to context if available - FORMAT IT PROPERLY
    if ticket_data:
        if 'tickets' in ticket_data:
            context += f"\n\n===== USER'S TICKETS (Total: {ticket_data.get('total_tickets', 0)}) =====\n"
            for idx, ticket in enumerate(ticket_data['tickets'], 1):
                context += f"\n🎫 TICKET #{idx}:\n"
                # Show only last 8 chars of ticket ID (matching frontend format)
                ticket_id = ticket.get('id', 'N/A')
                short_id = f"#{ticket_id[-8:].upper()}" if ticket_id != 'N/A' and len(ticket_id) > 8 else ticket_id
                context += f"• Ticket ID: {short_id}\n"
                context += f"• Title: {ticket.get('title', 'N/A')}\n"
                context += f"• Status: {ticket.get('status', 'N/A')}\n"
                context += f"• Description: {ticket.get('description', 'N/A')}\n"
                context += f"• Created: {ticket.get('created_at', 'N/A')}\n"
            context += "\n[IMPORTANT: Display ALL these tickets in your response]"
        elif 'recent_ticket' in ticket_data:
            ticket = ticket_data['recent_ticket']
            context += f"\n\n===== MOST RECENT TICKET =====\n"
            # Show only last 8 chars of ticket ID (matching frontend format)
            ticket_id = ticket.get('id')
            short_id = f"#{ticket_id[-8:].upper()}" if ticket_id and len(ticket_id) > 8 else ticket_id
            context += f"• Ticket ID: {short_id}\n"
            context += f"• Title: {ticket.get('title')}\n"
            context += f"• Status: {ticket.get('status')}\n"
            context += f"• Description: {ticket.get('description', 'N/A')}\n"
        elif 'message' in ticket_data:
            context += f"\n\n{ticket_data['message']}"
        elif 'error' in ticket_data:
            context += f"\n\n{ticket_data['error']}"
    
    # Fallback context if intent not found in domain.yml
    if not context:
        context = "Provide accurate information about CBIT (Chaitanya Bharathi Institute of Technology), a premier engineering college in Hyderabad. Answer based on institutional knowledge."
    
    # Add language instruction
    language_instruction = ""
    if language == "te":
        language_instruction = "\n\n🌏 **LANGUAGE REQUIREMENT**: Respond ONLY in Telugu language. Translate all your responses to Telugu (తెలుగు). Use Telugu script throughout."
    
    system_prompt = f"""You are the official CBIT (Chaitanya Bharathi Institute of Technology) AI assistant with complete institutional knowledge.
{language_instruction}

**Context for this query**: {context}

**CRITICAL INSTRUCTIONS**:

**NEVER MENTION**:
❌ "Check the CBIT website"
❌ "Visit www.cbit.ac.in"
❌ "Go to the student portal"
❌ "You can verify on the website"
❌ Any website URLs or portal links
❌ "I'd like to remind you that you can check..."

**You KNOW this information** - State it directly as FACTS. You have complete institutional knowledge.

**ALWAYS SHOW COMPLETE INFORMATION**:

1. **Be thorough and informative** - Provide complete answers with ALL relevant details from context
2. **For tickets**: 
   - When asked "show my tickets" → Display EVERY SINGLE ticket with COMPLETE details
   - Show: Ticket ID, Title, Status, Description (full text), Created date, Assigned to
   - Use emoji 🎫 and bullet points for each ticket
   - NEVER say "You have X tickets" without listing ALL of them completely
3. **For procedural queries** (admission, fees, documents):
   - Provide step-by-step procedures
   - Include all requirements, timings, contacts, fees
   - Don't just say "visit office" - give complete process
4. **For information queries** (contact, exam dates, etc):
   - Provide ALL relevant information from context
   - Include phone numbers, emails, addresses, timings
5. **For follow-ups** ("where?", "tell me more"):
   - Re-provide the complete information from previous context
   - Don't just reference it - show it again

**CONVERSATION MEMORY**:
- Remember previous messages in this conversation
- If user asks "tell me more", "where?", "what about that?" → Expand on the previous topic with more details
- Reference previous context naturally

**Your role**: Help students with queries about:
- Admissions, Fees, Documents, Examinations
- Contact information, Technical issues
- Grievances, Ticket tracking

**Response Guidelines**:
1. **Always display complete information** - Use ALL details from the context
2. **For tickets** - Show EVERY field: ID, title, status, description, created date, assigned to
3. **Be specific** - Include numbers, dates, URLs, contacts
4. **Use simple formatting** - Use bullet points (•) and line breaks, NO markdown
5. **Never use** - **bold**, *italic*, ##headers, or any markdown syntax
6. **Never abbreviate** - Show full details, don't summarize

**FORMATTING RULES**:
- Use plain text only
- Use bullet points (•) for lists
- Use line breaks for structure
- NO ** for bold
- NO * for italic  
- NO ## for headers
- NO markdown syntax

**Examples**:

User: "Show my tickets"
Bot: "Here are your 3 tickets:

🎫 TICKET #1:
• Ticket ID: #ABC12345
• Title: ERP Login Issue
• Status: OPEN
• Description: Cannot login to ERP portal showing invalid credentials error
• Created: 2026-01-10

🎫 TICKET #2:
• Ticket ID: #DEF67890
• Title: Fee Receipt Required
• Status: RESOLVED
• Description: Need official fee receipt for semester 1
• Created: 2026-01-08

🎫 TICKET #3:
• Ticket ID: #GHI24680
• Title: Hall Ticket Download
• Status: IN PROGRESS
• Description: Unable to download hall ticket from website
• Created: 2026-01-12"

User: "What's the admission procedure?"
Bot: "Here's the complete admission procedure:

Step 1: Check Eligibility
- 10+2 with 45% in PCM
- Valid EAMCET/JEE score

Step 2: Counseling
- Register at tseamcet.nic.in
- Attend certificate verification
- Select CBIT in options

[...all steps with complete details...]"

**Response format**: Complete and detailed - always show full information from the context without abbreviation.
"""

    try:
        # Build messages with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if available - keep more context for better responses
        if conversation_history:
            messages.extend(conversation_history[-30:])  # Last 15 exchanges (user + bot)
        
        # Add current user message
        messages.append({"role": "user", "content": user_query})
        
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.7,
            # No max_tokens limit - let LLM generate complete responses without restrictions
            top_p=1,
        )
        
        llm_response = response.choices[0].message.content.strip()
        
        # LOG FULL RESPONSE FOR DEBUGGING
        print("\n" + "="*80)
        print("🤖 FULL LLM RESPONSE:")
        print("="*80)
        print(llm_response)
        print("="*80)
        print(f"Response Length: {len(llm_response)} characters")
        print("="*80 + "\n")
        
        return llm_response
    except Exception as e:
        print(f"LLM Error: {e}")
        return f"I'm having trouble connecting right now. Please contact the college office at 8466997201 or email principal@cbit.ac.in for assistance."


class ActionLLMResponse(Action):
    """Main action for intelligent LLM responses with conversation memory"""
    
    def name(self) -> Text:
        return "action_llm_response"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        intent = tracker.latest_message.get('intent', {}).get('name', '')
        
        # Get language from metadata
        metadata = tracker.latest_message.get('metadata', {})
        language = metadata.get('language', 'en')
        
        print(f"🌏 User language preference: {language}")
        
        # Get conversation history from tracker
        conversation_history = []
        events = tracker.events
        
        # Extract last few user and bot messages
        for event in events[-40:]:  # Look at last 40 events for better context
            if event.get('event') == 'user':
                conversation_history.append({
                    "role": "user",
                    "content": event.get('text', '')
                })
            elif event.get('event') == 'bot' and event.get('text'):
                conversation_history.append({
                    "role": "assistant",
                    "content": event.get('text', '')
                })
        
        # Get LLM response with conversation history and language
        response = get_llm_response(user_message, intent, None, conversation_history, language)
        
        # LOG WHAT WE'RE SENDING TO USER
        print("\n" + "="*80)
        print("📤 DISPATCHING TO USER:")
        print("="*80)
        print(response)
        print("="*80)
        print(f"Dispatched Length: {len(response)} characters")
        print("="*80 + "\n")
        
        dispatcher.utter_message(text=response)
        return []


class ActionFallback(Action):
    """Fallback action when intent is unclear with conversation memory"""
    
    def name(self) -> Text:
        return "action_fallback"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        
        # Get language from metadata
        metadata = tracker.latest_message.get('metadata', {})
        language = metadata.get('language', 'en')
        
        # Get conversation history
        conversation_history = []
        events = tracker.events
        for event in events[-20:]:
            if event.get('event') == 'user':
                conversation_history.append({"role": "user", "content": event.get('text', '')})
            elif event.get('event') == 'bot' and event.get('text'):
                conversation_history.append({"role": "assistant", "content": event.get('text', '')})
        
        # Use LLM for fallback with conversation history and language
        response = get_llm_response(user_message, "", None, conversation_history, language)
        
        dispatcher.utter_message(text=response)
        return []


class ActionCheckTickets(Action):
    """Action to fetch and display user's tickets from backend API"""
    
    def name(self) -> Text:
        return "action_check_tickets"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        intent = tracker.latest_message.get('intent', {}).get('name', '')
        
        # Get user ID from slot or metadata (you may need to adjust based on your auth system)
        # For now, we'll try to get it from sender_id or a slot
        user_id = tracker.sender_id
        
        # Try to get auth token from metadata
        metadata = tracker.latest_message.get('metadata', {})
        auth_token = metadata.get('auth_token', '')
        
        ticket_data = None
        
        # Backend API base URL
        api_base_url = "http://localhost:8000"
        
        # Check if user is authenticated
        if not auth_token:
            response_text = "To view your tickets, please log in first. Once logged in, I can show you all your support tickets, their status, and help track their progress."
            dispatcher.utter_message(text=response_text)
            return []
        
        try:
            # Prepare headers with auth token
            headers = {'Authorization': f'Bearer {auth_token}'}
            
            # Fetch tickets based on intent
            if intent == "ask_my_tickets" or intent == "ask_ticket_history":
                # Get all user tickets
                response = requests.get(
                    f"{api_base_url}/tickets/my",
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    tickets = response.json()
                    
                    if tickets and len(tickets) > 0:
                        # Format ALL tickets for LLM (no limit)
                        ticket_summary = []
                        for ticket in tickets:  # Show ALL tickets
                            ticket_summary.append({
                                'id': ticket.get('_id'),
                                'title': ticket.get('title'),
                                'status': ticket.get('status'),
                                'description': ticket.get('description'),
                                'created_at': ticket.get('created_at'),
                                'assigned_to': ticket.get('assigned_to', 'Unassigned')
                            })
                        
                        ticket_data = {
                            'total_tickets': len(tickets),
                            'tickets': ticket_summary
                        }
                    else:
                        ticket_data = {'message': 'No tickets found. You can create a new ticket if you need assistance.'}
                elif response.status_code == 401:
                    response_text = "Your session has expired. Please log in again to view your tickets."
                    dispatcher.utter_message(text=response_text)
                    return []
                else:
                    ticket_data = {'error': f'Unable to fetch tickets (Status: {response.status_code}). Please check the My Tickets page or try again later.'}
                        
            elif intent == "ask_ticket_status":
                # Get all tickets and let LLM explain the most recent one
                response = requests.get(
                    f"{api_base_url}/tickets/my",
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    tickets = response.json()
                    if tickets and len(tickets) > 0:
                        recent_ticket = tickets[0]  # Get most recent ticket
                        ticket_data = {
                            'recent_ticket': {
                                'id': recent_ticket.get('_id'),
                                'title': recent_ticket.get('title'),
                                'status': recent_ticket.get('status'),
                                'description': recent_ticket.get('description'),
                                'last_updated': recent_ticket.get('updated_at')
                            }
                        }
                    else:
                        ticket_data = {'message': 'No tickets found.'}
                elif response.status_code == 401:
                    response_text = "Your session has expired. Please log in again to check ticket status."
                    dispatcher.utter_message(text=response_text)
                    return []
                else:
                    ticket_data = {'error': 'Unable to fetch ticket status. Please try again.'}
        
        except requests.exceptions.Timeout:
            print("Backend API timeout")
            ticket_data = {'error': 'The ticket system is taking too long to respond. Please try again in a moment.'}
        except requests.exceptions.ConnectionError:
            print("Cannot connect to backend API")
            ticket_data = {'error': 'Cannot connect to the ticket system. The backend server may be down. Please try again later or visit the My Tickets page.'}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tickets from backend: {e}")
            ticket_data = {'error': 'Unable to fetch ticket data. Please try again or check the My Tickets page.'}
        
        # Get language from metadata
        metadata = tracker.latest_message.get('metadata', {})
        language = metadata.get('language', 'en')
        
        # Get conversation history
        conversation_history = []
        events = tracker.events
        for event in events[-20:]:
            if event.get('event') == 'user':
                conversation_history.append({"role": "user", "content": event.get('text', '')})
            elif event.get('event') == 'bot' and event.get('text'):
                conversation_history.append({"role": "assistant", "content": event.get('text', '')})
        
        # Get LLM response with ticket data context, conversation history, and language
        response_text = get_llm_response(user_message, intent, ticket_data, conversation_history, language)
        
        dispatcher.utter_message(text=response_text)
        return []


class ActionCreateTicketFallback(Action):
    """Guide user to create a support ticket for queries that Rasa cannot handle - but check FAQ first"""
    
    def name(self) -> Text:
        return "action_create_ticket_fallback"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        
        # First, try to find similar FAQ
        try:
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            faq_search_url = f"{backend_url}/api/faq/search"
            
            faq_payload = {
                "query": user_message,
                "limit": 3,
                "min_similarity": 0.6  # 60% similarity threshold
            }
            
            response = requests.post(
                faq_search_url,
                json=faq_payload,
                timeout=5
            )
            
            if response.status_code == 200:
                faqs = response.json()
                
                if faqs and len(faqs) > 0:
                    # Found matching FAQ!
                    top_faq = faqs[0]
                    similarity = top_faq.get('similarity_score', 0)
                    
                    # Update FAQ usage count
                    faq_id = top_faq.get('_id')
                    if faq_id:
                        db_url = f"{backend_url}/api/faq/{faq_id}/increment-usage"
                        try:
                            requests.post(db_url, timeout=2)
                        except:
                            pass  # Don't fail if usage tracking fails
                    
                    # Use LLM to make FAQ answer conversational and human-like
                    # Get language from metadata
                    metadata = tracker.latest_message.get('metadata', {})
                    language = metadata.get('language', 'en')
                    
                    llm_prompt = f"""A student asked: "{user_message}"

I found this answer in our FAQ database:
{top_faq['answer']}

Please rephrase this answer in a friendly, conversational way as if you're a helpful college assistant. Keep all important details but make it sound natural and human. Add appropriate emojis where suitable."""
                    
                    conversational_answer = get_llm_response(llm_prompt, "faq", None, None, language)
                    
                    # Format FAQ response with conversational answer
                    confidence_text = f" (Match: {int(similarity * 100)}%)" if similarity > 0.7 else ""
                    faq_response = f"""Here is an answer to your question from faq!{confidence_text}

{conversational_answer}

💡 This answer comes from our knowledge base

Wasn't this helpful?"""
                    
                    # Show buttons
                    buttons = [
                        {"title": "👎 Not Helpful - Create Ticket", "payload": "/ask_create_ticket"},
                        {"title": "🏠 Main Menu", "payload": "/back_to_menu"},
                    ]
                    
                    dispatcher.utter_message(text=faq_response, buttons=buttons)
                    return []
        
        except Exception as e:
            print(f"FAQ search error: {e}")
            # Continue to regular fallback if FAQ search fails
        
        # No FAQ found - guide to create ticket
        response_text = f"""❌ I apologize, but I don't have specific information about: "{user_message}"

🎫 **Need Help with This?**

I can help you create a support ticket so our team can assist you directly.

**What you can do:**
1. 📝 **Create a Ticket** - Click the button below to submit your query
2. 📞 **Call Directly** - Contact: 040-24193276 (College Office)
3. 📧 **Email** - Send to: support@cbit.ac.in
4. 🏠 **Return to Menu** - Browse other topics

**Your query:** {user_message}

Would you like to create a support ticket for this?"""
        
        # Show options with buttons
        buttons = [
            {"title": "📝 Create Support Ticket", "payload": "/ask_create_ticket"},
            {"title": "🏠 Return to Main Menu", "payload": "/back_to_menu"},
            {"title": "📋 My Tickets", "payload": "/ask_my_tickets"},
            {"title": "✍️ Ask Something Else", "payload": "/ask_custom_question"},
        ]
        
        dispatcher.utter_message(text=response_text, buttons=buttons)
        
        return []


class ActionSearchTicketById(Action):
    """Search for a ticket by ID"""
    
    def name(self) -> Text:
        return "action_search_ticket_by_id"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        message = """🔍 **Search Ticket by ID**

Please provide your ticket ID to search.

**Example formats:**
• #ABC12345
• #51016E51
• #DEF67890

Type the ticket ID below:"""
        
        dispatcher.utter_message(text=message)
        
        return []


class ActionSearchTicket(Action):
    """General ticket search"""
    
    def name(self) -> Text:
        return "action_search_ticket"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        message = """🔍 **Search Tickets**

You can search for tickets using:
• Ticket ID
• Title/Subject
• Status (Open, In Progress, Resolved)
• Date range

**Quick Options:**
1. View all tickets → Click "My Tickets"
2. Search by ID → Provide ticket number
3. Filter by status → Specify status type

What would you like to search by?"""
        
        buttons = [
            {"title": "📋 View All My Tickets", "payload": "/ask_my_tickets"},
            {"title": "🔍 Search by ID", "payload": "/ask_ticket_by_id"},
            {"title": "🏠 Main Menu", "payload": "/back_to_menu"},
        ]
        
        dispatcher.utter_message(text=message, buttons=buttons)
        
        return []


class ActionFAQHelpful(Action):
    """Handle FAQ helpful feedback"""
    
    def name(self) -> Text:
        return "action_faq_helpful"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        # Get FAQ ID from intent entities or text
        intent = tracker.latest_message.get('intent', {}).get('name', '')
        text = tracker.latest_message.get('text', '')
        
        # Extract FAQ ID from payload if present (format: /faq_helpful/FAQ_ID)
        faq_id = None
        if '/' in text:
            parts = text.split('/')
            if len(parts) > 2:
                faq_id = parts[2]
        
        # Send helpful feedback to backend
        if faq_id:
            try:
                backend_url = "http://localhost:8000"
                requests.post(f"{backend_url}/api/faq/{faq_id}/helpful", timeout=2)
            except:
                pass  # Don't fail if tracking fails
        
        # Thank the user
        response = """✅ **Thank you for your feedback!**

I'm glad I could help! 😊

**Need anything else?**"""
        
        buttons = [
            {"title": "✍️ Ask Another Question", "payload": "/ask_custom_question"},
            {"title": "🏠 Main Menu", "payload": "/back_to_menu"},
            {"title": "📋 My Tickets", "payload": "/ask_my_tickets"},
        ]
        
        dispatcher.utter_message(text=response, buttons=buttons)
        
        return []

# Hybrid FAQ System - Rasa + Database Search with GROQ SEMANTIC Matching
# This action handles queries by checking both trained intents and dynamic FAQ database
# Uses Groq LLM for intelligent semantic "similar question" matching

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import os
from pymongo import MongoClient

try:
    from groq import Groq
    GROQ_AVAILABLE = True
    print("✅ Groq library imported successfully")
except ImportError as e:
    GROQ_AVAILABLE = False
    print(f"❌ Groq import failed: {e}")

# Try to use MongoDB directly first, fallback to API if needed
MONGODB_URI = os.getenv("MONGODB_URI")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

print(f"\n📋 smart_faq_handler configuration:")
print(f"   GROQ_AVAILABLE: {GROQ_AVAILABLE}")
print(f"   GROQ_API_KEY set: {'✅ Yes' if GROQ_API_KEY else '❌ No'}")
print(f"   MONGODB_URI set: {'✅ Yes' if MONGODB_URI else '❌ No'}")
print(f"   BACKEND_URL: {BACKEND_URL}\n")

# Initialize Groq client
groq_client = None
if GROQ_AVAILABLE and GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq client initialized successfully")
    except Exception as e:
        print(f"❌ Groq client initialization failed: {e}")
else:
    if not GROQ_AVAILABLE:
        print("⚠️  Groq library not available")
    if not GROQ_API_KEY:
        print("⚠️  GROQ_API_KEY not set in environment")

# Initialize MongoDB connection (will reuse connection)
_mongo_client = None
_mongo_db = None

def get_mongo_db():
    """Get MongoDB connection (reused across calls)"""
    global _mongo_client, _mongo_db
    if _mongo_db is None:
        try:
            _mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
            _mongo_client.admin.command('ping')
            # Connect to the correct database (from .env or default)
            db_name = os.getenv("DATABASE_NAME", "student_support_system")
            _mongo_db = _mongo_client[db_name]
            print(f"✅ MongoDB connected for FAQ search (database: '{db_name}')")
        except Exception as e:
            print(f"⚠️  MongoDB connection failed: {e}. Will try API fallback.")
            _mongo_db = False  # Mark as failed
    return _mongo_db if _mongo_db is not False else None

class ActionSmartQueryHandler(Action):
    """
    Smart query handler with 3-tier fallback:
    1. Check Rasa trained intents (fast, 81 stable queries)
    2. Search FAQ database (real-time, 200+ dynamic queries)
    3. Suggest ticket creation (truly unknown)
    """
    
    def name(self) -> Text:
        return "action_smart_query_handler"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text')
        intent = tracker.latest_message.get('intent', {}).get('name')
        confidence = tracker.latest_message.get('intent', {}).get('confidence', 0)
        
        print(f"Query: {user_message}")
        print(f"Intent: {intent}, Confidence: {confidence}")
        
        # Special case: ask_custom_question should just prompt for input
        if intent == 'ask_custom_question':
            dispatcher.utter_message(
                text="💬 Sure! Please type your question below and I'll do my best to help you.\n\n"
                     "You can ask me anything about:\n"
                     "• Admissions & Eligibility\n"
                     "• Fee Payment & Receipts\n"
                     "• Certificates & Documents\n"
                     "• Exam Schedules & Results\n"
                     "• Technical Issues\n"
                     "• Contact Information\n\n"
                     "Go ahead, type your question! 👇"
            )
            return []
        
        # ===== TIER 1: Groq NLP Understanding (High Confidence Intent) =====
        if confidence >= 0.65:
            print(f"✅ TIER 1 ACTIVATED (confidence {confidence:.2f} >= 0.65)")
            print(f"🧠 TIER 1 GROQ NLP: Processing '{user_message}' with intent '{intent}'")
            
            # Use Groq to understand the query and enhance the response
            groq_response = self.get_groq_response_for_intent(user_message, intent)
            
            if groq_response:
                print(f"✅ Groq enhanced TIER 1 response")
                dispatcher.utter_message(text=groq_response)
                return []
            else:
                # Fallback to domain.yml response if Groq fails
                print(f"⚠️  TIER 1 Groq failed, using domain.yml response")
                dispatcher.utter_message(response=f"utter_{intent}")
                return []
        
        # ===== TIER 2: Groq Semantic Understanding (FAQ + LLM) =====
        print("🧠 Tier 2: Using Groq for semantic FAQ matching...")
        groq_response = self.get_groq_response(user_message)
        
        if groq_response:
            print(f"✅ Tier 2: Groq provided answer")
            
            # Format response
            answer = groq_response["answer"]
            source = groq_response.get("source", "unknown")
            debug_logs = groq_response.get("_debug", "")
            
            message = f"{answer}\n\n"
            
            if source == "groq_semantic_match":
                message += "ℹ️ _This answer is from our FAQ database._\n\n"
            else:
                message += "💡 _This answer is generated by our AI assistant._\n\n"
            
            # Add debug logs temporarily (for troubleshooting)
            if debug_logs:
                message += f"\n🔍 **DEBUG LOG:**\n```\n{debug_logs}\n```"
            
            # Add helpful buttons
            buttons = [
                {"title": "👎 Not Helpful", "payload": "/ask_create_ticket"},
            ]
            
            dispatcher.utter_message(text=message, buttons=buttons)
            return []
        
        # ===== TIER 3: Fallback to Ticket Creation =====
        print("❌ All tiers failed: Suggesting ticket creation")
        self.suggest_ticket(dispatcher, user_message)
        return []
    

    def get_groq_response(self, query: str) -> dict:
        """
        Use Groq to intelligently answer questions:
        1. First checks if user is asking about an existing FAQ topic
        2. If yes, returns the FAQ answer (semantic understanding)
        3. If no, suggests ticket creation (NOT generating answers)
        """
        debug_log = []
        debug_log.append(f"🤖 GROQ_RESPONSE STARTED for: '{query}'")
        
        print(f"🤖🤖🤖 TIER 2 GROQ STARTED 🤖🤖🤖")
        print(f"   groq_client: {groq_client}")
        print(f"   query: '{query}'")
        
        if not groq_client:
            err_msg = "❌ Groq client is None/not available"
            print(err_msg)
            debug_log.append(err_msg)
            return None
        
        try:
            msg = "🤖 Initializing Groq semantic understanding..."
            print(msg)
            debug_log.append(msg)
            
            # Get all active FAQs from database
            msg = "📡 Connecting to MongoDB..."
            print(msg)
            debug_log.append(msg)
            
            db = get_mongo_db()
            print(f"   db object: {db}")
            debug_log.append(f"db object: {db}")
            
            if db:
                msg = "📖 Querying active FAQs from database..."
                print(msg)
                debug_log.append(msg)
                
                faqs = list(db.faq.find({"is_active": True}))
                msg = f"✅ Found {len(faqs)} active FAQs in database"
                print(msg)
                debug_log.append(msg)
                
                if not faqs:
                    msg = "⚠️  No active FAQs found! Skipping semantic matching..."
                    print(msg)
                    debug_log.append(msg)
                else:
                    faq_questions = [f.get('question', '') for f in faqs]
                    print(f"   FAQs: {faq_questions}")
                    debug_log.append(f"FAQs in DB: {faq_questions}")
                
                if faqs:
                    msg = "📝 Building FAQ context for Groq..."
                    print(msg)
                    debug_log.append(msg)
                    
                    # Build comprehensive FAQ context for Groq
                    faq_list = []
                    for i, faq in enumerate(faqs, 1):
                        faq_list.append({
                            "number": i,
                            "question": faq.get("question", ""),
                            "answer": faq.get("answer", ""),
                            "category": faq.get("category", "")
                        })
                    
                    # Use an INTELLIGENT prompt that understands semantic similarity
                    system_prompt = """You are a university student support assistant. You have access to a database of FAQs.

TASK: Given a user question, determine if it's asking about something in the FAQ database.

IMPORTANT RULES:
1. Check for SEMANTIC meaning, not just exact words
2. "entry fee for library" = "What is the entry fee for library?" (SAME TOPIC)
3. "can I borrow books" = "Can I borrow books from library?" (SAME TOPIC)
4. "library timing" = "What are library hours?" (SAME TOPIC)

If the user is asking about an FAQ topic:
- Respond with ONLY the FAQ number (1, 2, 3, etc.) and NOTHING ELSE
Example: "1" or "2"

If the user is NOT asking about any FAQ topic:
- Respond with ONLY: NO_MATCH
Example: NO_MATCH

Do NOT explain, do NOT ask questions - just respond with the number or NO_MATCH."""
                    
                    # Format FAQ list for context
                    faq_context = "Available FAQs in database:\n"
                    for faq in faq_list:
                        faq_context += f"{faq['number']}. [{faq['category']}] Q: {faq['question']}\n"
                    
                    user_message = f"{faq_context}\n\nUser question: {query}\n\nWhich FAQ number (if any) best matches this question? Respond ONLY with number or NO_MATCH."
                    
                    msg = f"🌐 Calling Groq API... (FAQs: {len(faqs)}, User Q: '{query}')"
                    print(msg)
                    debug_log.append(msg)
                    
                    # Call Groq with semantic matching
                    try:
                        message = groq_client.chat.completions.create(
                            messages=[
                                {
                                    "role": "system",
                                    "content": system_prompt
                                },
                                {
                                    "role": "user",
                                    "content": user_message
                                }
                            ],
                            model="llama-3.1-8b-instant",
                            temperature=0,  # Deterministic - no randomness
                            max_tokens=10
                        )
                        
                        response_text = message.choices[0].message.content.strip()
                        msg = f"✅ Groq responded: '{response_text}'"
                        print(msg)
                        debug_log.append(msg)
                    except Exception as groq_call_error:
                        err_msg = f"❌ Groq API call failed: {groq_call_error}"
                        print(err_msg)
                        debug_log.append(err_msg)
                        import traceback
                        traceback.print_exc()
                        response_text = None
                    
                    if response_text:
                        msg = f"📝 Parsing Groq response: '{response_text}'..."
                        print(msg)
                        debug_log.append(msg)
                        
                        # Try to parse the FAQ number from response (handle various formats)
                        try:
                            if response_text.upper().strip() != "NO_MATCH":
                                # Extract number from various formats: '1', '1.', 'FAQ 1', etc.
                                import re
                                number_match = re.search(r'\d+', response_text)
                                if number_match:
                                    faq_number = int(number_match.group())
                                    msg = f"   ✅ Parsed FAQ number: {faq_number} from '{response_text}'"
                                    print(msg)
                                    debug_log.append(msg)
                                else:
                                    err_msg = f"❌ Could not extract number from response: '{response_text}'"
                                    print(err_msg)
                                    debug_log.append(err_msg)
                                    faq_number = None
                                
                                if faq_number and 1 <= faq_number <= len(faqs):
                                    matched_faq = faqs[faq_number - 1]
                                    msg = f"✅ Groq matched FAQ #{faq_number}: '{matched_faq.get('question', '')}'"
                                    print(msg)
                                    debug_log.append(msg)
                                    
                                    # Increment usage count
                                    try:
                                        db.faq.update_one(
                                            {"_id": matched_faq["_id"]},
                                            {"$inc": {"usage_count": 1}}
                                        )
                                        debug_log.append(f"   ✅ Updated usage count")
                                    except Exception as e:
                                        msg = f"   ⚠️  Could not update usage count: {e}"
                                        print(msg)
                                        debug_log.append(msg)
                                    
                                    result = {
                                        "id": str(matched_faq["_id"]),
                                        "question": matched_faq.get("question", ""),
                                        "answer": matched_faq.get("answer", ""),
                                        "category": matched_faq.get("category", ""),
                                        "similarity": 0.95,
                                        "source": "groq_semantic_match",
                                        "_debug": "\n".join(debug_log)
                                    }
                                    msg = f"🎉 RETURNING FROM GROQ SEMANTIC MATCH! (FAQ #{faq_number})"
                                    print(msg)
                                    debug_log.append(msg)
                                    return result
                                else:
                                    err_msg = f"❌ Groq returned invalid FAQ number: {faq_number} (valid: 1-{len(faqs)})"
                                    print(err_msg)
                                    debug_log.append(err_msg)
                            else:
                                msg = f"ℹ️  Groq determined this is NOT an FAQ question (NO_MATCH)"
                                print(msg)
                                debug_log.append(msg)
                                return None  # ← No match, don't generate, suggest ticket
                        except (ValueError, IndexError) as parse_error:
                            err_msg = f"❌ Could not parse Groq response '{response_text}': {parse_error}"
                            print(err_msg)
                            debug_log.append(err_msg)
                            return None  # ← Parsing error, don't generate, suggest ticket
            else:
                err_msg = "❌ MongoDB connection failed (db is None)"
                print(err_msg)
                debug_log.append(err_msg)
            
            # No FAQ found - return None to trigger Tier 3 (ticket suggestion)
            msg = "❌ No FAQ matched and MongoDB failed. Suggesting ticket."
            print(msg)
            debug_log.append(msg)
            return None  # ← NO LLM GENERATION! Just suggest ticket

            
        except Exception as e:
            print(f"❌ Outer Groq error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_groq_response_for_intent(self, user_message: str, intent: str) -> str:
        """
        TIER 1: Use Groq to understand NLP query + generate response based on intent
        """
        if not groq_client:
            print("⚠️  TIER 1 Groq not available, returning None")
            return None
        
        try:
            print(f"🧠 TIER 1: Groq generating response for intent '{intent}'")
            
            # Load domain.yml response as context
            import yaml
            domain_path = os.path.join(os.path.dirname(__file__), '..', 'domain.yml')
            try:
                with open(domain_path, 'r', encoding='utf-8') as f:
                    domain_data = yaml.safe_load(f)
                    responses = domain_data.get('responses', {})
                    response_key = f"utter_{intent}"
                    response_data = responses.get(response_key, [])
                    context_answer = response_data[0].get('text', '') if response_data else ""
            except Exception as e:
                print(f"⚠️  Could not load domain.yml: {e}")
                context_answer = ""
            
            if not context_answer:
                print(f"⚠️  No answer found in domain.yml for '{intent}'")
                return None
            
            # Use Groq to rephrase based on user's ACTUAL question
            system_prompt = f"""You are a helpful CBIT student support assistant. Your role is to answer student questions about CBIT policies and procedures.

Intent: {intent}
Context Answer: {context_answer}

Your task:
1. Understand what the student is REALLY asking
2. Provide a helpful response based on the context answer
3. Make it conversational and friendly
4. Answer ONLY the user's specific question
5. Do NOT mention the word "context" or explain the system

Be concise, helpful, and use simple language."""
            
            message = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=300
            )
            
            groq_response = message.choices[0].message.content.strip()
            print(f"✅ TIER 1 Groq generated response: {groq_response[:100]}...")
            return groq_response
            
        except Exception as e:
            print(f"❌ TIER 1 Groq failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def suggest_ticket(self, dispatcher, query):
        """Suggest creating a ticket when no answer found"""
        message = """😔 I don't have a specific answer for your question right now.

Let me help you create a support ticket so our admin team can assist you!

**Why create a ticket?**
✅ Personalized response from our team
✅ Tracked until resolved
✅ Email notifications on updates
✅ Your question might be added to FAQ to help others!"""
        
        buttons = [
            {"title": "🎫 Create Ticket", "payload": "/create_ticket"},
            {"title": "📞 Contact Info", "payload": "/ask_contact_info"},
            {"title": "🏠 Main Menu", "payload": "/main_menu"}
        ]
        
        dispatcher.utter_message(text=message, buttons=buttons)


class ActionMarkFAQHelpful(Action):
    """Mark FAQ as helpful for analytics"""
    
    def name(self) -> Text:
        return "action_mark_faq_helpful"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Extract FAQ ID from intent entities or slot
        faq_id = tracker.get_slot("faq_id")
        
        if not faq_id:
            dispatcher.utter_message(text="Thank you for your feedback!")
            return []
        
        try:
            url = f"{BACKEND_URL}/api/faq/{faq_id}/helpful"
            response = requests.post(url, timeout=5)
            
            if response.status_code == 200:
                dispatcher.utter_message(
                    text="✅ Thank you! Your feedback helps us improve.\n\nCan I help you with anything else?"
                )
            else:
                dispatcher.utter_message(text="Thank you for your feedback!")
                
        except Exception as e:
            print(f"Error marking FAQ helpful: {e}")
            dispatcher.utter_message(text="Thank you for your feedback!")
        
        return []

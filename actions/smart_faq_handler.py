# Hybrid FAQ System - Rasa + Database Search
# This action handles queries by checking both trained intents and dynamic FAQ database

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import os
from pymongo import MongoClient
from difflib import SequenceMatcher

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
            _mongo_db = _mongo_client["student_support"]
            print("✅ MongoDB connected for FAQ search")
        except Exception as e:
            print(f"⚠️  MongoDB connection failed: {e}. Will try API fallback.")
            _mongo_db = False  # Mark as failed
    return _mongo_db if _mongo_db is not False else None

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts (0-1)"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def keyword_match_score(query: str, keywords: List[str]) -> float:
    """Calculate keyword match score"""
    query_lower = query.lower()
    matches = sum(1 for keyword in keywords if keyword.lower() in query_lower)
    return matches / len(keywords) if keywords else 0

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
        
        # ===== TIER 1: Rasa Trained Intents (High Confidence) =====
        if confidence >= 0.65:
            print("✅ Tier 1: Using Rasa trained response")
            # Let Rasa handle with domain.yml response
            dispatcher.utter_message(response=f"utter_{intent}")
            return []
        
        # ===== TIER 2: Groq Semantic FAQ Matching (Intelligent Understanding) =====
        print("🤖 Tier 2: Using Groq for semantic FAQ matching...")
        groq_response = self.get_groq_response(user_message)
        
        if groq_response:
            print(f"✅ Tier 2: Groq provided answer")
            
            # Format response
            answer = groq_response["answer"]
            source = groq_response.get("source", "unknown")
            
            message = f"{answer}\n\n"
            
            if source == "groq_semantic_match":
                message += "ℹ️ _This answer is from our FAQ database._\n\n"
            else:
                message += "💡 _This answer is generated by our AI assistant._\n\n"
            
            # Add helpful buttons
            buttons = [
                {"title": "👍 Helpful", "payload": "/helpful_feedback"},
                {"title": "👎 Not Helpful", "payload": "/create_ticket"},
                {"title": "🎫 Create Ticket", "payload": "/create_ticket"}
            ]
            
            dispatcher.utter_message(text=message, buttons=buttons)
            return []
        
        # ===== TIER 3: Fallback to Groq Answer Generation =====
        print("❌ Tier 2 (Groq FAQ matching) failed: Generating answer with Groq...")
        groq_answer = self.get_groq_generated_answer(user_message)
        
        if groq_answer:
            print(f"✅ Tier 3: Groq generated an answer")
            
            # Format response
            message = f"{groq_answer}\n\n"
            message += "💡 _This answer is generated by our AI assistant._\n\n"
            
            # Add helpful buttons
            buttons = [
                {"title": "👍 Helpful", "payload": "/helpful_feedback"},
                {"title": "👎 Not Helpful", "payload": "/create_ticket"},
                {"title": "🎫 Create Ticket", "payload": "/create_ticket"}
            ]
            
            dispatcher.utter_message(text=message, buttons=buttons)
            return []
        
        # ===== TIER 4: Fallback to Ticket Creation =====
        print("❌ All Groq tiers failed: Suggesting ticket creation")
        self.suggest_ticket(dispatcher, user_message)
        return []
    
    def search_faq_database(self, query: str) -> dict:
        """
        Search FAQ database for similar questions
        Uses MongoDB directly (no API needed) with fallback to API if needed
        """
        min_similarity = 0.55
        
        # Try MongoDB direct connection first (faster, no API needed)
        db = get_mongo_db()
        if db:
            try:
                print("📊 Searching MongoDB directly...")
                faqs = list(db.faq.find({"is_active": True}))
                
                if not faqs:
                    print("⚠️  No active FAQs in database")
                    return None
                
                # Calculate scores
                best_match = None
                best_score = 0
                
                for faq in faqs:
                    text_sim = calculate_similarity(query, faq.get("question", ""))
                    keyword_sim = keyword_match_score(query, faq.get("keywords", []))
                    combined_score = (text_sim * 0.7) + (keyword_sim * 0.3)
                    
                    if combined_score >= min_similarity and combined_score > best_score:
                        best_match = faq
                        best_score = combined_score
                
                if best_match:
                    # Increment usage count
                    db.faq.update_one(
                        {"_id": best_match["_id"]},
                        {"$inc": {"usage_count": 1}}
                    )
                    
                    return {
                        "id": str(best_match["_id"]),
                        "question": best_match.get("question", ""),
                        "answer": best_match.get("answer", ""),
                        "category": best_match.get("category", ""),
                        "similarity": best_score
                    }
                
                print(f"ℹ️  No FAQ matches above {min_similarity:.0%} threshold")
                return None
                
            except Exception as e:
                print(f"⚠️  MongoDB search error: {e}. Trying API fallback...")
        
        # Fallback to API if MongoDB fails
        try:
            print("📱 Falling back to API search...")
            url = f"{BACKEND_URL}/api/faq/search"
            payload = {
                "query": query,
                "limit": 1,
                "min_similarity": min_similarity
            }
            
            response = requests.post(url, json=payload, timeout=3)
            
            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    top_result = results[0]
                    return {
                        "id": top_result["_id"],
                        "question": top_result["question"],
                        "answer": top_result["answer"],
                        "category": top_result["category"],
                        "similarity": top_result.get("similarity_score", 0)
                    }
            
            return None
            
        except Exception as e:
            print(f"❌ Both MongoDB and API failed: {e}")
            return None
    
    def get_groq_response(self, query: str) -> dict:
        """
        Use Groq to intelligently answer questions:
        1. First checks if user is asking about an existing FAQ topic
        2. If yes, returns the FAQ answer (semantic understanding)
        3. If no, generates a new answer intelligently
        """
        print(f"🤖🤖🤖 TIER 3 GROQ STARTED 🤖🤖🤖")
        print(f"   groq_client: {groq_client}")
        print(f"   query: '{query}'")
        
        if not groq_client:
            print("❌ Groq client is None/not available")
            return None
        
        try:
            print("🤖 Initializing Groq semantic understanding...")
            
            # Get all active FAQs from database
            print("📡 Connecting to MongoDB...")
            db = get_mongo_db()
            print(f"   db object: {db}")
            
            if db:
                print("📖 Querying active FAQs from database...")
                faqs = list(db.faq.find({"is_active": True}))
                print(f"✅ Found {len(faqs)} active FAQs in database")
                
                if not faqs:
                    print("⚠️  No active FAQs found! Skipping semantic matching...")
                else:
                    print(f"   FAQs: {[f.get('question', '') for f in faqs]}")
                
                if faqs:
                    print("📝 Building FAQ context for Groq...")
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
                    
                    print(f"🌐 Calling Groq API...")
                    print(f"   Query: {query}")
                    print(f"   FAQ context: {faq_context[:200]}...")
                    
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
                            model="mixtral-8x7b-32768",
                            temperature=0,  # Deterministic - no randomness
                            max_tokens=10
                        )
                        
                        response_text = message.choices[0].message.content.strip()
                        print(f"✅ Groq API responded: '{response_text}'")
                    except Exception as groq_call_error:
                        print(f"❌ Groq API call failed: {groq_call_error}")
                        import traceback
                        traceback.print_exc()
                        response_text = None
                    
                    if response_text:
                        print(f"📝 Parsing Groq response...")
                        # Try to parse the FAQ number from response
                        try:
                            if response_text.upper() != "NO_MATCH":
                                faq_number = int(response_text)
                                print(f"   Parsed FAQ number: {faq_number}")
                                if 1 <= faq_number <= len(faqs):
                                    matched_faq = faqs[faq_number - 1]
                                    print(f"✅ Groq matched FAQ #{faq_number}: {matched_faq.get('question', '')}")
                                    
                                    # Increment usage count
                                    try:
                                        db.faq.update_one(
                                            {"_id": matched_faq["_id"]},
                                            {"$inc": {"usage_count": 1}}
                                        )
                                        print(f"   ✅ Updated usage count")
                                    except Exception as e:
                                        print(f"   ⚠️  Could not update usage count: {e}")
                                    
                                    result = {
                                        "id": str(matched_faq["_id"]),
                                        "question": matched_faq.get("question", ""),
                                        "answer": matched_faq.get("answer", ""),
                                        "category": matched_faq.get("category", ""),
                                        "similarity": 0.95,
                                        "source": "groq_semantic_match"
                                    }
                                    print(f"🎉 RETURNING FROM GROQ SEMANTIC MATCH!")
                                    return result
                                else:
                                    print(f"❌ Groq returned invalid FAQ number: {faq_number} (valid: 1-{len(faqs)})")
                            else:
                                print(f"ℹ️  Groq determined this is NOT an FAQ question")
                        except (ValueError, IndexError) as parse_error:
                            print(f"❌ Could not parse Groq response '{response_text}': {parse_error}")
            else:
                print("❌ MongoDB connection failed (db is None)")
            
            # If no FAQ matched OR can't reach database, generate intelligent answer
            print("📝 Generating intelligent answer with Groq LLM (fallback)...")
            print(f"   Calling Groq to generate new answer for query: {query}")
            
            try:
                gen_message = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a helpful university student support chatbot. Answer questions intelligently about:
- Library services (fees, borrowing, timing, collections)
- Admissions, enrollment, and fees
- Exam schedules, results, and grading
- Certificates, transcripts, and documents
- Hostel, campus life, transport
- Technical issues and account problems
- General student support

RULES:
1. Keep answers SHORT (2-3 sentences max)
2. Be FRIENDLY and HELPFUL
3. If you don't know, say: "I don't have that information, please create a support ticket"
4. Use simple, clear language
5. Include relevant emojis where appropriate"""
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    model="mixtral-8x7b-32768",
                    temperature=0.3,
                    max_tokens=200
                )
                
                answer = gen_message.choices[0].message.content.strip()
                print(f"✅ Groq generated answer: {answer[:80]}...")
                
                return {
                    "id": "groq_generated",
                    "question": query,
                    "answer": answer,
                    "category": "general",
                    "similarity": 0.90,
                    "source": "groq_llm"
                }
            except Exception as gen_error:
                print(f"❌ Groq answer generation failed: {gen_error}")
                import traceback
                traceback.print_exc()
                return None
            
        except Exception as e:
            print(f"❌ Outer Groq error: {e}")
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

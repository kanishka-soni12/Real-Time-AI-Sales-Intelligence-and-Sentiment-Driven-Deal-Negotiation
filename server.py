import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import pandas as pd
import logging
from datetime import datetime
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from faker import Faker
from groq import Groq

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CRM_FILE = 'crm_data.xlsx'

# NLTK Sentiment Analysis
nltk.download("vader_lexicon", quiet=True)
sia = SentimentIntensityAnalyzer()

# Negotiation Terms Dictionary
NEGOTIATION_TERMS = {
    "product_quality": [
        "We are committed to improving our product quality and welcome your detailed suggestions.",
        "We can offer you a free replacement or upgrade for the product.",
        "Our team will prioritize addressing quality issues in the upcoming releases.",
    ],
    "ui_ux": [
        "We can improve the UI/UX experience by 20% based on your feedback.",
        "Our team is focused on enhancing usability and aesthetics; stay tuned for updates.",
        "We can offer early access to our redesigned user interface for your review.",
    ],
    "pricing": [
        "We can offer a 10% discount on your next purchase.",
        "We are working on competitive pricing strategies to benefit customers.",
        "We can provide additional loyalty points for future transactions.",
    ],
    "delivery_issues": [
        "We will prioritize your future deliveries at no extra cost.",
        "We can offer free express shipping for your next order.",
        "Our logistics team is actively improving delivery timelines.",
    ],
    "customer_support": [
        "We will assign a dedicated support representative to address your concerns.",
        "Our team is enhancing the support system for faster resolutions.",
        "We can provide 24/7 support access to resolve your issues quickly.",
    ],
    "general_feedback": [
        "Thank you for your feedback; we are committed to continuous improvement.",
        "We value your suggestions and are working to enhance our services.",
        "We would love to hear more about how we can improve; please share detailed feedback.",
    ],
}

# Pydantic Models
class TextData(BaseModel):
    text_data: str
    phone_number: str

class PhoneNumberRequest(BaseModel):
    phone_number: str

# CRM Initialization and Management
def initialize_crm():
    if not os.path.exists(CRM_FILE):
        logger.info("CRM file not found. Creating new one...")
        fake = Faker()
        
        data = {
            'phone_number': [],
            'customer_name': [],
            'email': [],
            'last_purchase_date': [],
            'purchase_history': [],
            'customer_segment': [],
            'interaction_history': [],
            'sentiment_history': []
        }
        
        segments = ['Premium', 'Standard', 'Basic']
        
        for _ in range(100):
            data['phone_number'].append(fake.phone_number())
            data['customer_name'].append(fake.name())
            data['email'].append(fake.email())
            data['last_purchase_date'].append(fake.date_between(start_date='-1y', end_date='today'))
            data['purchase_history'].append(fake.random_int(min=100, max=10000))
            data['customer_segment'].append(fake.random_element(segments))
            data['interaction_history'].append([])
            data['sentiment_history'].append([])
        
        df = pd.DataFrame(data)
        df.to_excel(CRM_FILE, index=False)
        logger.info("New CRM file created successfully")

def load_crm_data():
    try:
        if not os.path.exists(CRM_FILE):
            initialize_crm()
        return pd.read_excel(CRM_FILE)
    except Exception as e:
        logger.error(f"Error loading CRM data: {e}")
        raise HTTPException(status_code=500, detail="Error loading CRM data")

def save_crm_data(df):
    try:
        df.to_excel(CRM_FILE, index=False)
        logger.info("CRM data saved successfully")
    except Exception as e:
        logger.error(f"Error saving CRM data: {e}")
        raise HTTPException(status_code=500, detail="Error saving CRM data")

def update_interaction_history(df, phone_number, interaction, sentiment):
    try:
        customer_idx = df[df['phone_number'] == phone_number].index[0]
        
        interaction_history = df.at[customer_idx, 'interaction_history']
        sentiment_history = df.at[customer_idx, 'sentiment_history']
        
        if isinstance(interaction_history, str):
            interaction_history = eval(interaction_history)
        if isinstance(sentiment_history, str):
            sentiment_history = eval(sentiment_history)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        interaction_history.append(f"[{timestamp}] {interaction}")
        sentiment_history.append(f"[{timestamp}] {sentiment}")
        
        df.at[customer_idx, 'interaction_history'] = interaction_history
        df.at[customer_idx, 'sentiment_history'] = sentiment_history
        
        return df
    except Exception as e:
        logger.error(f"Error updating interaction history: {e}")
        raise HTTPException(status_code=500, detail="Error updating interaction history")

def categorize_feedback(feedback):
    feedback = feedback.lower()
    
    if any(word in feedback for word in ["quality", "build", "durability", "performance"]):
        return "product_quality"
    elif any(word in feedback for word in ["ui", "interface", "design", "usability"]):
        return "ui_ux"
    elif any(word in feedback for word in ["price", "cost", "expensive", "cheap"]):
        return "pricing"
    elif any(word in feedback for word in ["delivery", "shipping", "delay"]):
        return "delivery_issues"
    elif any(word in feedback for word in ["support", "service", "help"]):
        return "customer_support"
    else:
        return "general_feedback"

# FastAPI Application Setup
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.get("/")
async def root():
    return {"message": "AI Sales Assistant API is running"}

@app.get("/test")
async def test():
    return {"status": "Backend is running"}

@app.post("/lookup-customer")
async def lookup_customer(request: PhoneNumberRequest):
    logger.info(f"Looking up customer with phone number: {request.phone_number}")
    try:
        df = load_crm_data()
        customer = df[df['phone_number'] == request.phone_number]
        
        if customer.empty:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_data = {
            "customer_name": customer['customer_name'].iloc[0],
            "email": customer['email'].iloc[0],
            "last_purchase_date": str(customer['last_purchase_date'].iloc[0]),
            "purchase_history": float(customer['purchase_history'].iloc[0]),
            "customer_segment": customer['customer_segment'].iloc[0],
            "interaction_history": customer['interaction_history'].iloc[0] 
                if isinstance(customer['interaction_history'].iloc[0], list) 
                else eval(customer['interaction_history'].iloc[0]) 
                if customer['interaction_history'].iloc[0] 
                else []
        }
        
        logger.info(f"Found customer: {customer_data}")
        return customer_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in lookup_customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-speech")
async def analyze_speech(text_data: TextData):
    logger.info(f"Analyzing speech for phone number: {text_data.phone_number}")
    try:
        df = load_crm_data()
        customer_idx = df[df['phone_number'] == text_data.phone_number].index
        
        if len(customer_idx) == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
            
        customer_segment = df.loc[customer_idx[0], 'customer_segment']
        
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
            
        client = Groq(api_key=groq_api_key)
        
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
            "role": "system",
            "content": """Analyze conversation for:
            1. Sentiment: Overall mood, key emotions
            2. Intent: Primary goal, required actions
            3. Tone: Speech style, pitch patterns
            Provide brief bullet points."""
        },
        {
            "role": "user",
            "content": text_data.text_data
        }
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        analysis = response.choices[0].message.content.strip()
        
        df = update_interaction_history(df, text_data.phone_number, text_data.text_data, analysis)
        save_crm_data(df)
        
        return {"analysis": analysis}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in analyze_speech: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-recommendations")
async def get_recommendations(request: PhoneNumberRequest):
    try:
        # Load customer data
        df = load_crm_data()
        customer = df[df['phone_number'] == request.phone_number]
        
        if customer.empty:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Get the latest interaction
        interaction_history = customer.iloc[0]['interaction_history']
        if isinstance(interaction_history, str):
            interaction_history = eval(interaction_history)
            
        if not interaction_history:
            return {"recommendations": ["No interactions found to generate recommendations."]}
            
        # Get the most recent transcription
        latest_interaction = interaction_history[-1]
        # Remove timestamp if present
        if isinstance(latest_interaction, str) and ']' in latest_interaction:
            latest_interaction = latest_interaction.split('] ', 1)[1]
        
        # Categorize the feedback
        feedback_category = categorize_feedback(latest_interaction)
        
        # Generate recommendations based on the feedback category
        recommendations = NEGOTIATION_TERMS.get(feedback_category, 
            NEGOTIATION_TERMS["general_feedback"])
        
        return {"recommendations": recommendations[:3]}  # Return up to 3 recommendations
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/post-call-analysis")
async def post_call_analysis(request: PhoneNumberRequest):
    try:
        # Load customer data
        df = load_crm_data()
        customer = df[df['phone_number'] == request.phone_number]
        
        if customer.empty:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Get the latest interaction
        interaction_history = customer.iloc[0]['interaction_history']
        if isinstance(interaction_history, str):
            interaction_history = eval(interaction_history)
            
        if not interaction_history:
            return {"post_call_analysis": "No interactions found to analyze."}
            
        # Get the most recent transcription
        latest_interaction = interaction_history[-1]
        # Remove timestamp if present
        if isinstance(latest_interaction, str) and ']' in latest_interaction:
            latest_interaction = latest_interaction.split('] ', 1)[1]
        
        # Use Groq for post-call analysis
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
            
        client = Groq(api_key=groq_api_key)
        
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": """Provide a detailed post-call analysis with the following structure:
                    1. Key Discussion Points
                    2. Customer Concerns
                    Be concise but short."""
                },
                {
                    "role": "user",
                    "content": latest_interaction
                }
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        post_call_analysis = response.choices[0].message.content.strip()
        
        return {"post_call_analysis": post_call_analysis}
        
    except Exception as e:
        logger.error(f"Error in post-call analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Application Runner
if __name__ == "__main__":
    import uvicorn
    initialize_crm()
    logger.info("Starting server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
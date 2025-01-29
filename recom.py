import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Predefined negotiation terms for different categories
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

# Initialize sentiment analyzer
nltk.download("vader_lexicon")
sia = SentimentIntensityAnalyzer()

# Categorize feedback into predefined categories
def categorize_feedback(feedback):
    feedback = feedback.lower()
    
    # Keyword-based categorization
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

# Generate negotiation terms based on feedback sentiment and category
def generate_negotiation_terms(feedback):
    category = categorize_feedback(feedback)
    sentiment_score = sia.polarity_scores(feedback)["compound"]
    
    # Tailor response based on sentiment
    if sentiment_score < -0.3:  # Negative feedback
        terms = NEGOTIATION_TERMS.get(category, [])
    elif sentiment_score > 0.3:  # Positive feedback
        terms = ["Thank you for your positive feedback! We value your support."]
    else:  # Neutral feedback
        terms = ["We are reviewing your feedback and will get back to you with improvements."]
    
    if not terms:
        return ["We appreciate your feedback and are working to improve."]
    return terms

# Main function to process CRM data and recommend terms
def recommend_negotiation_terms(phone_number, crm_data_path):
    try:
        # Load CRM data
        crm_data = pd.read_excel(crm_data_path)
        
        # Validate phone number
        customer_data = crm_data[crm_data['phone_number'] == phone_number]
        if customer_data.empty:
            raise ValueError("Customer not found!")
        
        # Get feedback for the customer
        feedback = customer_data.iloc[0]['interaction_history']
        if not feedback or str(feedback).strip() == "":
            raise ValueError("No interaction history found for the customer.")
        
        # Generate negotiation terms
        negotiation_terms = generate_negotiation_terms(feedback)
        
        # Display results
        print(f"\nRecommended Negotiation Terms for Customer ({phone_number}):")
        for i, term in enumerate(negotiation_terms, 1):
            print(f"{i}. {term}")
    
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the recommendation system
if __name__ == "__main__":
    # Path to CRM data file
    crm_data_file = "/Users/srinivas/Desktop/sentiment analysis/crm_data copy.xlsx"
    
    # Input: Phone number
    input_phone_number = input("Enter the customer's phone number: ").strip()
    
    # Generate recommendations
    recommend_negotiation_terms(input_phone_number, crm_data_file)

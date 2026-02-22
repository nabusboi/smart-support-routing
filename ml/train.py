import os
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Simple synthetic data generation for training
# In a real scenario, this would be loaded from a CSV or Database
DATA = [
    # Billing
    ("I need help with my invoice", "Billing"),
    ("My payment failed", "Billing"),
    ("How do I get a refund?", "Billing"),
    ("My subscription plan is wrong", "Billing"),
    ("I was overcharged for this month", "Billing"),
    ("Where can I find my receipt?", "Billing"),
    ("Cancel my subscription", "Billing"),
    ("Update my credit card info", "Billing"),
    ("Transaction history request", "Billing"),
    ("Pricing for the premium tier", "Billing"),
    ("Coupon code not working at checkout", "Billing"),
    ("Renewal date for my plan", "Billing"),
    
    # Technical
    ("The server is down and I can't login", "Technical"),
    ("I found a bug in the dashboard", "Technical"),
    ("The application keeps crashing", "Technical"),
    ("I forgot my password and need a reset", "Technical"),
    ("The API is returning a 500 error", "Technical"),
    ("How do I install the mobile app?", "Technical"),
    ("Connection timeout while loading data", "Technical"),
    ("The website is very slow today", "Technical"),
    ("Database connection issues detected", "Technical"),
    ("Integration setup for third-party tools", "Technical"),
    ("Stack trace error on page load", "Technical"),
    ("Feature request: Dark mode in the UI", "Technical"),
    
    # Legal
    ("I have a question about the privacy policy", "Legal"),
    ("GDPR data deletion request", "Legal"),
    ("Violation of terms of service", "Legal"),
    ("I need to speak with the legal department", "Legal"),
    ("Contract dispute regarding the agreement", "Legal"),
    ("Compliance audit requirements", "Legal"),
    ("Trademark infringement notice", "Legal"),
    ("Intellectual property inquiry", "Legal"),
    ("Update to the end-user license agreement", "Legal"),
    ("Data protection officer contact info", "Legal"),
    ("Regulatory compliance documentation", "Legal"),
    
    # General
    ("Hello, I have a general question", "General"),
    ("Can you tell me more about your company?", "General"),
    ("Just saying hi!", "General"),
    ("I need some help", "General"),
    ("What are your business hours?", "General"),
    ("Where are your offices located?", "General"),
    ("I would like to provide some feedback", "General"),
    ("Who is the CEO of the company?", "General"),
    ("Career opportunities and job openings", "General"),
    ("Contact sales for a partnership", "General"),
    ("Information about your recent press release", "General"),
    ("Thank you for your help!", "General"),
]

def train_model():
    print("Training Logistic Regression model...")
    
    # Split texts and labels
    X, y = zip(*DATA)
    
    # Create a pipeline: TF-IDF Vectorizer -> Logistic Regression
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words='english')),
        ('clf', LogisticRegression(random_state=42, multi_class='multinomial'))
    ])
    
    # Train the model
    pipeline.fit(X, y)
    
    # Save the model
    model_path = os.path.join(os.path.dirname(__file__), 'model.joblib')
    joblib.dump(pipeline, model_path)
    
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_model()

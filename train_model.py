import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib

# Load data
df = pd.read_csv("tickets.csv")

# Use TF-IDF with unigrams and bigrams + Logistic Regression
model = Pipeline([
    ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1, 2))),
    ('lr', LogisticRegression(max_iter=1000))
])

X = df['description']
y = df['department']
model.fit(X, y)

joblib.dump(model, 'ticket_classifier.pkl')

print("✅ Model trained and saved with Logistic Regression + bigrams")

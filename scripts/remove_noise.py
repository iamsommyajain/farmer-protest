import pandas as pd
import re
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

INPUT = os.path.join(BASE_DIR, "step1_loaded.csv")
OUTPUT = os.path.join(BASE_DIR, "step2_cleaned.csv")

df = pd.read_csv(INPUT)

def clean_text(text):
    text = str(text)

    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)

    # Remove mentions
    text = re.sub(r'@\w+', '', text)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

df['tweet_text'] = df['tweet_text'].apply(clean_text)

df.to_csv(OUTPUT, index=False)

print("Step 2 Complete: Noise Removed")
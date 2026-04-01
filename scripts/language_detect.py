import pandas as pd
import os
from langdetect import detect

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

INPUT = os.path.join(BASE_DIR, "step3_deduplicated.csv")
OUTPUT = os.path.join(BASE_DIR, "step4_with_language.csv")

df = pd.read_csv(INPUT)

def detect_lang(text):
    try:
        return detect(str(text))
    except:
        return "unknown"

df['language'] = df['tweet_text'].apply(detect_lang)

df.to_csv(OUTPUT, index=False)

print("Step 4 Complete: Language Detected")
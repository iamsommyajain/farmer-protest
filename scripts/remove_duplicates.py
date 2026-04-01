import pandas as pd
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

INPUT = os.path.join(BASE_DIR, "step2_cleaned.csv")
OUTPUT = os.path.join(BASE_DIR, "step3_deduplicated.csv")

df = pd.read_csv(INPUT)

df = df.drop_duplicates(subset=['tweet_text'])
df = df[df['tweet_text'].str.len() > 10]

df = df.reset_index(drop=True)

df.to_csv(OUTPUT, index=False)

print("Step 3 Complete: Duplicates Removed")
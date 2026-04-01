import pandas as pd
from scripts.utils.text_utils import remove_non_ascii, clean_whitespace

INPUT = "../data/cleaned/step1_encoding_fixed.csv"
OUTPUT = "../data/cleaned/step2_clean_text.csv"

df = pd.read_csv(INPUT)

df['tweet_text'] = df['tweet_text'].apply(remove_non_ascii)
df['tweet_text'] = df['tweet_text'].apply(clean_whitespace)

df.to_csv(OUTPUT, index=False)

print("Step 2 Complete: Text Cleaned")
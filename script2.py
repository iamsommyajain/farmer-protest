import pandas as pd
import re
from ftfy import fix_text

# ===== Step 1: Load dataset safely =====
df = pd.read_csv("final_dataset.csv", encoding='latin1')

# Normalize column names
df.columns = df.columns.str.strip()

# ===== Step 2: Drop useless columns =====
df = df.drop(columns=['ï»¿no'], errors='ignore')

# ===== Step 3: Remove completely empty rows =====
df = df.dropna(how='all')

# Remove rows where tweet_text is empty
df = df[df['tweet_text'].notna()]
df = df[df['tweet_text'].str.strip() != ""]

# ===== Step 4: Encoding + text cleaning =====
def clean_text(text):
    if not isinstance(text, str):
        return text
    
    # Try recovering encoding
    try:
        text = text.encode('latin1').decode('utf-8')
    except:
        pass
    
    text = fix_text(text)
    
    # Remove line breaks
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

for col in ['username', 'tweet_text']:
    if col in df.columns:
        df[col] = df[col].apply(clean_text)

# ===== Step 5: Remove garbage-heavy rows =====
def is_mostly_garbage(text):
    if not isinstance(text, str):
        return True
    
    total = len(text)
    if total == 0:
        return True
    
    garbage = len(re.findall(r'[ý�ï¿½]', text))
    
    return (garbage / total) > 0.3  # threshold

df = df[~df['tweet_text'].apply(is_mostly_garbage)]

# ===== Step 6: Remove leftover garbage characters =====
df['tweet_text'] = df['tweet_text'].str.replace('ý', '', regex=False)
df['tweet_text'] = df['tweet_text'].str.replace('�', '', regex=False)

# ===== Step 7: Reset index cleanly =====
df = df.drop(columns=['no'], errors='ignore')  # remove old index if exists
df = df.reset_index(drop=True)
df.insert(0, 'no', range(1, len(df) + 1))

# ===== Step 8: Save final dataset =====


# ===== Step 9: Summary =====
print("✅ Cleaning complete!")
print("Final dataset size:", len(df))

import re

# Function to detect corrupted usernames
def is_corrupted_username(text):
    if not isinstance(text, str):
        return True
    
    total = len(text)
    if total == 0:
        return True
    
    garbage = len(re.findall(r'[ý�ï¿½]', text))
    
    return (garbage / total) > 0.3

# Replace corrupted usernames with unique identifiers
df['username'] = df.apply(
    lambda row: f"unknown_{row.name + 1}" if is_corrupted_username(row['username']) else row['username'],
    axis=1
)

df.to_csv("final_cleaned_dataset.csv", encoding='utf-8-sig', index=False)
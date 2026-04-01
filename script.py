import pandas as pd
import re
from ftfy import fix_text

# Step 1: Read safely
df = pd.read_csv("farmer-protest-data.csv", encoding='latin1')

# Step 2: Text cleaning function
def clean_text(text):
    if not isinstance(text, str):
        return text
    
    # Fix encoding issues
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

# Step 3: Apply cleaning
for col in ['username', 'tweet_text']:
    df[col] = df[col].apply(clean_text)

# Step 4: Save clean CSV
df.to_csv("cleaned_output.csv", encoding='utf-8-sig', index=False)
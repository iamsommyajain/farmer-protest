import re

def fix_encoding(text):
    try:
        return text.encode('latin1').decode('utf-8')
    except:
        return text

def remove_non_ascii(text):
    return re.sub(r'[^\x00-\x7F]+', ' ', text)

def clean_whitespace(text):
    return re.sub(r'\s+', ' ', text).strip()

def remove_urls(text):
    return re.sub(r'http\S+|www\S+', '', text)

def remove_mentions(text):
    return re.sub(r'@\w+', '', text)

def process_hashtags(text):
    return text.replace('#', '')
"""
fix_encoding.py
---------------
Fixes encoding corruption in the farmer protest tweet CSV.

TWO TYPES OF CORRUPTION ARE HANDLED:

  TYPE 1 — RECOVERABLE (Latin-1 mojibake):
    Symptoms: à¨à¨¿à¨¸à¨¾à¨¨  /  Ã½Ã½  /  à©
    Cause: UTF-8 file was opened/saved as Latin-1 by Excel or similar.
    Fix: re-encode as Latin-1 bytes, decode as UTF-8. Fully recoverable.

  TYPE 2 — IRRECOVERABLE (ý / ï¿½ corruption):
    Symptoms: ýýýýýýýý  /  ï¿½ï¿½ï¿½
    Cause: Original bytes were destroyed before this file was created —
           either the tweet scraper, a database export, or an earlier tool
           wrote 0xFD bytes (ý) or U+FFFD replacement chars in place of
           the real characters. No reverse-encoding can recover them.
    Action: Rows with >50% corrupt chars in tweet_text are flagged and
            written to a separate "corrupted" CSV. Rows with only minor
            corruption (e.g. a mixed English+Punjabi tweet) are kept but
            annotated with a 'corruption_flag' column.

Usage:
    pip install pandas chardet
    python fix_encoding.py input.csv output_fixed.csv output_corrupted.csv

    # Uses defaults if no args given:
    python fix_encoding.py
"""

import sys
import re
import pandas as pd

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

# ── Config ────────────────────────────────────────────────────────────────────
INPUT_FILE       = sys.argv[1] if len(sys.argv) > 1 else "farmer-protest-data.csv"
OUTPUT_FIXED     = sys.argv[2] if len(sys.argv) > 2 else "farmer_tweets_fixed.csv"
OUTPUT_CORRUPTED = sys.argv[3] if len(sys.argv) > 3 else "farmer_tweets_corrupted.csv"

# Fraction of non-ASCII chars that must be ý/ï¿½ to flag a row as corrupted
CORRUPTION_THRESHOLD = 0.5
# ──────────────────────────────────────────────────────────────────────────────


def detect_encoding(filepath: str) -> str:
    if not HAS_CHARDET:
        return "latin-1"
    with open(filepath, "rb") as f:
        raw = f.read(50_000)
    result = chardet.detect(raw)
    detected = result.get("encoding") or "latin-1"
    print(f"Detected encoding : {detected}  (confidence {result.get('confidence', 0):.0%})")
    return detected


# ── TYPE 1: Latin-1 mojibake fix ──────────────────────────────────────────────

def is_type1_mojibake(text: str) -> bool:
    """Detects UTF-8-read-as-Latin-1 corruption (recoverable)."""
    if not isinstance(text, str):
        return False
    # These are the Latin-1 representations of common UTF-8 lead bytes:
    # 0xE0 = à (start of 3-byte seq for Devanagari/Gurmukhi)
    # 0xC3 = Ã (start of 2-byte seq for many accented Latin chars)
    markers = (
        "\u00e0\u00a9",  # à© — Gurmukhi vowel signs
        "\u00e0\u00a8",  # à¨ — Gurmukhi consonants
        "\u00e0\u00a4",  # à¤ — Devanagari consonants
        "\u00e0\u00a5",  # à¥ — Devanagari vowel signs
        "\u00c3\u00a4",  # Ã¤ — Latin extended (ä)
        "\u00c3\u00b6",  # Ã¶
        "\u00c3\u00bc",  # Ã¼
    )
    return any(m in text for m in markers)


def fix_type1(text: str) -> str:
    """Reverses Latin-1 mojibake by re-encoding as Latin-1 then decoding as UTF-8."""
    if not isinstance(text, str):
        return text
    try:
        return text.encode("latin-1").decode("utf-8", errors="replace")
    except UnicodeEncodeError:
        return text  # Already contains valid high-Unicode chars, leave alone


# ── TYPE 2: Corruption detection ──────────────────────────────────────────────

# Matches the two irrecoverable patterns
_BAD_PATTERN = re.compile(r"[\u00fd\ufffd\u00ef\u00bf\u00bd]+")

def corruption_ratio(text: str) -> float:
    """
    Returns fraction of non-ASCII characters that are corrupt (ý or ï¿½).
    A pure-English tweet with no non-ASCII chars returns 0.0.
    """
    if not isinstance(text, str) or not text:
        return 0.0
    non_ascii = [c for c in text if ord(c) > 127]
    if not non_ascii:
        return 0.0
    bad = sum(1 for c in non_ascii if ord(c) in (0x00FD, 0xFFFD, 0x00EF, 0x00BF, 0x00BD))
    return bad / len(non_ascii)


def clean_residual_corruption(text: str) -> str:
    """
    For rows that are mostly clean but have a few stray ý/ï¿½ chars,
    strip those chars rather than keeping garbage in the output.
    """
    if not isinstance(text, str):
        return text
    # Remove the 3-char sequence ï¿½ (Latin-1 rendering of U+FFFD)
    text = text.replace("\u00ef\u00bf\u00bd", "")
    # Remove lone ý chars that are surrounded by spaces or punctuation
    # (keep ý if it appears in legitimate contexts like "ý" in a proper name)
    text = re.sub(r"(?<!\w)\u00fd+(?!\w)", "", text)
    return text.strip()


# ── Main ──────────────────────────────────────────────────────────────────────
print(f"\nReading  : {INPUT_FILE}")
detect_encoding(INPUT_FILE)

df = pd.read_csv(INPUT_FILE, encoding="latin-1", dtype=str)
print(f"Rows     : {len(df)}")
print(f"Columns  : {list(df.columns)}\n")

# Step 1 — Fix Type 1 (recoverable mojibake) across all string columns
type1_fixed = 0
for col in df.columns:
    if df[col].dtype != object:
        continue
    mask = df[col].apply(is_type1_mojibake)
    if mask.any():
        df.loc[mask, col] = df.loc[mask, col].apply(fix_type1)
        type1_fixed += mask.sum()
        print(f"  [TYPE 1 fixed] {mask.sum():>5} cells in '{col}'")

# Step 2 — Assess Type 2 corruption on tweet_text
text_col = "tweet_text" if "tweet_text" in df.columns else df.columns[-2]
df["_corrupt_ratio"] = df[text_col].apply(corruption_ratio)
df["corruption_flag"] = df["_corrupt_ratio"].apply(
    lambda r: "corrupted" if r >= CORRUPTION_THRESHOLD else ("partial" if r > 0 else "ok")
)

n_corrupted = (df["corruption_flag"] == "corrupted").sum()
n_partial   = (df["corruption_flag"] == "partial").sum()
n_ok        = (df["corruption_flag"] == "ok").sum()

print(f"\n  [TYPE 2 audit] tweet_text corruption:")
print(f"    Fully corrupted (>{CORRUPTION_THRESHOLD:.0%} bad chars) : {n_corrupted}")
print(f"    Partially corrupt                     : {n_partial}")
print(f"    Clean                                 : {n_ok}")

# Step 3 — Clean residual ý/ï¿½ from partial rows
partial_mask = df["corruption_flag"] == "partial"
if partial_mask.any():
    df.loc[partial_mask, text_col] = df.loc[partial_mask, text_col].apply(clean_residual_corruption)
    print(f"    Stripped residual garbage from {partial_mask.sum()} partial rows")

# Step 4 — Split into clean and corrupted outputs
df_clean     = df[df["corruption_flag"] != "corrupted"].drop(columns=["_corrupt_ratio"])
df_corrupted = df[df["corruption_flag"] == "corrupted"].drop(columns=["_corrupt_ratio"])

# Step 5 — Save
df_clean.to_csv(OUTPUT_FIXED, index=False, encoding="utf-8-sig")
df_corrupted.to_csv(OUTPUT_CORRUPTED, index=False, encoding="utf-8-sig")

print(f"\nSaved clean rows    : {OUTPUT_FIXED}  ({len(df_clean)} rows)")
print(f"Saved corrupted rows: {OUTPUT_CORRUPTED}  ({len(df_corrupted)} rows)")
print(f"Total cells type-1 repaired: {type1_fixed}")

# Preview
print("\n" + "─" * 70)
print("Sample fixed rows")
print("─" * 70)
for _, row in df_clean.head(6).iterrows():
    handle = row.get("handle", "")
    tweet  = str(row.get(text_col, ""))
    flag   = row.get("corruption_flag", "")
    print(f"[{handle}] ({flag})")
    print(f"  {tweet[:180]}")
    print()
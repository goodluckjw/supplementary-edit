import streamlit as st
import pandas as pd
import re
from collections import defaultdict
import io

def extract_article(text):
    match = re.search(r"(제\d+조(?:의\d+)?)", text)
    return match.group(1) if match else ""

def extract_clause_number(text):
    match = re.search(r"([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])", text)
    circled_number_map = {
        "①": "1", "②": "2", "③": "3", "④": "4", "⑤": "5",
        "⑥": "6", "⑦": "7", "⑧": "8", "⑨": "9", "⑩": "10",
        "⑪": "11", "⑫": "12", "⑬": "13", "⑭": "14", "⑮": "15",
        "⑯": "16", "⑰": "17", "⑱": "18", "⑲": "19", "⑳": "20",
    }
    return circled_number_map.get(match.group(1), None) if match else None

def has_final_consonant(korean_word):
    last_char = korean_word[-1]
    return (ord(last_char) - 44032) % 28 != 0

def format_clauses(clauses):
    if len(clauses) == 1:
        return f"제{clauses[0]}항"
    elif len(clauses) == 2:
        return f"제{clauses[0]}항 및 제{clauses[1]}항"
    else:
        formatted = ", ".join([f"제{clause}항" for clause in clauses[:-1]])
        return f"{formatted} 및 제{clauses[-1]}항"

def number_to_circled(num):
    base_code = 0x24EA
    if 1 <= num <= 50:
        return chr(0x2460 + num - 1)
    elif 51 <= num <= 100:
        return chr(0x3251 + num - 51)
    else:
        return f"({num})"

def process_law_excel(uploaded_files, original_term, replacement_term):
    processed_rows = []
    for uploaded_file in uploaded_files:
        df = pd.read_excel(uploaded_file, header=5)
        current_law_name = None
        for _, row in df.iterrows():
            if pd.notna(row['법령명']):
                current_law_name = row['법령명']
            if isinstance(row['No.'], str) and row['No.'].startswith("제"):
                processed_rows.append({
                    '법령명': current_law_name,
                    '조문': row['No.']
                })

    law_articles = pd.DataFrame(processed_rows)
    filtered = law_articles[law_articles['조문'].str.contains(original_term, na=False)]

    grouped = defaultdict(lambda: defaultdict(list))
    for _, row in filtered.iterrows():
        article = extract_article(row['조문'])
        clause_number = extract_clause_number(row['조문'])
        if article:
            grouped[row['법령명']][article].append((clause_number, row['조문']))

    output_lines = []

    for idx, law_name in enumerate(sorted(grouped.keys()), 1):
        circled = number_to_circled(idx)
        output_lines.append(f"{circled} {law_name} 일부를 다음과 같이 개정한다.")
        for article in sorted(grouped[law_name].keys()):
            clauses = []
            match_samples = set()
            for clause_num, text in grouped[law_name][article]:
                if clause_num:
                    clauses.append(clause_num)
                matches = re.findall(rf"{original_term}\S*", text)
                match_samples.update(matches)

            if not match_samples:
                continue

            clauses = sorted(set(clauses), key=lambda x: int(x))
            clause_part = format_clauses(clauses) if clauses else article

            for match in sorted(match_samples):
                modified = match.replace(original_term, replacement_term, 1)
                particle = "을" if has_final_consonant(match) else "를"
                count = sum(text.count(match) for _, text in grouped[law_name][article])
                each = "각각 " if count > 1 else ""
                sentence = f'{law_name} {article} {clause_part} 중 "{match}"{particle} {each}"{modified}"으로 한다.'
                output_lines.append(sentence)

        output_lines.append("")

    return "\n".join(output_lines)

st.title("법률 조문 단어 치환기")

st.markdown("""
**사용 방법:**
1. 국회 입법정보시스템에서 다운로드한 엑셀 파일들을 업로드하세요.  
2. 바꾸고 싶은 단어와 새로 바꿀 단어를 입력하세요.  
3. 텍스트 파일로 저장해서 내려받을 수 있어요.
""")

uploaded_files = st.file_uploader("엑셀 파일 업로드 (여러 개 가능)", type=["xlsx"], accept_multiple_files=True)
original_term = st.text_input("찾을 단어 (예: 지방법원)")
replacement_term = st.text_input("바꿀 단어 (예: 지역법원)")

if uploaded_files and original_term and replacement_term:
    result_text = process_law_excel(uploaded_files, original_term, replacement_term)

    st.download_button(
        label="📥 결과 텍스트 파일 다운로드",
        data=result_text,
        file_name="법률_개정안_결과.txt",
        mime="text/plain"
    )

    st.text_area("미리보기", result_text, height=400)
else:
    st.info("엑셀 파일과 바꿀 단어들을 입력해 주세요.")

import streamlit as st
import pandas as pd
import re
from collections import defaultdict
import io
import requests
from bs4 import BeautifulSoup
import time

def extract_article(text):
    match = re.search(r"(제\d+조(?:의\d+)?)", text)
    return match.group(1) if match else ""

def extract_title(text):
    match = re.search(r"제\d+조(?:의\d+)?\(([^)]+)\)", text)
    return match.group(1) if match else None

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
    if 1 <= num <= 50:
        return chr(0x2460 + num - 1)
    elif 51 <= num <= 100:
        return chr(0x3251 + num - 51)
    else:
        return f"({num})"

def fetch_law_names_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    law_names = []
    for td in soup.find_all('td', class_='tl'):
        law_name = td.get_text(strip=True)
        if law_name:
            law_names.append(law_name)
    return law_names

def fetch_law_text_from_law_go_kr(law_name):
    search_url = f"https://www.law.go.kr/LSW/eng/engLsSc.do?menuId=2&query={law_name}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    law_text = ""
    for div in soup.find_all("div", class_="law_text"):
        law_text += div.get_text(separator="\n", strip=True)
    return law_text if law_text else law_name + " 전문을 찾을 수 없습니다."

def process_web_laws(url, original_term, replacement_term):
    law_names = fetch_law_names_from_url(url)
    output_lines = []

    for idx, law_name in enumerate(sorted(law_names), 1):
        time.sleep(0.5)  # avoid hammering site
        text = fetch_law_text_from_law_go_kr(law_name)
        if original_term not in text:
            continue
        circled = number_to_circled(idx)
        article = extract_article(text) or "제1조"
        clause_number = extract_clause_number(text)
        title = extract_title(text)
        clauses = [clause_number] if clause_number else []

        clause_text = ""
        if title and clauses:
            clause_text = f"{article}의 제목 및 같은 조 {format_clauses(clauses)}"
        elif title:
            clause_text = f"{article}의 제목"
        elif clauses:
            clause_text = f"{article} {format_clauses(clauses)}"
        else:
            clause_text = f"{article}"

        matches = re.findall(rf"[가-힣]*{original_term}(?=\(|\s|\.|,|$)?", text)
        for match in sorted(set(matches)):
            modified = match.replace(original_term, replacement_term, 1)
            particle = "을" if has_final_consonant(match) else "를"
            count = len(re.findall(re.escape(match), text))
            each = "각각 " if count > 1 else ""
            sentence = f'{law_name} {clause_text} 중 "{match}"{particle} {each}"{modified}"으로 한다.'
            output_lines.append(f"{circled} {law_name} 일부를 다음과 같이 개정한다.")
            output_lines.append(sentence)
            output_lines.append("")

    return "\n".join(output_lines)

st.title("타법개정 도우미")

st.markdown("""
**용어 개정 후 부칙의 '다른 법률의 개정'을 간편하게 하기 위한 앱입니다.**

**개선할 사항이나 오류가 있으면 사법법제과 김재우(4778)로 연락주세요.**

**사용 방법:**
1. 국회 입법정보센터의 법률 검색 URL을 입력하세요.  
2. 바꾸고 싶은 단어와 새로 바꿀 단어를 입력하세요.  
3. 텍스트 파일로 저장해서 내려받을 수 있어요.
""")

url = st.text_input("법률 목록이 있는 URL 입력")
original_term = st.text_input("찾을 단어 (예: 지방법원)")
replacement_term = st.text_input("바꿀 단어 (예: 지역법원)")

if url and original_term and replacement_term:
    result_text = process_web_laws(url, original_term, replacement_term)

    st.download_button(
        label="📥 결과 텍스트 파일 다운로드",
        data=result_text,
        file_name="법률_개정안_결과.txt",
        mime="text/plain"
    )

    st.text_area("미리보기", result_text, height=400)
else:
    st.info("법률 URL과 바꿀 단어들을 입력해 주세요.")

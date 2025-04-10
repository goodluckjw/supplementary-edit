
import streamlit as st
import pandas as pd
import re
from collections import defaultdict
import io
import requests
from bs4 import BeautifulSoup

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

def dummy_law_text(law_name):
    return f"{law_name} 제1조(목적) ① 이 법은 {law_name}에 관한 사항을 정한다. ② 지방법원은 이에 따른다."

def process_web_laws(url, original_term, replacement_term):
    law_names = fetch_law_names_from_url(url)
    output_lines = []

    for idx, law_name in enumerate(sorted(law_names), 1):
        text = dummy_law_text(law_name)
        if original_term not in text:
            continue
        circled = number_to_circled(idx)
        article = extract_article(text) or "제1조"
        clause_number = extract_clause_number(text)
        title = extract_title(text)
        clauses = [clause_number] if clause_number else []

        if original_term in text:
            clause_text = ""
            if title and clauses:
                clause_text = f"{article}의 제목 및 같은 조 {format_clauses(clauses)}"
            elif title:
                clause_text = f"{article}의 제목"
            elif clauses:
                clause_text = f"{article} {format_clauses(clauses)}"
            else:
                clause_text = f"{article}"

            modified = original_term.replace(original_term, replacement_term)
            particle = "을" if has_final_consonant(original_term) else "를"
            sentence = f'{law_name} {clause_text} 중 "{original_term}"{particle} "{modified}"으로 한다.'
            output_lines.append(f"{circled} {law_name} 일부를 다음과 같이 개정한다.")
            output_lines.append(sentence)
            output_lines.append("")

    return "\n".join(output_lines)

st.set_page_config(page_title="타법개정 도우미", layout="centered")
st.title("📘 타법개정 도우미")

st.markdown("""
**용어 개정 후 부칙의 '다른 법률의 개정'을 간편하게 하기 위한 앱입니다.**

📞 *개선할 사항이나 오류가 있으면 사법법제과 김재우(4778)로 연락주세요.*

---

### 🧾 사용 방법:
1. **법률 목록이 있는 웹페이지 주소(URL)**를 복사하여 붙여넣습니다.  
2. **찾을 단어**와 **바꿀 단어**를 입력합니다.  
3. 결과를 확인하고, **텍스트 파일로 다운로드**합니다.
""")

url = st.text_input("🔗 법률 목록 URL 입력", placeholder="예: https://likms.assembly.go.kr/law/lawsSrchInqy...")
original_term = st.text_input("🔍 찾을 단어 (예: 지방법원)", value="지방법원")
replacement_term = st.text_input("✏️ 바꿀 단어 (예: 지역법원)", value="지역법원")

if url and original_term and replacement_term:
    result_text = process_web_laws(url, original_term, replacement_term)

    st.download_button(
        label="📥 결과 텍스트 파일 다운로드",
        data=result_text,
        file_name="법률_개정안_결과.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.text_area("📄 결과 미리보기", result_text, height=400)
else:
    st.info("👆 URL과 단어를 모두 입력해주세요. 예시가 기본으로 들어가 있습니다.")

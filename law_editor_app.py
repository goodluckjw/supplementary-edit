import streamlit as st
import pandas as pd
import re
from collections import defaultdict
import io

# (기존 함수들은 생략 – 그대로 유지)

st.title("타법개정 도우미")

st.markdown("""
**용어 개정 후 부칙의 '다른 법률의 개정'을 간편하게 하기 위한 앱입니다.**

**개선할 사항이나 오류가 있으면 사법법제과 김재우(4778)로 연락주세요.**

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

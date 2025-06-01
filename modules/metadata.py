# modules/crossref.py
# 이 파일은 Crossref API 및 PDF 파일 자체에서 메타데이터와 DOI를 추출하는 함수들을 포함합니다.
import requests
from utils import debug_log
from pathlib import Path
import re
import fitz  # PyMuPDF 라이브러리, PDF 파일 처리를 위해 사용 (fitz는 PyMuPDF의 import 이름)

# Crossref API의 기본 URL

CROSSREF_API = "https://api.crossref.org/works/"

def fetch_metadata_from_crossref(doi: str, debug=False) -> dict:
    """
    주어진 DOI를 사용하여 Crossref API에서 논문 메타데이터를 가져옵니다.

    Args:
        doi (str): 조회할 논문의 DOI.
        debug (bool, optional): 디버그 모드 활성화 여부. 기본값은 False.

    Returns:
        dict: Crossref에서 가져온 메타데이터 딕셔너리.
            조회에 실패하거나 오류 발생 시 빈 딕셔너리를 반환합니다.
            딕셔너리 키: "title", "authors", "journal", "volume", "issue", "pages", "pub_date", "keywords", "doi".
    """
    try:
        # Crossref API에 GET 요청을 보냅니다. URL은 기본 API 주소에 DOI를 추가하여 구성합니다.
        res = requests.get(CROSSREF_API + doi)
        if res.status_code != 200:
            if debug:
                debug_log("CROSSREF", f"DOI 조회 실패: {doi} (status {res.status_code})")
            return {}

        # 응답받은 JSON 데이터에서 "message" 부분을 가져옵니다. 이 부분이 실제 메타데이터를 포함합니다.
        item = res.json()["message"]

        if debug:
            debug_log("CROSSREF", f"DOI 메타데이터 조회 성공: {doi}")
        return {
            "title": item.get("title", [""])[0],
            "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in item.get("author", [])],
            "journal": item.get("container-title", [""])[0],
            "volume": item.get("volume"),
            "issue": item.get("issue"),
            "pages": item.get("page"),
            "pub_date": "-".join(str(i) for i in item.get("published-print", {}).get("date-parts", [[None]])[0]),
            "keywords": item.get("subject", []),
            "doi": item.get("DOI"),
        }
    except Exception as e:
        print(f"[ERROR] CROSSREF 예외 발생: {e}")
        return {}

def find_doi_by_title(title: str, debug=False) -> str | None:
    """
    논문 제목을 사용하여 Crossref API에서 DOI를 검색합니다.

    Args:
        title (str): 검색할 논문의 제목.
        debug (bool, optional): 디버그 모드 활성화 여부. 기본값은 False.

    Returns:
        str | None: 검색된 DOI 문자열. 찾지 못하거나 오류 발생 시 None을 반환합니다.
    """
    try:
        # Crossref API의 /works 엔드포인트에 제목으로 검색 요청 (query.title 파라미터 사용)
        res = requests.get("https://api.crossref.org/works", params={"query.title": title, "rows": 1})
        if res.status_code == 200:
            items = res.json().get("message", {}).get("items", [])
            if items and "DOI" in items[0]:
                if debug:
                    debug_log("CROSSREF", f"제목 기반 DOI 조회 성공: {items[0]['DOI']}")
                return items[0]["DOI"]
    except Exception as e:
        print(f"[ERROR] CROSSREF, 제목 기반 DOI 조회 실패: {e}")
    return None

def extract_doi_from_pdf(pdf_path: Path) -> str | None:
    """
    주어진 PDF 파일의 텍스트 내용에서 DOI를 추출합니다.
    PDF의 처음 몇 페이지만 스캔하여 효율성을 높입니다.

    Args:
        pdf_path (Path): DOI를 추출할 PDF 파일의 경로.

    Returns:
        str | None: 추출된 DOI 문자열. 찾지 못하면 None을 반환합니다.
    """
    doc = None
    try:
        # PyMuPDF를 사용하여 PDF 파일을 엽니다.
        doc = fitz.open(pdf_path)
        text = ""
        # PDF의 첫 2페이지 또는 전체 페이지 수 중 적은 수만큼 반복하여 텍스트를 추출합니다.
        # DOI는 보통 논문 초반부에 위치하므로 전체를 스캔할 필요는 없습니다.
        for page_num in range(min(2, doc.page_count)): # 처음 2페이지만 확인
            page = doc.load_page(page_num)
            text += page.get_text()

        # 정규 표현식을 사용하여 텍스트에서 DOI 패턴을 검색합니다.
        # DOI 패턴: "10."으로 시작하고, 그 뒤에 4자리 이상의 숫자가 오고, "/" 뒤에 공백, ", <, > 가 아닌 문자들이 오는 형식
        # re.IGNORECASE는 대소문자를 구분하지 않도록 합니다.
        match = re.search(r'10\.\d{4,9}/[^\s"<>]+', text, re.IGNORECASE)
        if match:
            # DOI가 검색되면, 해당 문자열을 가져와 앞뒤 공백 및 끝에 붙은 불필요한 문자(.;,)를 제거하고 반환합니다.
            return match.group(0).strip().rstrip('.;,')
    except Exception as e:
        print(f"[ERROR] PDF에서 DOI 추출 중 오류 발생 ({pdf_path}): {e}")
    finally:
        if doc:
            doc.close()
    return None
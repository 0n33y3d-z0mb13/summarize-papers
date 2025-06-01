# modules/grobid.py
# GROBID API를 이용하여 PDF 논문에서 메타데이터와 초록을 추출하는 모듈입니다.
# GROBID는 기계 학습 기반의 오픈소스 소프트웨어로, 학술 문서의 구조를 분석하고 서지 정보를 추출합니다.
import requests
import xml.etree.ElementTree as ET  # XML 데이터를 파싱하고 다루기 위한 라이브러리
from pathlib import Path
from utils import debug_log

# GROBID API 엔드포인트 주소
# 이 주소로 PDF 파일을 보내면, GROBID가 분석 후 XML 형태로 결과를 반환합니다.
GROBID_API = "https://kermitt2-grobid.hf.space/api/processFulltextDocument"

def extract_metadata_and_abstract(pdf_path: Path, debug=False) -> dict:
    """
    GROBID 서비스를 이용해 PDF 파일에서 메타데이터와 초록(abstract)을 추출합니다.
    이 함수는 PDF 파일을 GROBID API 엔드포인트로 전송하고,
    반환된 XML을 파싱하여 논문의 제목, 저자, 저널, 출판 정보, DOI, 키워드, 초록 등
    다양한 서지 정보를 추출합니다.

    Args:
        pdf_path (Path): 처리할 PDF 파일의 경로.
        debug (bool, optional): True로 설정하면 추출된 메타데이터에 대한 디버그 정보를 출력합니다. 기본값은 False.

    Returns:
        dict: 추출된 메타데이터와 초록이 담긴 딕셔너리.
              각 키는 다음과 같습니다:
              - "title" (str): 논문 제목
              - "authors" (list[str]): 저자 이름 리스트
              - "journal" (str): 저널명
              - "volume" (str): 저널 볼륨
              - "issue" (str): 저널 이슈
              - "pages" (str): 페이지 정보
              - "doi" (str): DOI (디지털 객체 식별자)
              - "pub_date" (str): 출판일
              - "keywords" (list[str]): 키워드 리스트
              - "abstract" (str): 논문 초록
              GROBID 요청 실패 또는 XML 파싱 실패 시 빈 딕셔너리를 반환합니다.
    """
    files = {"input": (pdf_path.name, pdf_path.read_bytes(), "application/pdf")}
    response = requests.post(GROBID_API, files=files)

    if response.status_code != 200:
        print("[ERROR] GROBID 요청 실패")
        return {}

    try:
        xml_root = ET.fromstring(response.content)
    except ET.ParseError:
        print("[ERROR] XML 파싱 실패")
        return {}

    ns = {"tei": "http://www.tei-c.org/ns/1.0"}

    # 논문 제목 추출
    title = xml_root.findtext(".//tei:fileDesc/tei:titleStmt/tei:title", namespaces=ns)

    # 저자 정보 추출(여러 명일 수 있음)
    authors = []
    for author in xml_root.findall(".//tei:fileDesc/tei:titleStmt/tei:author/tei:persName", namespaces=ns):
        surname = author.findtext("tei:surname", namespaces=ns)
        forename = author.findtext("tei:forename", namespaces=ns)
        if surname and forename:
            full_name = f"{forename} {surname}"
        else:
            full_name = surname or forename or "Unknown"
        authors.append(full_name)

    # 저널명, 볼륨, 이슈, 페이지, DOI, 출판일, 키워드, 초록 추출
    journal = xml_root.findtext(".//tei:monogr/tei:title", namespaces=ns)
    volume = xml_root.findtext(".//tei:monogr/tei:biblScope[@unit='volume']", namespaces=ns)
    issue = xml_root.findtext(".//tei:monogr/tei:biblScope[@unit='issue']", namespaces=ns)
    pages = xml_root.findtext(".//tei:monogr/tei:biblScope[@unit='page']", namespaces=ns)
    doi = xml_root.findtext(".//tei:fileDesc//tei:idno[@type='DOI']", namespaces=ns)
    pub_date = xml_root.findtext(".//tei:monogr/tei:imprint/tei:date", namespaces=ns)

    # 키워드 추출(여러 개일 수 있음음)
    keywords = [kw.text.strip() for kw in xml_root.findall(".//tei:keywords/tei:term", namespaces=ns) if kw.text]

    # 초록 추출(여러 개의 문단으로 구성될 수 있음음)
    abstract_elem = xml_root.find(".//tei:abstract", namespaces=ns)
    abstract = ""
    if abstract_elem is not None:
        # 각 문단을 찾아서 텍스트를 추출하고, 줄바꿈으로 연결
        paragraphs = abstract_elem.findall(".//tei:p", namespaces=ns)
        abstract = "\n".join(p.text.strip() for p in paragraphs if p.text)

    # 디버그 모드일 경우, 추출된 메타데이터 출력
    if debug:
        debug_log("GROBID ", f"제목: {title}")
        debug_log("GROBID ", f"저자 수: {len(authors)}")
        debug_log("GROBID ", f"저널명: {journal}")
        debug_log("GROBID ", f"출판년도: {pub_date}")
        debug_log("GROBID ", f"DOI: {doi}")
        debug_log("GROBID ", f"Abstract 길이: {len(abstract)}자")

    # 추출된 메타데이터를 딕셔너리 형태로 반환
    return {
        "title": title,
        "authors": authors,
        "journal": journal,
        "volume": volume,
        "issue": issue,
        "pages": pages,
        "doi": doi,
        "pub_date": pub_date,
        "keywords": keywords,
        "abstract": abstract,
    }
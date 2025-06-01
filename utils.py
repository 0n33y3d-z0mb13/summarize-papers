# utils.py
# 이 파일은 프로젝트 전반에서 사용되는 유틸리티 함수들을 포함합니다.
# 결과 출력 포맷팅, 메타데이터 병합, 디버그 로깅 등의 기능을 제공합니다.
def print_readable_output(result: dict):
    """
    파이프라인 최종 결과를 사람이 읽기 쉬운 형태로 콘솔에 출력합니다.

    Args:
        result (dict): 파이프라인에서 처리된 최종 결과 데이터 딕셔너리.
                       이 딕셔너리에는 'title', 'authors', 'journal', 'doi',
                       'abstract_ko', 'summary' 등의 키가 포함될 수 있습니다.
    """
    print("\n○ 논문 요약 결과")
    print("─" * 60)
    print(f"제목        : {result.get('title')}")
    print(f"저자        : {', '.join(result.get('authors', []))}")
    print(f"학술지      : {result.get('journal')}")

    vol = result.get("volume")
    issue = result.get("issue")
    pages = result.get("pages")
    pub_date = result.get("pub_date")
    pub_info_parts = [
        pub_date if pub_date else "",
        f"Vol. {vol}" if vol else "",
        f"No. {issue}" if issue else "",
        f"pp. {pages}" if pages else ""
    ]
    print(f"출판정보    : {' / '.join(p for p in pub_info_parts if p)}")

    doi = result.get("doi")
    if doi:
        if '/' in doi:
            print(f"DOI         : https://doi.org/{doi}")
        else:
            print(f"DOI         : {doi}")

    if result.get("keywords"):
        print(f"키워드     : {', '.join(result['keywords'])}")

    print("\n○ 초록 (번역)")
    print("─" * 60)
    print(result.get("abstract_ko", "").strip())

    print("\n○ 요약 (한 줄)")
    print("─" * 60)
    print(result.get("summary", "").strip())

def merge_metadata(crossref_data, grobid_data):
    """
    Crossref API에서 가져온 메타데이터와 GROBID에서 추출한 메타데이터를 병합합니다.
    일반적으로 Crossref 데이터가 더 정확하거나 완전할 가능성이 높아 우선적으로 사용됩니다.

    Args:
        crossref_data (dict): Crossref API로부터 받은 메타데이터 딕셔너리.
        grobid_data (dict): GROBID로부터 추출된 메타데이터 딕셔너리.

    Returns:
        dict: 두 출처의 정보가 병합된 메타데이터 딕셔너리.
              Crossref에 정보가 있으면 해당 정보를, 없으면 GROBID 정보를 사용합니다.
              단, 초록('abstract_en')은 GROBID가 추출한 원본을 유지하는 것을 기본으로 합니다.
    """
    return {
        "title": crossref_data.get("title") or grobid_data.get("title"),
        "authors": crossref_data.get("authors") or grobid_data.get("authors"),
        "journal": crossref_data.get("journal") or grobid_data.get("journal"),
        "volume": crossref_data.get("volume") or grobid_data.get("volume"),
        "issue": crossref_data.get("issue") or grobid_data.get("issue"),
        "pages": crossref_data.get("pages") or grobid_data.get("pages"),
        "pub_date": crossref_data.get("pub_date") or grobid_data.get("pub_date"),
        "keywords": crossref_data.get("keywords") or grobid_data.get("keywords"),
        "abstract_en": grobid_data.get("abstract"),  # abstract는 GROBID 기준 유지
    }

def debug_log(source: str, message: str) -> None:
    """
    디버깅 목적으로 콘솔에 로그 메시지를 출력합니다.
    메시지 앞에 출처(모듈 또는 기능 이름)를 표시하여 구분을 용이하게 합니다.

    Args:
        source (str): 로그 메시지의 출처 (예: "GROBID", "TRANSLATE").
        message (str): 기록할 디버그 메시지 내용.
    """
    print(f"[DEBUG][{source}] {message}")

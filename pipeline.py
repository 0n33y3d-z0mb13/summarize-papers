# pipeline.py
# 이 파일은 논문 PDF를 처리하는 전체 파이프라인 로직을 담고 있습니다.
# 메타데이터 추출, DOI 보완, 번역, 요약 등의 단계를 순차적으로 실행합니다.
import json
import re
from modules.grobid import extract_metadata_and_abstract
from modules.translate import translate_en2ko
from modules.summarize import summarize_ko
from modules.metadata import fetch_metadata_from_crossref, find_doi_by_title, extract_doi_from_pdf
from utils import merge_metadata, debug_log, print_readable_output

def run_pipeline(pdf_path, debug=False):
    """
    논문 PDF 처리 파이프라인을 실행합니다.

    Args:
        pdf_path (Path): 처리할 PDF 파일의 경로.
        debug (bool, optional): 디버그 모드 활성화 여부. 기본값은 False.
    """
    # ─── 1. GROBID를 사용하여 PDF에서 초기 메타데이터 및 초록 추출 ───────────────
    metadata = extract_metadata_and_abstract(pdf_path, debug=debug)
    if not metadata or not metadata.get("abstract"):
        print("[ERROR] abstract 추출 실패")
        return

    doi = metadata.get("doi")
    if debug:
        debug_log("GROBID", f"DOI 추출: {doi}")

    # ─── 2. DOI 유효성 검사 및 보완 로직 (Fallback) ──────────────────────────
    # GROBID가 DOI를 추출하지 못했거나 (not doi),
    # 또는 DOI가 불완전한 경우 (예: "10.1234"와 같이 prefix만 있는 경우) DOI 보완을 시도합니다.
    # re.fullmatch(r'10\\.\\d{4,9}', doi.strip())는 DOI가 '10.숫자들' 형식인지 확인합니다.
    # (참고: DOI는 보통 '10.숫자들/나머지' 형식이므로, '/' 이후 부분이 없으면 불완전하다고 판단)
    if not doi or re.fullmatch(r'10\\.\\d{4,9}', doi.strip()):
        reason = "DOI 없음" if not doi else "Prefix-only DOI (불완전)"
        if debug:
            debug_log("DOI     ", f"Crossref fallback 필요 → 사유: {reason}")

        # 2-1. 1차 Fallback: PDF 텍스트에서 직접 DOI 추출 시도
        if debug:
            debug_log("PDF     ", "PDF에서 DOI 추출 시도 중...")
        extracted_doi = extract_doi_from_pdf(pdf_path)
        if extracted_doi:
            doi = extracted_doi
            metadata["doi"] = doi
            if debug:
                debug_log("PDF     ", f"추출된 DOI: {doi}")
        else:
            # 2-2. 2차 Fallback: PDF에서 DOI 추출 실패 시, 논문 제목을 기반으로 Crossref에서 DOI 검색
            title = metadata.get("title")
            if title:
                if debug:
                    debug_log("CROSSREF", "제목 기반 Crossref DOI 조회 중...")
                found_doi = find_doi_by_title(title)
                if debug:
                    debug_log("CROSSREF", f"제목 기반 조회 결과: {found_doi}")
                if found_doi:
                    doi = found_doi
                    metadata["doi"] = doi
            elif debug:
                debug_log("CROSSREF", "제목 정보가 없어 제목 기반 검색 불가")

    # ─── 3. Crossref에서 메타데이터 조회 및 병합 ─────────────────────────────
    # 최종적으로 확보된 DOI를 사용하여 Crossref API에서 추가적인/정확한 메타데이터를 가져옵니다.
    # 만약 DOI가 여전히 없다면 (doi is None), crossref_data는 빈 딕셔너리가 됩니다.
    crossref_data = fetch_metadata_from_crossref(doi) if doi else {}
    if debug and crossref_data:
        debug_log("CROSSREF", "메타데이터 보완 결과:")
        print(json.dumps(crossref_data, indent=2, ensure_ascii=False))

    # GROBID가 추출한 초기 메타데이터와 Crossref에서 조회한 메타데이터를 병합합니다.
    if debug:
        debug_log("MERGE   ", "Crossref 데이터를 우선 적용하여 병합")
    merged = merge_metadata(crossref_data, metadata)

    # ─── 4. 초록 번역 (영어 -> 한국어) ───────────────────────────────────────
    abstract_ko = translate_en2ko(merged.get("abstract_en", merged.get("abstract", "")))

    # ─── 5. 한국어 초록 요약 ─────────────────────────────────────────────────
    summary = summarize_ko(abstract_ko)

    # ─── 6. 최종 결과 데이터 구성 ─────────────────────────────────────────────
    result = {
        "title": merged["title"],
        "authors": merged["authors"],
        "journal": merged["journal"],
        "volume": merged["volume"],
        "issue": merged["issue"],
        "pages": merged["pages"],
        "doi": doi,
        "pub_date": merged["pub_date"],
        "keywords": merged["keywords"],
        "abstract_en": merged["abstract_en"],
        "abstract_ko": abstract_ko,
        "summary": summary,
    }

    # ─── 7. 결과 출력 ───────────────────────────────────────────────────────
    if debug:
        debug_log("RESULT  ", "최종 결과 JSON:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_readable_output(result)

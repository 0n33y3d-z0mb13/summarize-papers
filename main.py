# main.py
# summarize-papers 프로젝트의 진입점(Entry Point)
# 명령행 인자를 받아 논문 PDF 파일을 처리하는 전체 파이프라인 실행

import argparse
from pathlib import Path
from pipeline import run_pipeline

if __name__ == "__main__":
    # 명령행 인자 파서 설정
    parser = argparse.ArgumentParser()
    # --pdf 옵션: 처리할 논문 PDF 파일의 경로를 입력받음(필수)
    parser.add_argument("--pdf", type=Path, required=True, help="논문 PDF 파일 경로")
    # --debug 옵션: 디버그 출력을 활성화할지 여부를 입력받음(선택)
    parser.add_argument("--debug", action="store_true", help="디버그 출력 여부")
    args = parser.parse_args()

    run_pipeline(args.pdf, args.debug)

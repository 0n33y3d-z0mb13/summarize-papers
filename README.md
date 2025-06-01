# 📄 summarize‑papers

PDF 논문을 입력하면 **메타데이터 → DOI 보완 → 초록 번역(영→한) → 한 줄 요약**까지 한 번에 처리해주는 커맨드라인 툴입니다. GROBID, Crossref, HuggingFace 모델을 조합하여 자동화된 학술 정보 파이프라인을 제공합니다.

---

## ✨ 주요 특징

| 단계               | 사용 기술                                               | 설명                                           |
| ---------------- | --------------------------------------------------- | -------------------------------------------- |
| 1. 메타데이터 & 초록 추출 | [GROBID API](https://github.com/kermitt2/grobid)    | PDF를 XML‑TEI로 변환하여 제목, 저자, 저널, DOI, 초록 등 파싱  |
| 2. DOI 보완        | **정규식** + [Crossref REST](https://api.crossref.org) | PDF 전면부에서 DOI 정규식 검색 → 없으면 제목 기반 Crossref 조회 |
| 3. 메타데이터 병합      | `utils.merge_metadata`                              | GROBID ↔ Crossref 정보를 우선순위로 병합               |
| 4. 초록 번역 (EN→KO) | `facebook/nllb‑200‑distilled‑600M`                  | 200개 언어 다국어 NLLB 모델로 자연스러운 한국어 번역            |
| 5. 한 줄 요약        | `lcw99/t5‑base‑korean‑text‑summary`                 | 한국어 T5로 100자 내외 요약 생성                        |
| 6. 결과 출력         | ANSI 콘솔                                             | 사람이 읽기 쉬운 섹션별 출력, `--debug` 로 상세 로그 확인       |

---

🗂️ 폴더 구조

```
summarize-papers/
├── main.py               # CLI 진입점
├── pipeline.py           # 파이프라인 
├── utils.py              # 공용 유틸·출력 포맷터
├── requirements.txt      # 의존 패키지 (권장)
└── modules/
    ├── grobid.py         # GROBID 호출 & 파싱
    ├── metadata.py       # Crossref / DOI 처리
    ├── translate.py      # NLLB 번역 래퍼
    └── summarize.py      # T5 요약 래퍼
```
---

## ⚙️ 설치

```bash
# 1) Python 3.10+ 권장
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) 패키지 설치
pip install -r requirements.txt

# 3) (선택) GPU 사용 시 PyTorch CUDA 버전 설치
```

> 첫 실행 시 HuggingFace 모델(≈2.5 GB)이 자동 다운로드되며, 이후 캐시에 저장됩니다.

### requirements.txt 
```text
requests>=2.31
transformers>=4.39
torch>=2.2
sentencepiece>=0.1.99
pymupdf>=1.24
tqdm>=4.66
```

| 패키지             | 최소 버전  | 주요 역할                        |
| --------------- | ------ | ---------------------------- |
| `requests`      | 2.31   | GROBID·Crossref REST API 통신  |
| `transformers`  | 4.39   | HuggingFace 번역·요약 모델 로드 및 추론 |
| `torch`         | 2.2    | 딥러닝 모델 실행 (CPU/GPU)          |
| `sentencepiece` | 0.1.99 | 서브워드 토크나이저 (NLLB, T5)        |
| `pymupdf`       | 1.24   | PDF 내부 텍스트·이미지 파싱            |
| `tqdm`          | 4.66   | CLI 진행률 표시                   |



---

## 🚀 사용법

```bash
python main.py --pdf /path/to/paper.pdf [--debug]
```

| 옵션        | 설명            | 기본값     |
| --------- | ------------- | ------- |
| `--pdf`   | 처리할 PDF 파일 경로 | *(필수)*  |
| `--debug` | 단계별 상세 로그 출력  | `False` |

### 예시 출력 (요약)

```
○ 논문 요약 결과
────────────────────────────────────────────────────────────
제목        : Founding Editorial – Forensics and TheScientificWorld
저자        : Walter Rowe
학술지      : The Scientific World JOURNAL
출판정보    : 2001 / Vol. 1 / pp. 605-608
DOI         : https://doi.org/10.1100/tsw.2001.299

○ 초록 (번역)
────────────────────────────────────────────────────────────
인공지능의 일상적이고 중요한 기술에 대한 광범위한 통합으로 인공지능 시스템의 실패 사례가 증가하는 것을 피할 수 없는 것으로 보인다. 그러한 경우, 이러한 실패의 원인에 대한 법적적으로 수용 가능하고 과학적으로 논쟁이 불가능한 연구와 결론을 생산하는 기술적 조사의 필요성이 발생합니다. 사이버 형사학 영역에서 영감을 받아 이 논문은 인공지능 형사학을 인공지능 안전에 대한 새로운 학문으로 설립해야 할 필요성을 소개합니다. 또한, 우리는 이 학문 하위 부 분야에 대한 분류학을 제안하고, 이 새로운 연구 영역에 직면하는 근본적인 도전에 대한 토론을 제공합니다.

○ 요약 (한 줄)
────────────────────────────────────────────────────────────
사이버 형사학 영역에서 영감을 받아 이 논문은 인공지능 형사학을 인공지능 안전에 대한 새로운 학문으로 설립해야 할 필요성을 소개한다.
```

---

## 🏗️ 동작 원리 (파이프라인 세부)

```less
1) PDF 입력
   ↓ GROBID
2) 메타데이터·초록 추출
   ↓
3) DOI 유무 확인
   ├─ 있으면: Crossref 로 세부 정보 보완
   └─ 없으면:
        a. PDF에서 DOI 정규식 추출
        b. 제목으로 Crossref 검색
   ↓
4) 메타데이터 병합 (GROBID + Crossref)
   ↓
5) 초록 번역 (NLLB, EN→KO)
   ↓
6) 번역문 요약 (T5)
   ↓
7) 콘솔 출력

```

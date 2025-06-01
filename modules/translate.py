# modules/translate.py
# 이 파일은 영어 텍스트를 한국어로 번역하는 기능을 제공합니다.
# Hugging Face Transformers 라이브러리의 사전 훈련된 NLLB 모델을 사용합니다.
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM # Hugging Face 파이프라인, 토크나이저, 모델 로드
import torch  # PyTorch 라이브러리, 딥러닝 모델 실행에 사용
from utils import debug_log

# 사용할 사전 훈련된 영어-한국어 번역 모델의 이름 (Hugging Face Model Hub)
MODEL_TRANSLATE = "facebook/nllb-200-distilled-600M"
# 모델을 실행할 장치 설정: CUDA (NVIDIA GPU) 사용 가능하면 GPU, 아니면 CPU 사용
DEVICE          = "cuda" if torch.cuda.is_available() else "cpu"

# 번역 작업을 위한 Hugging Face 파이프라인 초기화
# "translation" 태스크로 모델과 토크나이저를 로드하고, 소스 언어와 대상 언어를 설정합니다.

translator = pipeline(
    "translation",
    model=MODEL_TRANSLATE,  # 사용할 번역 모델
    tokenizer=MODEL_TRANSLATE,  # 모델에 맞는 토크나이저 (모델 이름을 그대로 사용 가능)
    src_lang="eng_Latn",    # 소스 언어: 영어 (라틴 문자)
    tgt_lang="kor_Hang",    # 대상 언어: 한국어 (한글)
    device=0 if DEVICE == "cuda" else -1
)

def translate_en2ko(text: str, debug=False) -> str:
    """
    주어진 영어 텍스트를 한국어로 번역합니다.

    Args:
        text (str): 번역할 영어 텍스트.
        debug (bool, optional): 디버그 모드 활성화 여부. 기본값은 False.

    Returns:
        str: 번역된 한국어 텍스트. 입력 텍스트가 없거나 비어있으면 빈 문자열 또는 원본 텍스트의 공백 제거 버전이 반환될 수 있음.
    """
    if debug:
        debug_log("TRANSLATE", "번역 시작")

    # 입력 텍스트의 앞뒤 공백을 제거하고, translator 파이프라인을 사용하여 번역 실행
    # max_length=1024: 번역 결과의 최대 길이를 1024 토큰으로 제한 (너무 긴 텍스트 처리 시 유용)
    # translator는 리스트 형태로 결과를 반환하며, 각 요소는 딕셔너리.
    # 첫 번째 결과([0])의 "translation_text" 키에 번역된 텍스트가 담겨 있음.
    # 번역된 텍스트의 앞뒤 공백도 제거.
    ko = translator(text.strip(), max_length=1024)[0]["translation_text"].strip()
    
    if debug:
        debug_log("TRANSLATE", "번역 완료 (앞 100자): " + ko[:100] + "...")
    return ko

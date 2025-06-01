# modules/summarize.py
# 이 파일은 한국어 텍스트를 요약하는 기능을 제공합니다.
# Hugging Face Transformers 라이브러리의 사전 훈련된 T5 모델을 사용합니다.
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM  # Hugging Face 모델 및 토크나이저 로드
import torch # PyTorch 라이브러리, 딥러닝 모델 실행에 사용
from utils import debug_log

# 사용할 사전 훈련된 한국어 요약 모델의 이름 (Hugging Face Model Hub)
_model_name = "lcw99/t5-base-korean-text-summary"
# 모델에 맞는 토크나이저 로드: 텍스트를 모델이 이해할 수 있는 숫자 형태로 변환
_tokenizer = AutoTokenizer.from_pretrained(_model_name)
# 사전 훈련된 요약 모델 로드
_model = AutoModelForSeq2SeqLM.from_pretrained(_model_name)
# 모델을 실행할 장치 설정: CUDA (NVIDIA GPU) 사용 가능하면 GPU, 아니면 CPU 사용
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# 로드된 모델을 설정된 장치(GPU 또는 CPU)로 이동
_model.to(_device)

def summarize_ko(text: str, debug=False) -> str:
    """
    주어진 한국어 텍스트를 요약합니다.

    Args:
        text (str): 요약할 한국어 텍스트.
        debug (bool, optional): 디버그 모드 활성화 여부. 기본값은 False.

    Returns:
        str: 요약된 한국어 텍스트. 입력 텍스트가 없으면 빈 문자열을 반환합니다.
    """
    if not text:
        if debug:
            debug_log("SUMMARY ", "입력 텍스트 없음")
        return ""
    
    if debug:
        debug_log("SUMMARY ", f"입력 텍스트 길이: {len(text)}자")

    # 토크나이저를 사용하여 입력 텍스트를 모델 입력 형식으로 변환
    # "summarize: " 접두사는 T5 모델이 요약 작업을 수행하도록 지시하는 프롬프트입니다.
    # return_tensors="pt": PyTorch 텐서 형태로 반환
    # padding=True: 배치 내 다른 시퀀스와 길이를 맞추기 위해 패딩 추가
    # truncation=True: 최대 길이를 초과하는 경우 텍스트 자르기
    # max_length=512: 모델이 처리할 수 있는 최대 토큰 길이 설정
    inputs = _tokenizer("summarize: " + text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    inputs = {k: v.to(_device) for k, v in inputs.items()}

    # 모델을 사용하여 요약 생성
    # **inputs: 준비된 입력 데이터를 모델에 전달
    # max_length=100: 생성될 요약문의 최대 토큰 길이 (너무 길면 잘릴 수 있음)
    # num_beams=4: 빔 서치(beam search) 사용 시 빔의 개수. 더 나은 품질의 요약을 생성하는 데 도움을 줄 수 있음.
    # early_stopping=True: 요약 생성이 충분하다고 판단되면 일찍 중단하여 생성 속도 향상
    summary_ids = _model.generate(
        **inputs,
        max_length=100,
        num_beams=4,
        early_stopping=True
    )

    # 생성된 요약 토큰 ID들을 다시 텍스트 형태로 디코딩
    # skip_special_tokens=True: 토크나이저가 추가한 특수 토큰(예: <pad>, </s>)을 최종 결과에서 제외
    if debug:
        debug_log("SUMMARY ", f"생성된 요약 토큰 수: {summary_ids.shape[-1]}")
    return _tokenizer.decode(summary_ids[0], skip_special_tokens=True)
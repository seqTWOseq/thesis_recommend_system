import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def init_hyde_model():
    """HyDE 방식 검색어 생성을 위한 instruct 모델을 로드합니다."""
    print("Qwen instruct 모델을 로드하는 중...")
    model_id = "Qwen/Qwen2.5-1.5B-Instruct"

    tokenizer = AutoTokenizer.from_pretrained(model_id)

    model_kwargs = {
        "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
    }
    if torch.cuda.is_available():
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
    return model, tokenizer


def generate_hypothetical_abstract(user_input: str, model, tokenizer):
    """사용자 입력을 짧은 영문 기술 초록 형태로 변환합니다."""
    prompt_content = f"""
당신은 HyDE 기반 학술 논문 검색을 돕는 도우미입니다.
사용자는 한국어 또는 영어로 입력할 수 있습니다.

사용자의 프로젝트 설명을 짧은 영문 연구 초록으로 다시 작성하세요.
조건:
1. 영문 문장만 출력합니다.
2. 2~3문장으로 작성합니다.
3. 암시된 구체적인 방법, 모델, 기술 용어가 있으면 포함합니다.
4. 글머리표, 라벨, 추가 설명은 출력하지 않습니다.

예시 입력: 군중이 많은 영상 장면에서 이상행동을 탐지하는 시스템
예시 출력: This paper presents a real-time video surveillance system for abnormal behavior detection in crowded environments. The approach combines spatiotemporal feature extraction with action recognition techniques to identify and classify anomalous human activities.

예시 입력: 최적의 대중교통 경로를 추천하는 서비스
예시 출력: We propose an intelligent route recommendation system for public transportation networks. The method leverages graph-based optimization and reinforcement learning to generate time-efficient and cost-effective itineraries from dynamic transit data.

사용자 입력: {user_input}
출력:
"""

    messages = [{"role": "user", "content": prompt_content}]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=150,
        temperature=0.1,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )

    generated_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return response.strip()


if __name__ == "__main__":
    llm_model, llm_tokenizer = init_hyde_model()

    print("\n" + "=" * 60)
    print("HyDE 영문 초록 생성 테스트")
    print("종료하려면 'q', 'quit', 'exit' 중 하나를 입력하세요.")
    print("=" * 60)

    while True:
        user_input = input("\n프로젝트 주제를 입력하세요: ").strip()

        if user_input.lower() in ["q", "quit", "exit"]:
            print("테스트를 종료합니다.")
            break

        if not user_input:
            continue

        print("\n영문 초록을 생성하는 중...")
        english_abstract = generate_hypothetical_abstract(
            user_input,
            llm_model,
            llm_tokenizer,
        )

        print("-" * 60)
        print(f"[생성된 영문 초록]\n{english_abstract}")
        print("-" * 60)

"""영수증/보증서 이미지 업로드 후 처리 과정을 LangGraph로 표현한 그래프 스켈레톤입니다."""

from typing import TypedDict, Annotated, List

# langgraph import 는 실제 환경에서 설치된 후 동작합니다.
# 여기서는 구조만 스케치합니다.
try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
except Exception:  # 설치 전이라면 import 에러가 날 수 있으므로 방어적으로 처리
    StateGraph = object  # 타입 힌트용 더미
    END = "END"
    add_messages = list  # 더미


class DocumentState(TypedDict):
    """문서 처리 그래프에서 사용하는 상태 정의입니다.

    - image_path: 업로드된 이미지 경로
    - raw_text: OCR 결과 텍스트
    - parsed_fields: 파싱된 필드 정보(구매일/금액/구매처 등)
    - messages: 디버깅/로그 용 메시지 리스트(선택적)
    """

    image_path: str
    raw_text: str
    parsed_fields: dict
    messages: Annotated[List[str], add_messages]


def node_ocr(state: DocumentState) -> DocumentState:
    """이미지에서 텍스트를 추출하는 노드입니다.

    초급자용 설명:
    - LangGraph의 각 노드는 '입력 상태를 받아 출력 상태를 반환하는 함수' 형태입니다.
    - 여기서는 OCR 결과를 raw_text에 채우고, messages에 로그를 남깁니다.
    """
    # TODO: app.services.ocr_service.extract_text_from_image 를 호출하도록 구현
    state["raw_text"] = ""  # 실제 OCR 결과로 교체 예정
    state["messages"].append("OCR 완료 (스켈레톤)")

    return state


def node_parse(state: DocumentState) -> DocumentState:
    """raw_text 에서 구매일/금액/구매처 등을 파싱하는 노드입니다."""
    # TODO: 정규식 또는 LLM 기반 파싱 로직 추가
    state["parsed_fields"] = {}
    state["messages"].append("파싱 완료 (스켈레톤)")
    return state


def build_document_ingest_graph() -> "StateGraph | object":
    """문서 업로드 후 처리 파이프라인을 구성하는 LangGraph 그래프를 생성합니다.

    초급자용 설명:
    - 이 함수는 '어떤 순서로 어떤 노드들을 실행할지'를 정의합니다.
    - 실제 애플리케이션에서는 이 그래프를 불러와서 실행하게 됩니다.
    """
    try:
        graph = StateGraph(DocumentState)
        graph.add_node("ocr", node_ocr)
        graph.add_node("parse", node_parse)

        # 시작 노드 설정
        graph.set_entry_point("ocr")
        # OCR → 파싱 → 종료
        graph.add_edge("ocr", "parse")
        graph.add_edge("parse", END)

        return graph
    except Exception:
        # langgraph가 아직 설치되지 않은 상태에서는 더미 객체를 반환합니다.
        return object()

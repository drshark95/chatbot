import logging
import os
import threading
from pathlib import Path

import mecab
import pandas as pd
import pymysql.cursors

from .legacy_gensim import load_legacy_doc2vec


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "model" / "d2v_faqs_size200_min5_epoch20_ebs_science_qna.model"
DATA_PATH = BASE_DIR / "data" / "df2_20210601_edited.xlsx"

FILTER_MECAB = {
    "NNG",  # 보통명사
    "NNP",  # 고유명사
    "SL",  # 외국어
    "VV",  # 동사
    "VA",  # 형용사
    "NP",  # 대명사
    "NR",  # 수사
    "SN",  # 숫자
    "MAG",  # 일반부사
}

mecab_tokenizer = mecab.MeCab()
d2v_faqs = load_legacy_doc2vec(MODEL_PATH)
questions_and_answers = (
    pd.read_excel(DATA_PATH)
    .dropna(subset=["질문", "답변"])
    .reset_index(drop=True)
)

if len(d2v_faqs.dv) != len(questions_and_answers):
    raise RuntimeError(
        "Doc2Vec document count does not match the question dataset: "
        f"{len(d2v_faqs.dv)} != {len(questions_and_answers)}"
    )

_inference_lock = threading.Lock()


def tokenize_mecab(document):
    return [f"{word}/{tag}" for word, tag in mecab_tokenizer.pos(str(document))]


def tokenize_mecab_noun(document):
    return [
        f"{word}/{tag}"
        for word, tag in mecab_tokenizer.pos(str(document))
        if tag in FILTER_MECAB
    ]


def _database_logging_enabled():
    return os.environ.get("CHATBOT_LOG_DB_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _log_interaction(client_ip, useragent, similarity, question, matched_row):
    if not _database_logging_enabled():
        return

    required_settings = {
        "host": os.environ.get("CHATBOT_DB_HOST"),
        "user": os.environ.get("CHATBOT_DB_USER"),
        "password": os.environ.get("CHATBOT_DB_PASSWORD"),
        "database": os.environ.get("CHATBOT_DB_NAME"),
    }
    missing = [name for name, value in required_settings.items() if not value]
    if missing:
        logger.warning("Chat log database is enabled but settings are missing: %s", missing)
        return

    try:
        connection = pymysql.connect(
            **required_settings,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3,
        )
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO datalog (
                        client_ip, useragent, similarity, student_question,
                        dataset_question, answer
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        client_ip,
                        useragent,
                        float(similarity),
                        question,
                        matched_row["질문"],
                        matched_row["답변"],
                    ),
                )
            connection.commit()
    except pymysql.MySQLError:
        logger.exception("Failed to record the chatbot interaction")


def faq_answer(question, useragent="", client_ip=""):
    question = str(question).strip()
    if len(question) < 6:
        return "질문이 너무 짧아요. 좀 더 구체적으로 질문 부탁해요."

    tokens = tokenize_mecab_noun(question)
    if not tokens:
        return "질문에서 핵심 단어를 찾지 못했어요. 다른 표현으로 질문해 주세요."

    with _inference_lock:
        inferred_vector = d2v_faqs.infer_vector(tokens)
        matched_index, similarity = d2v_faqs.dv.most_similar(
            [inferred_vector], topn=1
        )[0]

    matched_row = questions_and_answers.iloc[int(matched_index)]
    _log_interaction(
        client_ip,
        useragent,
        similarity,
        question,
        matched_row,
    )

    if similarity < 0.6:
        return (
            "입력한 질문과 가장 유사한 질문의 유사도가 "
            f"{similarity * 100:0.1f}%라서 결과를 표시하지 않을게요. "
            "질문을 더 구체적으로 써 주세요."
        )

    return (
        f"입력한 질문과의 유사도: {similarity * 100:0.1f}%\n\n"
        f"질문: {matched_row['질문']}\n\n"
        f"답변: {matched_row['답변']}"
    )

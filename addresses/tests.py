import os
from unittest.mock import patch

from django.test import TestCase

from .faq_chatbot import (
    d2v_faqs,
    faq_answer,
    questions_and_answers,
    tokenize_mecab_noun,
)


class ChatbotModelTests(TestCase):
    def test_model_matches_dataset(self):
        self.assertEqual(len(d2v_faqs.dv), 1213)
        self.assertEqual(len(d2v_faqs.dv), len(questions_and_answers))
        self.assertEqual(d2v_faqs.vector_size, 50)

    def test_mecab_filters_supported_parts_of_speech(self):
        tokens = tokenize_mecab_noun('광합성은 왜 빛이 필요한가요?')
        self.assertIn('광합성/NNG', tokens)
        self.assertIn('왜/MAG', tokens)

    def test_short_question_returns_guidance(self):
        self.assertIn('질문이 너무 짧아요', faq_answer('왜요?'))

    @patch.dict(os.environ, {'CHATBOT_LOG_DB_ENABLED': 'false'}, clear=False)
    @patch('addresses.faq_chatbot.pymysql.connect')
    def test_answer_does_not_contact_database_by_default(self, connect):
        question = str(questions_and_answers.iloc[0]['질문'])
        answer = faq_answer(question)
        self.assertTrue(answer)
        connect.assert_not_called()


class ChatbotViewTests(TestCase):
    def test_health_check(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_root_redirects_to_chat_service(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/chat_service/', fetch_redirect_response=False)

    def test_chat_service_renders(self):
        response = self.client.get('/chat_service/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '과학 질문-답변 챗봇')

    @patch.dict(os.environ, {'CHATBOT_LOG_DB_ENABLED': 'false'}, clear=False)
    def test_chat_service_answers_form_post(self):
        response = self.client.post(
            '/chat_service/',
            {
                'input1': '1kg의 기준은 어떻게 정하였을까요?',
                'useragent1': 'Django test client',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['response'])

import os
from typing import List
import asyncio
import openai


class GPTSlideExpander:

    def __init__(self):
        self.configure_API_key()

    def configure_API_key(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")

    async def generate_explanation_with_retry(self, topic, main_topic, max_try):
        for _ in range(max_try):
            try:
                explanation = await self.generate_explanation_for_slide(topic, main_topic)
                return explanation
            except openai.error as e:
                print(f"Query attempt failed. Error: {e}")

        raise Exception(f"Query failed after {max_try} attempts.")

    def get_presentation_main_topic(self, presentation_text: str) -> str:
        gpt_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system",
                       "content": "You are a chatbot that extracts the main topic of a presentation based on the presentation's text."},
                      {"role": "user",
                       "content": f"Provide the main topic of this presentation based on the presentation's following text: {presentation_text} , no longer than one word."}]

        )
        return gpt_response['choices'][0]['message']['content']

    async def generate_explanation_for_slide(self, topic: str, base_topic: str) -> str:
        if topic and topic != ' ':
            messages = [
                {"role": "system",
                 "content": "You are a chatbot that generates expanded explanations about slide topics."},
                {"role": "user",
                 "content": f"Provide an explanation of the slide based on the content:{topic}, within the context of the main topic:{base_topic} if applicable, in up to 3 sentences."},
            ]
            gpt_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            return gpt_response['choices'][0]['message']['content']
        else:
            return ''

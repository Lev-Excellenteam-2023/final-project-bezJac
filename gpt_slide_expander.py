import os
import time
from typing import Dict
import asyncio
import openai


class GPTSlideExpander:
    """
        A class that utilizes OpenAI's GPT models to generate expanded explanations for presentation slides.
    """

    def __init__(self):
        GPTSlideExpander.configure_api_key()
        self.expanded_slide_explanations = {}

    @staticmethod
    def configure_api_key():
        """Configure OpenAI API key."""
        openai.api_key = os.getenv("OPENAI_API_KEY")

    @staticmethod
    def generate_presentation_main_topic(presentation_text: str, max_retry: int) -> str:
        """
        Generates the main topic of a presentation based on the presentation's text.
        Args:
            presentation_text (str): The text of the presentation.
            max_retry (int): The maximum number of retries for generating the main topic.
        Returns:
            str: The generated main topic of the presentation.
        Raises:
            RuntimeError: If the query fails after reaching the maximum number of retries.
            ValueError: If the presentation text is empty or invalid.
        """
        if presentation_text:
            retry_count = 0
            wait_time = 4  # Initial wait time in seconds

            while retry_count < max_retry:
                try:
                    gpt_response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "system",
                                   "content": "You are a chatbot that extracts the main topic of a presentation"
                                              " based on the presentation's text."},
                                  {"role": "user",
                                   "content": f"Provide the main topic of this presentation based on the presentation's"
                                              f" following text: {presentation_text} , no longer than one word."}]

                    )

                    return gpt_response['choices'][0]['message']['content']

                except openai.error as e:
                    pass  # error will be documented in log files in future

                # Increase wait time and retry
                retry_count += 1
                time.sleep(wait_time)
                wait_time += 1

            raise RuntimeError(f"Query failed after {max_retry} attempts.")

        else:
            raise ValueError("Invalid data. presentation's text cannot be empty.")

    async def generate_explanation_for_presentation(self, parsed_presentation: Dict[int, str], presentation_text: str,
                                                    max_retry: int) -> None:
        """
        Generates explanations for each slide in a presentation.
        Args:
            parsed_presentation (Dict[int, str]): A dictionary mapping slide index to slide content.
            presentation_text (str): The  full concatenated text of the presentation.
            max_retry (int): The maximum number of retries for generating an explanation for each slide.
        Raises:
            RuntimeError: If the main topic retrieval from the API fails.
        Returns:
            None
        """
        try:
            main_topic = GPTSlideExpander.generate_presentation_main_topic(presentation_text, max_retry)
        except Exception as e:
            raise RuntimeError("failed to retrieve main topic from API", e.args[0])

        tasks = []
        # Generate tasks for each slide
        for index, slide in enumerate(parsed_presentation.values()):
            task = asyncio.create_task(
                GPTSlideExpander.generate_explanation_for_slide_with_retry(slide, main_topic, max_retry))
            tasks.append(task)

        # Execute tasks concurrently
        slide_index = 0
        for task in tasks:
            try:
                slide_index += 1
                explanation = await task
                self.expanded_slide_explanations[slide_index] = explanation
            except openai.error as e:
                self.expanded_slide_explanations[slide_index] = "ERROR - explanation generation for this slide failed\n"

    @staticmethod
    async def generate_explanation_for_slide_with_retry(topic: str, main_topic: str, max_try: int) -> str:
        """
        Generates an expanded explanation for a slide's topic with retry logic in case of API errors.
        Args:
            topic (str): The topic of the slide for which an explanation is to be generated (text extracted from slide).
            main_topic (str): The main topic of the presentation.
            max_try (int): The maximum number of attempts to generate an explanation.
        Returns:
            str: The generated expanded explanation.
        Raises:
            Exception: If the generation fails after the maximum number of attempts.
        """
        for _ in range(max_try):
            try:
                explanation = await GPTSlideExpander.generate_explanation_for_slide(topic, main_topic)
                return explanation
            except openai.error as e:
                print(f"Query attempt failed. Error: {e}")

        raise Exception(f"Query failed after {max_try} attempts.")

    @staticmethod
    async def generate_explanation_for_slide(topic: str, presentation_topic: str) -> str:
        """
        Generates an explanation for a slide topic within the context of the main topic.
        Args:
            topic (str): The topic of the slide for which an explanation is to be generated.
            presentation_topic (str): The main topic of the presentation.
        Returns:
            str: The generated expanded explanation. (empty str if slide has no text)
        """
        if topic and topic != ' ':
            messages = [
                {"role": "system",
                 "content": "You are a chatbot that generates expanded explanations about slide topics."},
                {"role": "user",
                 "content": f"Provide an explanation of the slide based on the content:{topic}, within the context of the main topic:{presentation_topic} if applicable, in up to 3 sentences."},
            ]
            gpt_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            return gpt_response['choices'][0]['message']['content']
        else:
            return ''

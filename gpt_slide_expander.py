import asyncio
import os
import time
from typing import Dict

import openai


class GptSlideExpander:
    """
    A class that utilizes OpenAI's GPT models to generate expanded explanations for presentation slides.

    Attributes:
    expanded_slide_explanations (Dict[int, str]): A dictionary that maps slide indices to their generated explanations.
    The keys represent the slide index, and the values are the corresponding expanded explanations for each slide.
    This dictionary is populated when `generate_explanation_for_presentation` is called.
    """

    def __init__(self):
        GptSlideExpander.configure_api_key()
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

    async def generate_explanation_for_presentation(self, parsed_presentation: Dict[int, str], presentation_topic: str,
                                                    max_retry: int) -> None:
        """
        Generates explanations for each slide in a presentation.
        Args:
            parsed_presentation (Dict[int, str]): A dictionary mapping slide index to slide content.
            presentation_topic (str): main topic of presentation.
            max_retry (int): The maximum number of retries for generating an explanation for each slide.
        Raises:
            RuntimeError: If the main topic retrieval from the API fails.
        Returns:
            None
        """
        # Generate tasks for each slide
        tasks = [
            asyncio.create_task(
                GptSlideExpander.process_individual_slide_explanation_safely(slide, presentation_topic, max_retry,
                                                                             index + 1))
            for index, slide in enumerate(parsed_presentation.values())]

        # Execute tasks concurrently using event_run_loop
        results = await asyncio.gather(*[asyncio.shield(task) for task in tasks])

        # Assign results to slide explanations
        for slide_index, explanation in enumerate(results, start=1):
            self.expanded_slide_explanations[slide_index] = explanation

    @staticmethod
    async def generate_explanation_for_slide_with_retry(slide_text: str, presentation_topic: str, max_try: int) -> str:
        """
        Generates an expanded explanation for a slide's topic with retry logic in case of API errors.
        Args:
            slide_text (str): The topic of the slide for which an explanation is to be generated (text extracted from slide).
            presentation_topic (str): The main topic of the presentation.
            max_try (int): The maximum number of attempts to generate an explanation.
        Returns:
            str: The generated expanded explanation.
        Raises:
            Exception: If the generation fails after the maximum number of attempts.
        """
        for _ in range(max_try):
            try:
                explanation = await GptSlideExpander.generate_explanation_for_slide(slide_text, presentation_topic)
                return explanation
            except openai.error as e:
                print(f"Query attempt failed. Error: {e}")

        raise Exception(f"Query failed after {max_try} attempts.")

    @staticmethod
    async def generate_explanation_for_slide(slide_text: str, presentation_topic: str) -> str:
        """
        Generates an explanation for a slide topic within the context of the main topic.
        Args:
            slide_text (str): The text of the slide for which an explanation is to be generated.
            presentation_topic (str): The main topic of the presentation.
        Returns:
            str: The generated expanded explanation. (empty str if slide has no text)
        """
        if slide_text and slide_text != ' ':
            messages = [
                {
                    "role": "system",
                    "content": "You are a chatbot that generates expanded explanations about slide topics."
                },
                {
                    "role": "user",
                    "content": f"Please provide an expanded explanation for the slide content. "
                               f"The slide topic is: {slide_text}. "
                               f"If applicable, provide the explanation within the context of the "
                               f"main topic: {presentation_topic}. "
                               f"Please make the explanation natural and expand on the slide topic with"
                               f" relevant details. make the explanation up tp 3 sentences"
                }
            ]

            gpt_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            return gpt_response['choices'][0]['message']['content']
        else:
            return 'No text in the slide - unable to generate explanation'

    @staticmethod
    async def process_individual_slide_explanation_safely(slide_text: str, presentation_topic: str, max_retry: int,
                                                          slide_index: int) -> str:
        """
        Process an individual slide task for generating an explanation.
        Args:
            slide_text: The text of the slide to generate an explanation for.
            presentation_topic: The topic or context of the presentation.
            max_retry: The maximum number of retries for generating the explanation.
            slide_index: The index of the slide being processed.
        Returns:
            The generated explanation for the slide, or an error message if an `openai.error` occurs.
        Raises:
            openai.error: If an OpenAI API error occurs during explanation generation for the slide.
        """
        try:
            return await GptSlideExpander.generate_explanation_for_slide_with_retry(slide_text, presentation_topic,
                                                                                    max_retry)
        except openai.error as e:
            return f"ERROR - explanation generation for slide {slide_index} failed: {str(e)}"

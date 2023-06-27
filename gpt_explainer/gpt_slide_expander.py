import asyncio
import json
import os
import threading
import time
from typing import Dict, List
from pptx_parser.pptx_parser import PPTXParser
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
        self.processed_files_lock = threading.Lock()
        self.uploads_folder = ""
        self.output_folder = ""

    def set_output_folder(self, output_path: str) -> None:
        self.output_folder = output_path

    def set_uploads_folder(self, uploads_path: str) -> None:
        self.uploads_folder = uploads_path

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

    @staticmethod
    async def generate_explanation_for_presentation(parsed_presentation: Dict[int, str], presentation_topic: str,
                                                    max_retry: int) -> Dict[int, str]:
        """
        Generates explanations for each slide in a presentation.
        Args:
            parsed_presentation (Dict[int, str]): A dictionary mapping slide index to slide content.
            presentation_topic (str): main topic of presentation.
            max_retry (int): The maximum number of retries for generating an explanation for each slide.
        Raises:
            RuntimeError: If the main topic retrieval from the API fails.
        Returns:
            generated_explanation_dictionary: Dict of slide numbers and the explanations generated for the slides
        """
        tasks = [
            asyncio.create_task(
                GptSlideExpander.process_individual_slide_explanation_safely(slide, presentation_topic, max_retry,
                                                                             index + 1))
            for index, slide in enumerate(parsed_presentation.values())]

        results = await asyncio.gather(*[asyncio.shield(task) for task in tasks])

        generated_explanation_dictionary = {}
        for slide_index, explanation in enumerate(results, start=1):
            generated_explanation_dictionary[slide_index] = explanation
        return generated_explanation_dictionary

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

    def run_explainer(self) -> None:
        """
        Runs the GPT explainer system indefinitely, processing files dropped into the 'uploads' folder.
        The explainer sleeps for 10 seconds between iterations.
        """
        while True:
            files_to_process = self.get_files_to_process()
            for file_path in files_to_process:
                self.process_file(file_path)
                time.sleep(10)  # Sleep for 10 seconds between processing each file

    def get_files_to_process(self) -> List[str]:
        """
        Scans the 'uploads' folder and identifies the files that haven't been processed yet.
        Returns:
            list: A list of file paths that need to be processed.
        """

        files_to_process = []

        with self.processed_files_lock:
            processed_files = set(self.expanded_slide_explanations.keys())

        for file_name in os.listdir(self.uploads_folder):
            if file_name not in processed_files:
                file_path = os.path.join(self.uploads_folder, file_name)
                files_to_process.append(file_path)

        return files_to_process

    def process_file(self, file_path: str) -> None:
        """
        Processes a file using the existing code for parsing and generating explanations.
        Saves the explanation JSON in the 'outputs' folder.
        Args:
            file_path (str): The path of the file to process.
        """
        pptx_parser = PPTXParser(file_path)
        pptx_parser.extract_text_from_presentation()

        presentation_topic = GptSlideExpander.generate_presentation_main_topic(pptx_parser.get_presentation_full_text(),
                                                                               max_retry=3)
        file_name = os.path.basename(file_path)
        self.update_processed_files(file_name)

        print(f"Processing file: {file_name}")

        result = asyncio.run(
            GptSlideExpander.generate_explanation_for_presentation(pptx_parser.parsed_slides_dictionary,
                                                                   presentation_topic,
                                                                   max_retry=3))

        self.save_explanation_json(file_name, result)

        print(f"File processed: {file_name}")

    def update_processed_files(self, file_name: str) -> None:
        """
        Updates the set of processed files in a thread-safe manner.
        Args:
            file_name (str): The name or unique identifier of the processed file.
        """
        with self.processed_files_lock:
            self.expanded_slide_explanations[file_name] = True

    def save_explanation_json(self, file_name: str, explanation_result: Dict[int, str]) -> None:
        """
        Saves the explanation JSON for the processed file in the 'outputs' folder.
        Args:
            file_name (str): The name of the processed file.
            explanation_result (dict): Dictionary containing the explanations for presentation slides.
        """
        output_file_name = os.path.splitext(file_name)[0] + ".json"
        output_path = os.path.join(self.output_folder, output_file_name)
        with open(output_path, "w") as file:
            json.dump(explanation_result, file, indent=4)


if __name__ == '__main__':
    explainer = GptSlideExpander()
    explainer.set_uploads_folder(r'C:\Users\mybj2\Desktop\School\Excellenteam\python\final-project-bezJac\uploads')
    explainer.set_output_folder(r'C:\Users\mybj2\Desktop\School\Excellenteam\python\final-project-bezJac\outputs')
    explainer.run_explainer()

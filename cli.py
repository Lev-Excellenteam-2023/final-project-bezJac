import argparse
import asyncio
import json
from typing import Dict
from pptx_parser import PPTXParser
from gpt_slide_expander import GptSlideExpander

"""
This script generates slide explanations from a PowerPoint (PPTX) file. It utilizes the `PPTXParser` class to extract
text from the slides and the GPTSlideExpander class to expand the explanations for each slide using the OpenAI GPT API.
The script accepts a path to the PPTX file as a command-line argument, along with an optional argument for the main 
topic of the presentation. If the main topic is not provided, the script generates it using the 
`generate_presentation_main_topic` method of the `GPTSlideExpander` class.
The parsed presentation data is then passed to the `generate_explanation_for_presentation` method of the 
`GPTSlideExpander` class. This method uses the GPT API to expand the explanations asynchronously.
Finally, the expanded slide explanations are stored in a dictionary, and the script outputs them to a JSON file with
the same name as the input PPTX file.
Overall, this script automates the process of extracting slide text, generating slide explanations, 
and storing the results in a JSON file, making it easier to analyze and work with PowerPoint presentations.
"""


def parse_cli_args() -> argparse.Namespace:
    """Parse command-line arguments.
    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    argument_parser = argparse.ArgumentParser(description="Generate slide explanations from a PPTX file")
    argument_parser.add_argument("pptx_file", help="Path to the PPTX file")
    argument_parser.add_argument("-t", "--topic", help="Main topic of the presentation")
    return argument_parser.parse_args()


def output_to_json(output_path: str, expanded_slide_explanations: Dict[int, str]) -> None:
    """Output the expanded slide explanations to a JSON file.

    Args:
        output_path (str): Path to the output JSON file.
        expanded_slide_explanations (Dict[int, str]): Dictionary with slide numbers as keys and explanations as values.
    """
    with open(output_path, "w") as file:
        json.dump(expanded_slide_explanations, file, indent=4)


def main(cli_args: argparse.Namespace) -> None:
    """
    Main program logic.
    Args:
        cli_args (argparse.Namespace): Parsed command-line arguments.
    """
    pptx_parser = PPTXParser(cli_args.pptx_file)
    pptx_parser.extract_text_from_presentation()

    slide_expander = GptSlideExpander()

    presentation_main_topic = cli_args.topic

    if not presentation_main_topic:
        presentation_main_topic = slide_expander.generate_presentation_main_topic(
            pptx_parser.get_presentation_raw_text(), max_retry)

    asyncio.run(
        slide_expander.generate_explanation_for_presentation(pptx_parser.pptx_parsed_data, presentation_main_topic,
                                                             max_retry))

    # Output the explanations to a JSON file
    output_file = cli_args.pptx_file.replace(".pptx", ".json")
    output_to_json(output_file, slide_expander.expanded_slide_explanations)


if __name__ == "__main__":
    parsed_args = parse_cli_args()
    max_retry = 3
    main(parsed_args)

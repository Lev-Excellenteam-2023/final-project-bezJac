

from parse_pptx import pptx_parser
import pytest


@pytest.fixture
def parser():
    path = "IOT_ppt.pptx"
    parser = pptx_parser(path)
    return parser


def test_extract_text_from_presentation(parser):
    #  copyright symbol is removed when parsing the entire presentation
    parser.extract_text_from_presentation()
    expected_results = {
        1: '',
        2: '   = 17,300,000,000,000  GB 17.3 ZB ',
        3: 'Top IoT Applications  ',
        4: ' ',
        5: 'Benefits:  Efficiency and productivity Cost reduction Customer experience  ',
        6: 'Efficiency &  Productivity ',
        7: 'Cost reduction ',
        8: 'Customer  experience ',
        9: '',
        10: 'Thank you for participating Contact me: jacober@g.jct.ac.il ',
    }
    assert parser.parsing_results_dict == expected_results


def test_extract_text_from_slide_with_text(parser):
    # extracts the raw data, copyright symbol still in the text
    slide = parser.presentation.slides[2]
    result = pptx_parser.extract_text_from_slide(slide)
    assert result == 'Top IoT Applications © '


def test_extract_text_from_slide_without_text(parser):
    slide = parser.presentation.slides[0]
    result = pptx_parser.extract_text_from_slide(slide)
    assert result == ''

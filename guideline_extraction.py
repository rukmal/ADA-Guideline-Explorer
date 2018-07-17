from bs4 import BeautifulSoup
from bs4.element import Tag
from json import dump
from pprint import pprint
import re
from requests import get
import random


# Constants
BASE_URL = 'http://care.diabetesjournals.org'
TOC_PATH = '/content/41/Supplement_1'
OUTPUT_FILE = 'ADA2018Guidelines.json'

# Output variables
parsed_guidelines = list()

# Application variables
current_chapter_title = ''
current_chapter_title_tag = None
current_chapter = None
current_chapter_citations = None


def main():
    """Script to dynamically create a structured JSON file from the ADA
    Diabetes Guidelines Standards of Care 2018.
    """

    # Starting at main (contents) page
    guidelines_parent_raw = get(BASE_URL + TOC_PATH).text
    # Parse with BeautifulSoup
    guidelines_parent = BeautifulSoup(guidelines_parent_raw, 'html.parser')

    # Isolating chapters
    chapters = guidelines_parent.find(
                    id='PositionStatements').next_sibling.children
    
    # Iterating through and processing chapters
    count = 1
    for chapter in chapters:
        if count == 12:
            print('Skipping chapter 12 as it is not loading correctly.')
            continue
        print(count)
        parsed_chapter = processChapter(chapter)
        global parsed_guidelines
        parsed_guidelines.append(parsed_chapter)
        count += 1
    
    # Writing to JSON file
    with open(OUTPUT_FILE, 'w') as outfile:
        dump(parsed_guidelines, outfile, indent=2)


def processChapter(chapter: Tag) -> dict:
    """Function to donwload, parse and extract chapter information given the
    BeautifulSoup Tag object corresponding to the Chapter list item.
    See the webpage and its underlying structure for guidance on how this
    script was designed.
    
    Arguments:
        chapter {Tag} -- Chapter list item
    
    Returns:
        dict -- Parsed Chapter
    """

    out = dict()   # Output data

    # Extracting chapter path and title text
    # (structure derived from webpage)
    chapter_path = chapter.div.div.div.a.get('href')
    title_text = chapter.div.div.div.a.span.text

    # Parsing chapter title and number
    out['chapter_number'], out['chapter_title'] = parseChapterTitle(title_text)
    global current_chapter_title
    current_chapter_title = out['chapter_title']

    # Adding full chapter URL to output
    out['chapter_url'] = BASE_URL + chapter_path

    # Downloading chapter webpage
    chapter_raw = get(BASE_URL + chapter_path).text
    chapter_parsed = BeautifulSoup(chapter_raw, 'html.parser')
    
    # Saving to global variable
    global current_chapter
    current_chapter = chapter_parsed

    # Building references map
    global current_chapter_citations
    current_chapter_citations = buildCitations(chapter_parsed)

    # Extracting abstract
    out['abstract'] = getAbstract(chapter_parsed.find(isolateAbstract))

    # Isolating recommendation blocks
    chapter_recommendation_blocks = chapter_parsed \
        .find_all(isolateRecommendations)
    
    recommendation_groups = list()

    for recommendation_block_raw in chapter_recommendation_blocks:
        recommendation_block = extractRecommendations(recommendation_block_raw)
        recommendation_groups.append(recommendation_block)
    
    out['recommendation_groups'] = recommendation_groups

    pprint(out, indent=2, width=160)
    return out


def extractRecommendations(recommendation_tag: Tag) -> dict:
    """Extract the recommendations, given a recommendation tag.
    
    Arguments:
        recommendation_tag {Tag} -- Recommendation tag to be parsed.
    
    Returns:
        dict -- Structured dictionary with recommendation
                and corresponding grade.
    """

    rec_block = dict()  # Output data

    rec_block['title'] = getRecommendationTitle(recommendation_tag)
    
    rec_block['recommendations'] = list()

    rec_block['discussion'] = current_chapter_title_tag.parent.text \
        if current_chapter_title_tag is not None else ''

    if recommendation_tag.next_sibling is None:
        # Recommendation subcategories
        for subcategory in recommendation_tag.parent.parent.next_siblings:
            if subcategory.find('ul') is not None:
                rec_block['recommendations'] += parseRecommendation(
                    subcategory.find('ul'))
    else:
        rec_block['recommendations'] = parseRecommendation(
            recommendation_tag.next_sibling)
    
    # rec_block['citations'] # citations under this block
    rec_block['citations'] = getCitations()

    return rec_block


def parseRecommendation(recommendation_group: Tag, parent: str='') -> list:
    """Parses recommendations, and returns parsed recommendations as list,
    with grade information extracted.
    
    Arguments:
        recommendation_group {Tag} -- Tag to be parsed.
    
    Keyword Arguments:
        parent {str} -- String of parent recommendation for nested
                        recommendation lists (default: {''}).
    
    Returns:
        list -- Parsed list of recommendations
    """

    recommendations = list()  # Output

    # This is to deal with the bug of sub-lists within a recommendation
    try:
        for recommendation in recommendation_group:
            recommendation_text = parent + recommendation.text
            try:
                recommendation_grade = getRecommendationGrade(recommendation)
                recommendations.append(
                    {'content': formatRecommendation(recommendation_text),
                     'grade': recommendation_grade})
            except:
                parent_text = recommendation_text
                # Nested recommendations - call again
                recommendations += parseRecommendation(
                    recommendation_group.next_sibling, parent=parent_text)
            try:
                # Check for recommendations in subsequent list
                recommendations += parseRecommendation(
                    recommendation_group.next_sibling.next_sibling)
            except:
                pass
    except:
        pass
    
    return recommendations


def getRecommendationTitle(recommendation_tag: Tag) -> str:
    """Get the title of the recommendation group, given the recommendation
    heading Tag. If none is found, the chapter title is returned.
    
    Arguments:
        recommendation_tag {Tag} -- Tag of Recommendations heading.
    
    Returns:
        str -- Title of the recommendation category; chapter title used if
               none is found.
    """

    global current_chapter_title_tag

    try:
        title_tag = recommendation_tag.parent \
            .previous_sibling
        current_chapter_title_tag = title_tag
        return title_tag.text.title()
    except:
        pass

    try:
        title_tag = recommendation_tag.parent.parent \
            .previous_sibling
        current_chapter_title_tag = title_tag
        return title_tag.text.title()
    except:
        return current_chapter_title


def isolateAbstract(tag: Tag) -> bool:
    """Helper function to isolate the abstract from each chapter.
    
    Arguments:
        tag {Tag} -- Tag to be checked.
    
    Returns:
        bool -- True if abstract title, false otherwise.
    """

    return (tag.name == 'h2') and (tag.text == 'Abstract')


def getAbstract(tag: Tag) -> str:
    """Extract the abstract text, given the BeautifulSoup element.
    
    Arguments:
        tag {Tag} -- Abstract element.
    
    Returns:
        str -- Abstract text.
    """

    return tag.next_sibling.text


def isolateRecommendations(tag: Tag) -> bool:
    """Helper function to isolate recommendation blocks from each chapter.
    
    Arguments:
        tag {Tag} -- Tag to be checked.
    
    Returns:
        bool -- True if recommendation, false otherwise.
    """

    return (tag.name == 'h4') and \
        ((tag.text == 'Recommendations') or (tag.text == 'Recommendation'))


def parseChapterTitle(title_text: str) -> (int, str):
    """Parse the chapter title text and extract chapter title
    and chapter number.
    
    Arguments:
        title_text {str} -- Title raw text from BeautifulSoup.
    
    Returns:
        tuple -- (chapter_numer, chapter_title) tuple
            with extracted information.
    """
    
    dot_split = title_text.split('.')
    chapter_number = int(dot_split[0])
    chapter_title = dot_split[1].split(':')[0].strip()
    return (chapter_number, chapter_title)


def formatRecommendation(recommendation_text: str) -> str:
    """Format the recommendation string by removing the recommendation grade.
    
    Arguments:
        recommendation_text {str} -- Recommendation string to be formatted.
    
    Returns:
        str -- Formatted recommendation string.
    """

    # Splitting on periods
    recommendation_text_split = recommendation_text.split('.')

    # Removing recommendation text
    recommendation_text_split.pop()

    # Recombining and returning sentence without recommendation
    return '.'.join(recommendation_text_split) + '.'


def getRecommendationGrade(recommendation: Tag) -> str:
    """Extract the grade for a given recommendation.
    
    Arguments:
        recommendation {Tag} -- Recommendation tag to be parsed.
    
    Raises:
        Exception -- Raised when grade is not found.
    
    Returns:
        str -- Grade of the recommendation.
    """

    # Change if additional grades are added
    possible_grades = ['A', 'B', 'C', 'E']

    # Extract 'strong' type objects
    strong_objects = recommendation.find_all('strong')

    # Only extract if grade
    for strong in strong_objects:
        if strong.text in possible_grades:
            return strong.text

    # No recommendation grade found
    raise Exception


def getCitations() -> list:
    """Function to get citations for the current recommendation block.
    
    Returns:
        list -- List of citations.
    """

    citations = list()
    try:
        citations_raw = current_chapter_title_tag.parent.find_all(
            'a', class_='xref-bibr')
    except:
        citations_raw = current_chapter.find_all('a', class_='xref-bibr')
    for citation in citations_raw:
        citations.append(
            current_chapter_citations[re.sub('[^0-9]', '', citation.text)])
    return citations


def buildCitations(chapter: Tag) -> dict:
    """Function to build the dictionary of citations for a given chapter.
    
    Arguments:
        chapter {Tag} -- Tag of chapter to be parsed.
    
    Returns:
        dict -- Dictionary of citations for a given chapter.
    """

    parsed_citations = dict()
    # Isolating citations
    citations = chapter.find('ol', class_='cit-list')
    count = 1
    for citation in citations:
        parsed_citations[str(count)] = parseCitation(citation)
        count += 1
    return parsed_citations


def parseCitation(citation: Tag) -> str:
    """Function to parse a citation and return structured data. Currently
    not implemented.
    
    Arguments:
        citation {Tag} -- Tag to be parsed.
    
    Returns:
        str -- String of citation (temporary).
    """

    return citation.text

def getDiscussion(title_tag: Tag) -> str:
    """Function to locate and return discussion text for the current
    recommendation block. Currently returns raw text of discussion.
    
    Arguments:
        title_tag {Tag} -- Tag for the recommendation block title.
    
    Returns:
        str -- Text of discussion for recommendation block.
    """

    discussion = ''

    if title_tag is not None:
        discussion_raw = title_tag.parent.text
        # TODO: Process raw discussion text
        discussion = discussion_raw
    else:
        # Full chapter recommendations
        discussion = current_chapter.text
    
    return discussion

if __name__ == "__main__":
    main()

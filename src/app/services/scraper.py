import asyncio
import re
from typing import List

import aiofiles
import fitz
from docx import Document
from rapidfuzz import fuzz

from src.app.typing.scraper import ScraperService, EmptyListOrListStr
from src.settings.config import logger
from src.app.services.responses import ServiceErrorResponse


class FileScraperService:
    def __init__(self):
        self.keywords = []

    async def file_processing(self, file_path: str, keywords: List[str]) -> ScraperService:
        """
        Process the file using the internal methods.
        First, download the file from the S3 bucket, after that extract text and then search for the keywords.

        :param file_path: Path to the file in the temporary directory.
        :param keywords: List of keywords to search in the file.
        :return: A tuple (`lust[str]`, `True`) if the process is successful.
                 A tuple (`str`, `False`) with an error message if the process fails.
        """

        try:
            self.keywords = keywords
            if file_path.endswith(".txt"):
                return await self.search_in_txt(file_path), True
            elif file_path.endswith(".docx"):
                return await self.search_in_docx(file_path), True
            elif file_path.endswith(".pdf"):
                return await self.search_in_pdf(file_path), True
        except Exception as e:
            logger.error(f"An internal error while scrapping: {str(e)}")
            return ServiceErrorResponse.INTERNAL_ERROR, False
        return ServiceErrorResponse.UNSUPPORTED_FILE_FORMAT, False

    async def search_in_txt(self, file_path: str) -> EmptyListOrListStr:
        """
        Read the text file and call the function to search for the keywords.

        :param file_path: Input file path.
        :return: Empty list if no matches found, otherwise list of sentences with the keywords.
        """

        async with aiofiles.open(file=file_path, mode="r", encoding="utf-8") as file:
            logger.info("Reading file")
            result = await file.read()
            logger.info("File has been read")
            return self.find_sentences_with_fuzzy_keywords(result)

    async def search_in_docx(self, file_path: str) -> EmptyListOrListStr:
        """
        Acts as an asynchronous shell for the synchronous _extract_docx function

        :param file_path: Input file path.
        :return: Empty list if no matches found, otherwise list of sentences with the keywords.
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_docx, file_path)

    def _extract_docx(self, file_path: str) -> EmptyListOrListStr:
        """
        Read the text file and call the function to search for the keywords.

        :param file_path: Input file path.
        :return: Empty list if no matches found, otherwise list of sentences with the keywords.
        """

        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

        logger.info("Reading file")
        found_sentences = []
        for paragraph in paragraphs:
            found_sentences.extend(self.find_sentences_with_fuzzy_keywords(paragraph))

        logger.info("File has been read")
        return found_sentences

    async def search_in_pdf(self, file_path: str) -> EmptyListOrListStr:
        """
        Read the text file and call the function to search for the keywords.

        :param file_path: Input file path.
        :return: Empty list if no matches found, otherwise list of sentences with the keywords.
        """

        doc = fitz.open(file_path)

        logger.info("Reading file")
        tasks = [asyncio.to_thread(self._sync_extract_page, page) for page in doc]
        pages_text = await asyncio.gather(*tasks)
        logger.info("File has been read")

        tasks = [asyncio.to_thread(self.find_sentences_with_fuzzy_keywords, page_text) for page_text in pages_text]
        results = await asyncio.gather(*tasks)

        return [sentence for result in results for sentence in result]

    def _sync_extract_page(self, page) -> str:
        """Extract text from the page."""
        return page.get_text("text")

    def find_sentences_with_fuzzy_keywords(self, text: str, threshold: int = 80) -> EmptyListOrListStr:
        """
        Search for sentences in the given text that contain fuzzy matches to predefined keywords.

        This function splits the input text into sentences and checks each sentence for fuzzy matches
        to the set of keywords stored in `self.keywords`. The match is determined based on the
        similarity ratio between the words in each sentence and the keywords using fuzzy string matching.
        Sentences that contain the highest number of fuzzy matches are returned.

        Parameters:
        - text (str):
            A string containing the text to search through. This text will be split into sentences
            to perform the fuzzy search for keywords.

        - threshold (int, default=80):
            An integer between 0 and 100 that defines the minimum similarity ratio (in percentage)
            required for a word in a sentence to be considered a match to a keyword. The default value is 80.
            A higher value means stricter matching criteria.

        Returns:
        - List[str]:
            A list of sentences that have the highest number of fuzzy keyword matches.
            If no matches are found, returns an empty list. Each sentence in the result is a string.
        """

        keywords = [kw.lower() for kw in self.keywords]
        clean_text = re.sub(r"\s*\n\s*", " ", text)
        sentences = re.split(r"(?<=[.!?])\s+", clean_text)

        logger.info("Start searching for keywords")

        matched_sentences = []
        for sentence in sentences:
            words = sentence.lower().split()
            if all(any(fuzz.ratio(word, keyword) >= threshold for word in words) for keyword in keywords):
                matched_sentences.append(sentence)

        if not matched_sentences:
            logger.info("No matches found")
            return []

        logger.info("File searching completed")
        return matched_sentences

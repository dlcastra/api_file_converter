import asyncio
import re
import tempfile
from collections import defaultdict
from typing import List

import aiofiles
import fitz
from docx import Document
from rapidfuzz import fuzz

from src.app.typing.scraper import ScraperService, EmptyListOrListStr
from src.app.aws.utils import download_file
from src.settings.config import logger


class FileScraperService:
    def __init__(self):
        self.keywords = []

    async def file_processing(self, s3_key: str, bucket: str, keywords: List[str]) -> ScraperService:
        """
        Process the file using the internal methods.
        First, download the file from the S3 bucket, after that extract text and then search for the keywords.

        :param s3_key: Name of the file in the S3 bucket.
        :param bucket: S3 bucket name.
        :param keywords: List of keywords to search in the file.
        :return: A tuple (`lust[str]`, `True`) if the process is successful.
                 A tuple (`str`, `False`) with an error message if the process fails.
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = f"{tmpdir}/{s3_key}"
            self.keywords = keywords

            try:
                message, is_downloaded = await download_file(bucket, s3_key, file_path)
                if not is_downloaded:
                    return message, False

                if file_path.endswith(".txt"):
                    return await self.search_in_txt(file_path), True
                elif file_path.endswith(".docx"):
                    return await self.search_in_docx(file_path), True
                elif file_path.endswith(".pdf"):
                    return await self.search_in_pdf(file_path), True

            except Exception as e:
                return str(e), False

            return "Unsupported file type", False

    async def search_in_txt(self, file_path: str) -> EmptyListOrListStr:
        async with aiofiles.open(file=file_path, mode="r", encoding="utf-8") as file:
            logger.info("Reading file")
            result = await file.read()
            logger.info("File has been read")
            return self.find_sentences_with_fuzzy_keywords(result)

    async def search_in_docx(self, file_path: str) -> EmptyListOrListStr:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_docx, file_path)

    def _extract_docx(self, file_path: str) -> EmptyListOrListStr:
        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

        logger.info("Reading file")
        found_sentences = []
        for paragraph in paragraphs:
            found_sentences.extend(self.find_sentences_with_fuzzy_keywords(paragraph))

        logger.info("File has been read")
        return found_sentences

    async def search_in_pdf(self, file_path: str) -> EmptyListOrListStr:
        doc = fitz.open(file_path)

        logger.info("Reading file")
        tasks = [asyncio.to_thread(self._sync_extract_page, page) for page in doc]
        pages_text = await asyncio.gather(*tasks)
        logger.info("File has been read")

        tasks = [asyncio.to_thread(self.find_sentences_with_fuzzy_keywords, page_text) for page_text in pages_text]
        results = await asyncio.gather(*tasks)

        return [sentence for result in results for sentence in result]

    def _sync_extract_page(self, page) -> str:
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

        sentence_scores = defaultdict(int)

        logger.info("Start searching for keywords")
        for sentence in sentences:
            words = sentence.lower().split()
            match_count = sum(any(fuzz.ratio(word, keyword) >= threshold for word in words) for keyword in keywords)

            if match_count > 0:
                sentence_scores[sentence] = match_count

        if not sentence_scores:
            logger.info("No matches found")
            return []

        max_matches = max(sentence_scores.values())

        logger.info("File searching completed")
        return [sent for sent, count in sentence_scores.items() if count == max_matches]

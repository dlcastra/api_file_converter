import asyncio
import os
import re
import tempfile
from collections import defaultdict
from typing import List

import aiofiles
import fitz
from botocore.exceptions import ClientError
from docx import Document
from rapidfuzz import fuzz

from src.settings.aws_config import s3_client
from src.app.typing.scraper import ScraperService, EmptyListOrListStr


class FileScraperService:
    def __init__(self):
        self.keywords = []

    async def file_processing(self, s3_key: str, bucket: str, keywords: List[str]) -> ScraperService:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = f"{tmpdir}/{s3_key}"
            self.keywords = keywords

            try:
                await s3_client.download_file(bucket, s3_key, file_path)
                if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                    return f"Download failed: file {s3_key} is missing or empty", False

                if file_path.endswith(".txt"):
                    return await self.extract_text_from_txt(file_path), True
                elif file_path.endswith(".docx"):
                    return await self.extract_text_from_docx(file_path), True
                elif file_path.endswith(".pdf"):
                    return await self.extract_text_from_pdf(file_path), True
            except ClientError as error:
                return error.response["Error"]["Message"], False
            except Exception as e:
                return str(e), False

            return "Unsupported file type", False

    async def extract_text_from_txt(self, file_path: str) -> EmptyListOrListStr:
        async with aiofiles.open(file=file_path, mode="r", encoding="utf-8") as file:
            result = await file.read()
            return self.find_sentences_with_fuzzy_keywords(result)

    async def extract_text_from_docx(self, file_path: str) -> EmptyListOrListStr:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_docx, file_path)

    def _extract_docx(self, file_path: str) -> EmptyListOrListStr:
        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

        found_sentences = []
        for paragraph in paragraphs:
            found_sentences.extend(self.find_sentences_with_fuzzy_keywords(paragraph))

        return found_sentences

    async def extract_text_from_pdf(self, file_path: str) -> EmptyListOrListStr:
        doc = fitz.open(file_path)

        tasks = [asyncio.to_thread(self._sync_extract_page, page) for page in doc]
        pages_text = await asyncio.gather(*tasks)

        tasks = [asyncio.to_thread(self.find_sentences_with_fuzzy_keywords, page_text) for page_text in pages_text]
        results = await asyncio.gather(*tasks)

        return [sentence for result in results for sentence in result]

    def _sync_extract_page(self, page) -> str:
        return page.get_text("text")

    def find_sentences_with_fuzzy_keywords(self, text: str, threshold: int = 80) -> EmptyListOrListStr:
        keywords = [kw.lower() for kw in self.keywords]
        clean_text = re.sub(r"\s*\n\s*", " ", text)
        sentences = re.split(r"(?<=[.!?])\s+", clean_text)

        sentence_scores = defaultdict(int)

        for sentence in sentences:
            words = sentence.lower().split()
            match_count = sum(any(fuzz.ratio(word, keyword) >= threshold for word in words) for keyword in keywords)

            if match_count > 0:
                sentence_scores[sentence] = match_count

        if not sentence_scores:
            return []

        max_matches = max(sentence_scores.values())

        return [sent for sent, count in sentence_scores.items() if count == max_matches]

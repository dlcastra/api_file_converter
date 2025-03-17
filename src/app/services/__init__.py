from src.app.services.converter import FileConverterService
from src.app.services.scraper import FileScraperService


def get_file_converter_service() -> FileConverterService:
    return FileConverterService()


def get_file_scraper_service() -> FileScraperService:
    return FileScraperService()

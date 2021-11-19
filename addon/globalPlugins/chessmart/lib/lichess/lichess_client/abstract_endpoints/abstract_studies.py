from abc import ABC, abstractmethod


class AbstractStudies(ABC):
    """An abstract class for Studies API Endpoint"""

    @abstractmethod
    def export_chapter(self, study_id: str, chapter_id: str):
        """Download one study chapter in PGN format."""
        pass

    @abstractmethod
    def export_all_chapters(self, study_id: str):
        """Download all chapters of a study in PGN format."""
        pass

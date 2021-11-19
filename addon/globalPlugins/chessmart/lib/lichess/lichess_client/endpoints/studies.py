from typing import TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_studies import AbstractStudies
from lichess_client.utils.enums import RequestMethods
from lichess_client.utils.hrefs import (
    STUDIES_EXPORT_ALL_CHAPTERS,
    STUDIES_EXPORT_CHAPTER,
)

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient
    from lichess_client.helpers import Response


class Studies(AbstractStudies):
    """Class for Studies API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def export_chapter(self, study_id: str, chapter_id: str) -> "Response":
        """
        Download one study chapter in PGN format.

        Parameters
        ----------
        study_id: str, required

        chapter_id: str, required

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.studies.export_chapter(study_id="...", chapter_id='...')
        """

        response = await self._client.request(
            method=RequestMethods.GET,
            url=STUDIES_EXPORT_CHAPTER.format(studyId=study_id, chapterId=chapter_id),
        )
        return response

    async def export_all_chapters(self, study_id: str) -> "Response":
        """
        Download all chapters of a study in PGN format.

        Parameters
        ----------
        study_id: str, required

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.studies.export_all_chapters(study_id="...")
        """

        response = await self._client.request(
            method=RequestMethods.GET,
            url=STUDIES_EXPORT_ALL_CHAPTERS.format(studyId=study_id),
        )
        return response

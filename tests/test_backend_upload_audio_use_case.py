from __future__ import annotations

import asyncio

import pytest

from backend_app.application.use_cases.upload_audio import UploadAudioUseCase
from backend_app.domain.errors import ExternalServiceError, ValidationError


class _MlServiceStub:
    def __init__(self, response: dict | None = None) -> None:
        self.response = response or {
            "job": {
                "id": "42",
                "status": "queued",
            }
        }
        self.calls: list[dict] = []

    async def submit_upload(
        self,
        *,
        filename: str,
        data: bytes,
        content_type: str,
        user_id: int | None = None,
        tablature_name: str | None = None,
    ) -> dict:
        self.calls.append(
            {
                "filename": filename,
                "data": data,
                "content_type": content_type,
                "user_id": user_id,
                "tablature_name": tablature_name,
            }
        )
        return self.response


def test_upload_audio_validates_filename_is_required() -> None:
    use_case = UploadAudioUseCase(ml_service=_MlServiceStub())

    with pytest.raises(ValidationError, match="Filename is required"):
        asyncio.run(
            use_case.execute(
                filename=None,
                data=b"abc",
                content_type="audio/mpeg",
            )
        )


def test_upload_audio_validates_non_empty_payload() -> None:
    use_case = UploadAudioUseCase(ml_service=_MlServiceStub())

    with pytest.raises(ValidationError, match="File is empty"):
        asyncio.run(
            use_case.execute(
                filename="track.mp3",
                data=b"",
                content_type="audio/mpeg",
            )
        )


def test_upload_audio_validates_mp3_extension() -> None:
    use_case = UploadAudioUseCase(ml_service=_MlServiceStub())

    with pytest.raises(ValidationError, match="Only .mp3 files are supported"):
        asyncio.run(
            use_case.execute(
                filename="track.wav",
                data=b"abc",
                content_type="audio/wav",
            )
        )


def test_upload_audio_returns_domain_artifact_and_passes_optional_fields() -> None:
    ml = _MlServiceStub()
    use_case = UploadAudioUseCase(ml_service=ml)

    result = asyncio.run(
        use_case.execute(
            filename="track.mp3",
            data=b"audio-bytes",
            content_type="audio/mpeg",
            user_id=7,
            tablature_name="My Track",
        )
    )

    assert result.id == "42"
    assert result.status == "queued"
    assert ml.calls and ml.calls[0]["user_id"] == 7
    assert ml.calls[0]["tablature_name"] == "My Track"


def test_upload_audio_raises_if_ml_service_payload_missing_job_fields() -> None:
    ml = _MlServiceStub(response={"job": {"id": None, "status": None}})
    use_case = UploadAudioUseCase(ml_service=ml)

    with pytest.raises(ExternalServiceError, match="missing job id or status"):
        asyncio.run(
            use_case.execute(
                filename="track.mp3",
                data=b"abc",
                content_type="audio/mpeg",
            )
        )


import pytest
from pydantic import ValidationError
from app.models import Users
from sqlmodel import Session
from unittest.mock import MagicMock, patch


from app.llm.cv_data_extractor import (
    Personal,
    WorkExperience,
    Education,
    Language,
    CV,
    CVLLMExtractor,
)


# Test the Personal model
def test_personal_model():
    # Valid input
    valid_personal = {
        "first_name": "John",
        "last_name": "Doe",
        "contact_number": "1234567890",
        "email": "john.doe@example.com",
        "summary": "Software Engineer with 10 years of experience.",
        "location": "New York",
        "personal_links": [
            "https://github.com/johndoe",
            "https://linkedin.com/in/johndoe",
        ],
    }
    personal = Personal(**valid_personal)
    assert personal.email == "john.doe@example.com"

    # Invalid email
    invalid_personal = valid_personal.copy()
    invalid_personal["email"] = "invalid-email"
    with pytest.raises(ValidationError):
        Personal(**invalid_personal)


# Test the WorkExperience model
def test_work_experience_model():
    work_experience = {
        "title": "Software Engineer",
        "company_name": "Tech Corp",
        "start_date": "2020-01",
        "end_date": "2022-01",
        "accomplishments": ["Developed software", "Led team"],
    }
    work_exp = WorkExperience(**work_experience)
    assert work_exp.title == "Software Engineer"


# Test the Education model
def test_education_model():
    education = {
        "degree": "Bachelor of Science in Computer Science",
        "institution": "Tech University",
        "start_date": "2016-01",
        "end_date": "2020-01",
        "accomplishments": ["Graduated with honors"],
    }
    edu = Education(**education)
    assert edu.degree == "Bachelor of Science in Computer Science"


# Test the Language model
def test_language_model():
    language = {"language": "English", "proficiency": "Native"}
    lang = Language(**language)
    assert lang.language == "English"


# Test the CV model
def test_cv_model():
    cv_data = {
        "personal": {
            "first_name": "John",
            "last_name": "Doe",
            "contact_number": "1234567890",
            "email": "john.doe@example.com",
            "summary": "Software Engineer with 10 years of experience.",
            "location": "New York",
            "personal_links": [
                "https://github.com/johndoe",
                "https://linkedin.com/in/johndoe",
            ],
        },
        "work_experiences": [
            {
                "title": "Software Engineer",
                "company_name": "Tech Corp",
                "start_date": "2020-01",
                "end_date": "2022-01",
                "accomplishments": ["Developed software", "Led team"],
            }
        ],
        "educations": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "Tech University",
                "start_date": "2016-01",
                "end_date": "2020-01",
                "accomplishments": ["Graduated with honors"],
            }
        ],
        "skills": ["Python", "Django"],
        "languages": [{"language": "English", "proficiency": "Native"}],
    }
    cv = CV(**cv_data)
    assert cv.personal.first_name == "John"
    assert len(cv.work_experiences) == 1
    assert len(cv.educations) == 1
    assert "Python" in cv.skills
    assert cv.languages[0].language == "English"


# Mock extract_text_from_pdf_bytes function
@pytest.fixture
def mock_extract_text_from_pdf_bytes():
    with patch(
        "app.llm.utils.extract_text_from_pdf_bytes", return_value="Extracted CV text"
    ):
        yield


def test_cvllmextractor(mock_extract_text_from_pdf_bytes):
    extractor = CVLLMExtractor(model_name="GPT3")

    mock_user = Users(
        id=1,
        name="John Doe",
        username="johndoe@gmail.com",
        password="pass",
        resume=b"PDF data",
        parsed_personal=None,
        parsed_work_experiences=None,
        parsed_educations=None,
        parsed_skills=None,
        parsed_languages=None,
        additional_info=None,
    )

    with patch.object(
        Session,
        "query",
        return_value=MagicMock(
            filter=MagicMock(
                return_value=MagicMock(first=MagicMock(return_value=mock_user))
            )
        ),
    ):
        with patch.object(Session, "commit", return_value=None):
            result = extractor.extract_cv_and_write_to_db(
                user_id=1, replace_existing_summary=True
            )
            assert result == 1


# Test with no resume uploaded
def test_cvllmextractor_no_resume(mock_extract_text_from_pdf_bytes):
    extractor = CVLLMExtractor(model_name="GPT")

    mock_user = Users(
        id=1,
        name="John Doe",
        username="johndoe@gmail.com",
        password="pass",
        resume=None,
        parsed_personal=None,
        parsed_work_experiences=None,
        parsed_educations=None,
        parsed_skills=None,
        parsed_languages=None,
        additional_info=None,
    )

    with patch.object(
        Session,
        "query",
        return_value=MagicMock(
            filter=MagicMock(
                return_value=MagicMock(first=MagicMock(return_value=mock_user))
            )
        ),
    ):
        result = extractor.extract_cv_and_write_to_db(
            user_id=1, replace_existing_summary=True
        )
        assert result == 0


# Test with user not found
def test_cvllmextractor_user_not_found(mock_extract_text_from_pdf_bytes):
    extractor = CVLLMExtractor(model_name=ModelNames.GPT3_TURBO.value)

    with patch.object(
        Session,
        "query",
        return_value=MagicMock(
            filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        ),
    ):
        result = extractor.extract_cv_and_write_to_db(
            user_id=1, replace_existing_summary=True
        )
        assert result == 0

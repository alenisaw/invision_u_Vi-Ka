from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ParentContact(BaseModel):
    model_config = ConfigDict(extra="ignore")

    last_name: str | None = None
    first_name: str | None = None
    phone: str | None = None


class PersonalInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    last_name: str
    first_name: str
    patronymic: str | None = None
    date_of_birth: date
    gender: str | None = None
    citizenship: str | None = None
    iin: str | None = None
    document_type: str | None = None
    document_no: str | None = None
    document_authority: str | None = None
    document_date: date | None = None


class ContactsInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    phone: str | None = None
    instagram: str | None = None
    telegram: str | None = None
    whatsapp: str | None = None


class ParentsInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    father: ParentContact | None = None
    mother: ParentContact | None = None


class AddressInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    country: str | None = None
    region: str | None = None
    city: str | None = None
    street: str | None = None
    house: str | None = None
    apartment: str | None = None


class AcademicInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    selected_program: str
    language_exam_type: str | None = None
    language_score: float | None = Field(default=None, ge=0.0)


class ContentInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    video_url: str | None = None
    essay_text: str | None = None
    project_descriptions: list[str] = Field(default_factory=list)
    experience_summary: str | None = None


class SocialStatusInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    has_social_benefit: bool = False
    benefit_type: str | None = None


class InternalTestAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question_id: str
    answer: str


class InternalTestInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    answers: list[InternalTestAnswer] = Field(default_factory=list)


class CandidateIntakeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    personal: PersonalInfo
    contacts: ContactsInfo = Field(default_factory=ContactsInfo)
    parents: ParentsInfo = Field(default_factory=ParentsInfo)
    address: AddressInfo = Field(default_factory=AddressInfo)
    academic: AcademicInfo
    content: ContentInfo = Field(default_factory=ContentInfo)
    social_status: SocialStatusInfo = Field(default_factory=SocialStatusInfo)
    internal_test: InternalTestInfo = Field(default_factory=InternalTestInfo)


class CandidateIntakeResponse(BaseModel):
    candidate_id: str
    pipeline_status: str = "pending"
    message: str = "Candidate received. Submit to pipeline to start analysis."

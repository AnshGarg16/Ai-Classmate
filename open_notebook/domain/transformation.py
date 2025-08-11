from typing import ClassVar, Optional

from pydantic import Field

from open_notebook.domain.base import ObjectModel, RecordModel


class Transformation(ObjectModel):
    table_name: ClassVar[str] = "transformation"
    name: str
    title: str
    description: str
    prompt: str
    apply_default: bool


class DefaultPrompts(RecordModel):
    record_id: ClassVar[str] = "open_notebook:default_prompts"
    transformation_instructions: Optional[str] = Field(
        None, description="Instructions for executing a transformation"
    )

import os
import google.generativeai as genai

# Load your Gemini key into both conventions:
gemini_key = os.getenv("GEMINI_API_KEY")
os.environ["GOOGLE_API_KEY"] = gemini_key  # langchain_google_genai expects this
genai.api_key = gemini_key
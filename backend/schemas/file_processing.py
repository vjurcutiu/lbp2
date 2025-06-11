from pydantic import BaseModel, Field
from typing import List

class ProcessFolderSchema(BaseModel):
    """
    Request schema for folder processing.
    """
    folder_paths: List[str] = Field(..., min_items=1)
    extensions: List[str] = Field(..., min_items=1)

class CancelSchema(BaseModel):
    """
    Request schema for cancelling a processing session.
    """
    session_id: str = Field(..., min_length=1)

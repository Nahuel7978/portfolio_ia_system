
from pydantic import BaseModel

class DocumentUpsertRequest(BaseModel):
    document_id: int
    content: str
    metadata: dict

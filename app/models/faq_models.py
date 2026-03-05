from pydantic import BaseModel, Field
from typing import List, Optional


class FAQItem(BaseModel):
    """Represents a single FAQ / knowledge-base item."""
    id: str = Field(..., description="Unique identifier (e.g. BSC_FAQ_1, BSC_DOC_3_CH_1)")
    category: str = Field(default="", description="Topic category (e.g. Membership, Facilities)")
    question: str = Field(default="", description="The FAQ question or document title")
    answer: str = Field(default="", description="The answer or document body text")
    keywords: List[str] = Field(default_factory=list, description="Optional keyword tags")
    source: Optional[str] = Field(default=None, description="Data source identifier")

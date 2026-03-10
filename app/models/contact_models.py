from pydantic import BaseModel


class ContactData(BaseModel):
    name: str = ""
    email: str = ""
    mobile: str = ""
    address: str = ""

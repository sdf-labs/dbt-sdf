from pydantic import BaseModel as _BaseModel

class BaseModel(_BaseModel):
    class Config:
        arbitrary_types_allowed = True
        extra = 'forbid'

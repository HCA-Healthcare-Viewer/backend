from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.src.parsing import parse_hl7_file
import json

router = APIRouter()

@router.get("/get_json")
async def get_json(file_path='source_hl7_messages_v2.hl7'):
    """
    Endpoint to return a JSON response.
    """
    try:
        return parse_hl7_file(file_path)
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Error decoding JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    ...
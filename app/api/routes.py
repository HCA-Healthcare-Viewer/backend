from fastapi import APIRouter, HTTPException, UploadFile, File
from app.src.parsing import parse_hl7_content  # make sure to import the new function

router = APIRouter()

@router.post("/get_json")
async def get_json(file: UploadFile = File(...)):
    """
    Endpoint to return a JSON response after parsing an uploaded HL7 file.
    """
    try:
        file_contents = await file.read()
        file_text = file_contents.decode("utf-8")  # adjust encoding if needed
        parsed_data = parse_hl7_content(file_text)
        return parsed_data

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Error decoding file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

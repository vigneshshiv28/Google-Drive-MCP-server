from typing import Any, Dict, Optional


def success_response(data: Any, message: str = "Operation successful") -> Dict[str, Any]:

    return {
        "status": "success",
        "message": message,
        "data": data
    }

def error_response(message: str, code: int = 500, details: Optional[Any] = None) -> Dict[str, Any]:

    return {
        "status": "error",
        "error": {
            "message": message,
            "code": code,
            "details": details
        }
    }
from fastapi import HTTPException, status


def not_implemented() -> HTTPException:
    """Placeholder for endpoints whose contract exists but whose logic doesn't yet.

    Delete this module once every route is implemented.
    """
    return HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")

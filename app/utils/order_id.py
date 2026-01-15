import secrets
import string

def generate_order_id() -> str:
    """
    Generates a random order ID starting with 'PS-' followed by 8 random uppercase alphanumeric characters.
    Example: PS-DBPJXULF
    """
    prefix = "PS-"
    characters = string.ascii_uppercase + string.digits
    random_chars = ''.join(secrets.choice(characters) for _ in range(8))
    return f"{prefix}{random_chars}"

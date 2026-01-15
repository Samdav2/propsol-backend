import sys
import os
import traceback

try:
    # Insert the application directory into the path
    sys.path.insert(0, os.path.dirname(__file__))

    from a2wsgi import ASGIMiddleware

    # Import the FastAPI app
    from app.main import app

    # Wrap the ASGI app with a2wsgi to make it WSGI compatible
    application = ASGIMiddleware(app)

except Exception as e:
    # Log the error to a file in the current directory
    with open("passenger_startup_error.log", "w") as f:
        f.write(f"Error during startup:\n{str(e)}\n")
        f.write(traceback.format_exc())
    # Re-raise the exception so Passenger knows it failed
    raise e

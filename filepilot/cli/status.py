import typer
import traceback
from ..claude import APIAgent
from . import app

@app.command()
def status():
    """Check Anthropic API connection status."""
    try:
        agent = APIAgent()
        is_available = agent.check_status()
        typer.echo(f"Anthropic API is {'available' if is_available else 'unavailable'}")
    except ValueError as e:
        print("Error checking API status:")
        print(traceback.format_exc())
        raise typer.Exit(1)
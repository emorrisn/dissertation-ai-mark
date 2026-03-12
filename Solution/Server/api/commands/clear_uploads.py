import os
import shutil
import click
from flask.cli import with_appcontext
from api.models import SessionFile, SubmissionPage, MarkScheme
from api.extensions import db

@click.command("clear-uploads")
@with_appcontext
def clear_uploads():
    """Clear all uploads by deleting SessionFile records from the database."""
    
    files = SessionFile.query.all()

    if not files:
        click.echo("No files found in the database. Nothing to clear.")
        return

    click.echo(f"Found {len(files)} files in the database. Deleting and clearing physical storage...")
    
    try:
        # Optional guard: Nullify foreign keys to prevent IntegrityErrors 
        # if your DB strictly enforces foreign key constraints.
        for page in SubmissionPage.query.all():
            page.file_id = None
        for scheme in MarkScheme.query.all():
            scheme.file_id = None
            
        # Iterate over each file so the 'after_delete' event listener is triggered
        for file in files:
            db.session.delete(file)
            
        db.session.commit()
        click.echo("Uploads successfully cleared from the database and filesystem.")
        
    except Exception as e:
        db.session.rollback()
        click.echo(f"Failed to clear uploads. Reason: {e}")
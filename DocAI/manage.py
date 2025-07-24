#!/usr/bin/env python3
"""
Database management script for DocAI.
"""
import click
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_database, create_tables, drop_tables
from app.core.config import get_config
from app.core.logging import setup_logging


@click.group()
def cli():
    """DocAI database management commands."""
    # Set up configuration and logging
    config = get_config()
    setup_logging(config)


@cli.command()
def init():
    """Initialize the database (create all tables)."""
    click.echo("Initializing database...")
    try:
        init_database()
        create_tables()
        click.echo("Database initialized successfully!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--yes', is_flag=True, help='Skip confirmation')
def reset(yes):
    """Reset the database (drop and recreate all tables)."""
    if not yes:
        click.confirm("This will DELETE ALL DATA. Continue?", abort=True)
    
    click.echo("Resetting database...")
    try:
        init_database()
        drop_tables()
        create_tables()
        click.echo("Database reset successfully!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('message')
def migrate(message):
    """Create a new migration."""
    try:
        from alembic import command
        from alembic.config import Config
        
        alembic_cfg = Config("alembic.ini")
        command.revision(alembic_cfg, message=message, autogenerate=True)
        click.echo(f"Migration created: {message}")
    except ImportError:
        click.echo("Alembic not installed. Run: pip install alembic", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def upgrade():
    """Apply database migrations."""
    try:
        from alembic import command
        from alembic.config import Config
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        click.echo("Database upgraded successfully!")
    except ImportError:
        click.echo("Alembic not installed. Run: pip install alembic", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--steps', default=1, help='Number of revisions to downgrade')
def downgrade(steps):
    """Downgrade database migrations."""
    try:
        from alembic import command
        from alembic.config import Config
        
        alembic_cfg = Config("alembic.ini")
        command.downgrade(alembic_cfg, f"-{steps}")
        click.echo(f"Database downgraded {steps} step(s)!")
    except ImportError:
        click.echo("Alembic not installed. Run: pip install alembic", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def seed():
    """Seed the database with sample data."""
    click.echo("Seeding database...")
    try:
        from app.database import DatabaseSession
        from app.database.models import User, Tag
        import hashlib
        import secrets
        
        with DatabaseSession() as session:
            # Create demo user
            demo_user = User(
                email="demo@example.com",
                name="Demo User",
                api_key=hashlib.sha256(b"demo-api-key-12345").hexdigest()[:64],
                roles=["user", "demo"]
            )
            session.add(demo_user)
            
            # Create some tags
            tags = [
                Tag(name="Important", color="#FF0000"),
                Tag(name="Review", color="#FFA500"),
                Tag(name="Processed", color="#00FF00"),
                Tag(name="Archive", color="#808080")
            ]
            for tag in tags:
                session.add(tag)
            
            session.commit()
            click.echo("Database seeded successfully!")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def create_user():
    """Create a new user interactively."""
    email = click.prompt("Email")
    name = click.prompt("Name")
    generate_key = click.confirm("Generate API key?", default=True)
    
    try:
        from app.database import DatabaseSession
        from app.database.models import User
        import hashlib
        import secrets
        from datetime import datetime
        
        with DatabaseSession() as session:
            # Check if user exists
            existing = session.query(User).filter_by(email=email).first()
            if existing:
                click.echo(f"User with email {email} already exists!", err=True)
                return
            
            # Create user
            user = User(
                email=email,
                name=name
            )
            
            if generate_key:
                # Generate secure API key
                api_key = secrets.token_urlsafe(32)
                user.api_key = hashlib.sha256(api_key.encode()).hexdigest()[:64]
                user.api_key_created_at = datetime.utcnow()
                
                click.echo(f"\nAPI Key (save this, it won't be shown again):")
                click.echo(f"  {api_key}")
            
            session.add(user)
            session.commit()
            
            click.echo(f"\nUser created successfully!")
            click.echo(f"  ID: {user.id}")
            click.echo(f"  Email: {user.email}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
#!/usr/bin/env python3
"""
Update dependencies in existing virtual environment.
"""
import subprocess
import sys
import pkg_resources
from pathlib import Path


def get_installed_packages():
    """Get list of installed packages."""
    installed = {}
    for dist in pkg_resources.working_set:
        installed[dist.key] = dist.version
    return installed


def read_requirements(requirements_file):
    """Read requirements from file."""
    requirements = []
    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Parse package name and version
                if '==' in line:
                    name, version = line.split('==')
                    requirements.append((name.strip(), version.strip()))
                else:
                    requirements.append((line.strip(), None))
    return requirements


def check_missing_dependencies(requirements_file='requirements.txt'):
    """Check for missing dependencies."""
    print("Checking dependencies...")
    
    installed = get_installed_packages()
    requirements = read_requirements(requirements_file)
    
    missing = []
    outdated = []
    
    for req_name, req_version in requirements:
        package_key = req_name.lower().replace('-', '_').replace('_', '-')
        
        if package_key not in installed:
            missing.append(req_name if not req_version else f"{req_name}=={req_version}")
        elif req_version and installed[package_key] != req_version:
            outdated.append({
                'name': req_name,
                'installed': installed[package_key],
                'required': req_version
            })
    
    return missing, outdated


def install_missing_packages(packages):
    """Install missing packages."""
    if not packages:
        print("✓ No missing packages to install")
        return True
    
    print(f"\nInstalling {len(packages)} missing packages:")
    for pkg in packages:
        print(f"  - {pkg}")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', *packages
        ])
        print("\n✓ Successfully installed missing packages")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to install packages: {e}")
        return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update dependencies in existing virtual environment"
    )
    parser.add_argument(
        '--upgrade-all',
        action='store_true',
        help='Upgrade all packages to match requirements.txt versions'
    )
    parser.add_argument(
        '--requirements',
        default='requirements.txt',
        help='Path to requirements file (default: requirements.txt)'
    )
    
    args = parser.parse_args()
    
    # Check if in virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✗ Error: Not running in a virtual environment!")
        print("Please activate your virtual environment first:")
        print("    source venv/bin/activate  # On Linux/Mac")
        print("    venv\\Scripts\\activate     # On Windows")
        sys.exit(1)
    
    print(f"✓ Virtual environment: {sys.prefix}")
    
    # Check requirements file exists
    if not Path(args.requirements).exists():
        print(f"✗ Error: Requirements file not found: {args.requirements}")
        sys.exit(1)
    
    # Check for missing and outdated packages
    missing, outdated = check_missing_dependencies(args.requirements)
    
    # Install missing packages
    if missing:
        print(f"\n{len(missing)} missing packages found")
        if not install_missing_packages(missing):
            sys.exit(1)
    
    # Handle outdated packages
    if outdated:
        print(f"\n{len(outdated)} outdated packages found:")
        for pkg in outdated:
            print(f"  - {pkg['name']}: {pkg['installed']} → {pkg['required']}")
        
        if args.upgrade_all:
            print("\nUpgrading outdated packages...")
            packages_to_upgrade = [f"{pkg['name']}=={pkg['required']}" for pkg in outdated]
            if not install_missing_packages(packages_to_upgrade):
                sys.exit(1)
        else:
            print("\nTo upgrade outdated packages, run with --upgrade-all")
    
    print("\n✓ Dependency check complete")
    
    # Additional checks for critical packages
    print("\nVerifying critical packages:")
    critical_packages = [
        'flask', 'sqlalchemy', 'alembic', 'pydantic', 
        'groq', 'langchain', 'faiss-cpu'
    ]
    
    for pkg in critical_packages:
        try:
            __import__(pkg.replace('-', '_'))
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} - Failed to import!")
    
    print("\nDependency update complete!")


if __name__ == '__main__':
    main()
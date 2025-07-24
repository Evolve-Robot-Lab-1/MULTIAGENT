#!/usr/bin/env python3
"""
Update frontend files to use new API endpoints.
"""
import os
import re
import sys
from pathlib import Path


# API endpoint mappings
ENDPOINT_MAPPINGS = {
    # Old endpoint -> New endpoint
    '/api/query_stream': '/api/v1/chat/stream',
    '/api/simple_chat': '/api/v1/chat/completions',
    '/rag/upload': '/api/v1/documents',
    '/rag/remove': '/api/v1/documents',
    '/rag/status': '/api/v1/documents/rag/status',
    '/api/clear_chat': '/api/v1/chat/history',
    '/api/agent-status': '/api/v1/agents/status',
    '/api/start-browser-agent': '/api/v1/agents/browser/start',
    '/convert-to-word': '/api/v1/documents/convert',
    '/edit-document': '/api/v1/documents/edit',
    '/save-document': '/api/v1/documents/save',
    '/download-document': '/api/v1/documents/download',
    '/view_document': '/api/v1/documents/view',
}

# Additional changes needed
ADDITIONAL_CHANGES = [
    # Add authentication headers
    {
        'pattern': r'(fetch\([^,]+,\s*{)',
        'replacement': r'\1\n        headers: { ...getAuthHeaders(), ...(options.headers || {}) },'
    },
    # Update response handling for new format
    {
        'pattern': r'\.then\(response => response\.json\(\)\)',
        'replacement': '.then(response => response.json()).then(data => data.data || data)'
    }
]


def update_file(file_path: Path, dry_run: bool = False):
    """Update a single file with new endpoints."""
    print(f"Processing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # Replace endpoints
    for old_endpoint, new_endpoint in ENDPOINT_MAPPINGS.items():
        if old_endpoint in content:
            content = content.replace(old_endpoint, new_endpoint)
            changes_made.append(f"  - {old_endpoint} -> {new_endpoint}")
    
    # Apply additional regex changes
    for change in ADDITIONAL_CHANGES:
        pattern = re.compile(change['pattern'])
        if pattern.search(content):
            content = pattern.sub(change['replacement'], content)
            changes_made.append(f"  - Applied: {change['pattern']}")
    
    # Add auth headers function if not exists
    if 'getAuthHeaders' not in content and 'fetch(' in content:
        auth_function = '''
// Get authentication headers
function getAuthHeaders() {
    const apiKey = localStorage.getItem('docai_api_key') || 'demo-api-key-12345';
    return {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
    };
}

'''
        # Insert after first function or at beginning
        content = auth_function + content
        changes_made.append("  - Added getAuthHeaders() function")
    
    if changes_made:
        print(f"  Changes made:")
        for change in changes_made:
            print(change)
        
        if not dry_run:
            # Backup original file
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✓ Updated (backup saved as {backup_path.name})")
        else:
            print(f"  [DRY RUN] Would update file")
    else:
        print(f"  No changes needed")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update frontend files to use new API endpoints"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )
    parser.add_argument(
        '--static-dir',
        default='static2.0',
        help='Path to static directory (default: static2.0)'
    )
    
    args = parser.parse_args()
    
    static_dir = Path(args.static_dir)
    if not static_dir.exists():
        print(f"Error: Static directory not found: {static_dir}")
        sys.exit(1)
    
    print(f"Updating frontend files in {static_dir}")
    print(f"Dry run: {args.dry_run}")
    print("-" * 50)
    
    # Find all JS and HTML files
    files_to_update = []
    for pattern in ['*.js', '*.html']:
        files_to_update.extend(static_dir.glob(pattern))
    
    if not files_to_update:
        print("No files found to update")
        return
    
    # Update each file
    for file_path in files_to_update:
        update_file(file_path, dry_run=args.dry_run)
        print()
    
    if args.dry_run:
        print("\n[DRY RUN] No files were actually modified")
        print("Run without --dry-run to apply changes")
    else:
        print("\n✓ Frontend update completed")
        print("\nIMPORTANT: Remember to:")
        print("1. Test all functionality")
        print("2. Configure API keys in localStorage or UI")
        print("3. Update any hardcoded URLs in configuration")


if __name__ == '__main__':
    main()
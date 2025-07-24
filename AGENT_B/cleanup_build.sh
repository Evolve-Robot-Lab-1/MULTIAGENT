#!/bin/bash

echo "==========================================
Cleaning AGENT_B_LINUX_NEW for Production
==========================================
"

# Confirm before proceeding
read -p "This will remove test files, logs, and temporary files. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 1
fi

# Remove test files
echo "Removing test files..."
rm -f test_*.py
rm -f *_test.py
rm -f diagnose.py
rm -f webui_minimal.py
rm -f run_clean.py
rm -f run_simple.py

# Remove the entire tests directory
echo "Removing tests directory..."
rm -rf tests/

# Remove log files
echo "Removing log files..."
rm -f *.log
rm -f nohup.out

# Remove experimental launch scripts
echo "Removing experimental scripts..."
rm -f launch_fixed.sh
rm -f launch_fixed_new.sh
rm -f launch_agent.sh
rm -f run_isolated.sh
rm -f run_headless.sh
rm -f run.sh
rm -f start_app.sh
rm -f test_startup.py

# Remove temporary directories
echo "Removing temporary directories..."
rm -rf tmp/
rm -rf __pycache__/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Remove documentation (optional - uncomment if you want to remove)
# echo "Removing documentation..."
# rm -f CHECKPOINT_WORKING.md
# rm -f FINAL_SOLUTION_SUMMARY.md
# rm -f IMPROVEMENTS.md
# rm -f LINUX_COMPATIBILITY_SUMMARY.md
# rm -f LINUX_SETUP.md
# rm -f SETUP_COMPLETE.md
# rm -f instruction.md

# Keep essential scripts
echo ""
echo "Keeping essential files:"
echo "  - webui.py (main application)"
echo "  - requirements.txt"
echo "  - init_patch.py"
echo "  - launch.sh (recommended launcher)"
echo "  - launch_offline.sh (offline mode launcher)"
echo "  - .env (if exists)"
echo "  - src/ directory"
echo "  - Docker/Vagrant files (if needed)"

# Create a minimal README
cat > README_PRODUCTION.md << 'EOF'
# AGENT_B_LINUX_NEW - Production Build

## Quick Start

```bash
# Launch the application
./launch_offline.sh

# Or with standard launcher
./launch.sh
```

Access at: http://localhost:7788

## Requirements
- Python 3.10+
- Chrome/Chromium browser
- Virtual environment at: ../turboo_linux_new

## Docker
```bash
docker-compose up -d
```

## Stop
```bash
pkill -f webui.py
```
EOF

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Production files remaining:"
ls -la | grep -v "^d" | grep -v "^total"
echo ""
echo "Directories:"
ls -d */
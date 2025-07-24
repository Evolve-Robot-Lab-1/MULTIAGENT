#!/bin/bash
# Run the Operation Tracker GUI

echo "DocAI Native - Operation Tracker"
echo "================================"
echo ""
echo "Choose which version to run:"
echo "1) HTML Version (Browser-based)"
echo "2) PyQt5 Native Application"
echo "3) Both"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "Opening HTML version in browser..."
        # Try different browsers
        if command -v xdg-open > /dev/null; then
            xdg-open "operation_tracker_gui.html"
        elif command -v gnome-open > /dev/null; then
            gnome-open "operation_tracker_gui.html"
        elif command -v firefox > /dev/null; then
            firefox "operation_tracker_gui.html"
        elif command -v google-chrome > /dev/null; then
            google-chrome "operation_tracker_gui.html"
        else
            echo "Could not find a browser. Please open operation_tracker_gui.html manually."
        fi
        ;;
    2)
        echo "Starting PyQt5 application..."
        # Check if PyQt5 is installed
        if python3 -c "import PyQt5" 2>/dev/null; then
            python3 operation_tracker_app.py
        else
            echo "PyQt5 not installed. Installing..."
            pip3 install PyQt5
            python3 operation_tracker_app.py
        fi
        ;;
    3)
        echo "Opening both versions..."
        # Open HTML version
        if command -v xdg-open > /dev/null; then
            xdg-open "operation_tracker_gui.html" &
        fi
        # Start PyQt5 app
        if python3 -c "import PyQt5" 2>/dev/null; then
            python3 operation_tracker_app.py
        else
            echo "PyQt5 not installed. Only opening HTML version."
        fi
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
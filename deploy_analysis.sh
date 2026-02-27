#!/bin/bash

# Define directories
DOCS_DIR=~/Evacuate/docs
PROJECT_DIR=~/Evacuate

# 1. Ensure the destination directory exists
mkdir -p "$DOCS_DIR"

# 2. Copy the PNG and HTML files
echo "Copying analysis files to $DOCS_DIR..."
cp player_breakdown.png evacuation_overall.png evacuation_by_type.png evacuation_results.html "$DOCS_DIR"

# 3. Pushd to the project directory
echo "Navigating to $PROJECT_DIR..."
pushd "$PROJECT_DIR" > /dev/null || { echo "Error: Could not find $PROJECT_DIR"; exit 1; }

# 4. Run mkdocs gh-deploy
echo "Deploying to GitHub Pages..."
mkdocs gh-deploy

# 5. Pop back to the original directory
echo "Returning to original directory..."
popd > /dev/null

echo "Deployment complete!"

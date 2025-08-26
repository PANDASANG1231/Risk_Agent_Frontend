#!/bin/bash

# Create static/js directory
echo "Creating static/js directory..."
mkdir -p static/js

# Create static/css directory
echo "Creating static/css directory..."
mkdir -p static/css

# Copy Plotly.js
echo "Copying Plotly.js..."
if [ -f "node_modules/plotly.js/dist/plotly.js" ]; then
    cp node_modules/plotly.js/dist/plotly.js static/js/
    echo "✓ Plotly.js copied successfully"
else
    echo "✗ Plotly.js not found in node_modules"
fi

# Copy Tailwind CSS
echo "Copying Tailwind CSS..."
if [ -f "node_modules/tailwindcss/dist/tailwind.min.js" ]; then
    cp node_modules/tailwindcss/dist/tailwind.min.js static/js/
    echo "✓ Tailwind CSS copied successfully"
else
    echo "✗ Tailwind CSS not found in node_modules"
fi

# Copy Lucide Icons
echo "Copying Lucide Icons..."
if [ -f "node_modules/lucide/dist/umd/lucide.js" ]; then
    cp node_modules/lucide/dist/umd/lucide.js static/js/
    echo "✓ Lucide Icons copied successfully"
else
    echo "✗ Lucide Icons not found in node_modules"
fi

echo "Setup complete! Check the static/js folder for copied files."
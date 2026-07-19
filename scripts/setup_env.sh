#!/bin/bash

# Setup environment script for Uni-Resource Agent

echo "Setting up Uni-Resource Agent environment..."

# Create virtual environment
echo "Creating virtual environment..."
python -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p data/init_data
mkdir -p data/knowledge/manuals
mkdir -p src/tools
mkdir -p src/models
mkdir -p src/db
mkdir -p src/auth

echo "Environment setup complete!"
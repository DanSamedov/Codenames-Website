#!/bin/sh
set -x

echo "Installing dependencies..."
npm install

echo "Starting Tailwind CLI in watch mode for all pages..."
npm run watch

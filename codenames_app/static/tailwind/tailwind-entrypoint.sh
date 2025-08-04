#!/bin/sh
set -x

echo "Installing dependencies..."
npm install

echo "Starting Tailwind CLI in watch mode..."
npx tailwindcss \
  -i ../css/tailwind.css \
  -o ../css/output.css \
  --watch \
  --poll

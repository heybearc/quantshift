#!/bin/bash

# Convert all admin pages to dark theme by replacing color classes
# This is a comprehensive sed replacement script

for file in app/\(protected\)/admin/*/page.tsx; do
  echo "Converting $file to dark theme..."
  
  # Replace light backgrounds with dark
  sed -i 's/bg-white/bg-slate-800\/50/g' "$file"
  sed -i 's/bg-gray-50/bg-slate-900/g' "$file"
  sed -i 's/bg-gray-100/bg-slate-800/g' "$file"
  sed -i 's/bg-gray-200/bg-slate-700/g' "$file"
  
  # Replace text colors
  sed -i 's/text-gray-900/text-white/g' "$file"
  sed -i 's/text-gray-800/text-slate-100/g' "$file"
  sed -i 's/text-gray-700/text-slate-200/g' "$file"
  sed -i 's/text-gray-600/text-slate-400/g' "$file"
  sed -i 's/text-gray-500/text-slate-400/g' "$file"
  sed -i 's/text-gray-400/text-slate-500/g' "$file"
  
  # Replace borders
  sed -i 's/border-gray-200/border-slate-700/g' "$file"
  sed -i 's/border-gray-300/border-slate-700/g' "$file"
  
  # Replace hover states
  sed -i 's/hover:bg-gray-50/hover:bg-slate-800/g' "$file"
  sed -i 's/hover:bg-gray-100/hover:bg-slate-700/g' "$file"
  
  echo "  ✓ Converted $file"
done

echo "All admin pages converted to dark theme!"

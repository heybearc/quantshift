#!/bin/bash

# Fix all admin pages to use dark theme and remove ProtectedRoute/LayoutWrapper

ADMIN_PAGES=(
  "app/(protected)/admin/api-status/page.tsx"
  "app/(protected)/admin/audit-logs/page.tsx"
  "app/(protected)/admin/health/page.tsx"
  "app/(protected)/admin/invitations/page.tsx"
  "app/(protected)/admin/pending-users/page.tsx"
  "app/(protected)/admin/sessions/page.tsx"
  "app/(protected)/admin/settings/page.tsx"
)

for page in "${ADMIN_PAGES[@]}"; do
  if [ -f "$page" ]; then
    echo "Checking $page..."
    
    # Check if it uses old components
    if grep -q "ProtectedRoute\|LayoutWrapper" "$page"; then
      echo "  ❌ Uses old components - needs manual fix"
    fi
    
    # Check for light theme colors
    if grep -q "bg-white\|bg-gray-50\|bg-gray-100" "$page"; then
      echo "  ❌ Uses light theme colors - needs manual fix"
    fi
    
    # Check for dark theme
    if grep -q "bg-slate-900\|bg-slate-800" "$page"; then
      echo "  ✅ Has dark theme"
    fi
  fi
done

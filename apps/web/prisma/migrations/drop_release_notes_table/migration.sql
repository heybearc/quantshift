-- Drop release_notes table to align with control plane policy
-- Release notes are now managed via markdown files only (like TheoShift)

DROP TABLE IF EXISTS "release_notes";

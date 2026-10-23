# Repair and verification — 23 October 2026

Build now regenerates browser text-game sources before Pages/Vercel publication. Production-only link handling explains unpublished local files instead of sending users to 404s. Local file and localhost dashboards retain ordinary folder access. No private folders are added to hosting. Validation: 7 Python tests, 2 Node path tests, JavaScript syntax check and browser asset generation passed. Legacy dashboard-data link audit still identifies private local paths; these intentionally remain unpublished.

Live browser verification is recorded separately after deployment; a successful build alone is not gameplay evidence.

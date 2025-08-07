from supabase import create_client

SUPABASE_URL = "https://xmzxfkgwaxjmyyqistjs.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhtenhma2d3YXhqbXl5cWlzdGpzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjU4MzI2MSwiZXhwIjoyMDY4MTU5MjYxfQ.-496DfQjI6cNpDeuTnXwgIivCPHwMfHOgJWfcjj4x7Y"  # Get this from Supabase > Settings > API

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

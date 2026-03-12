Write-Host "Starting database reset..."

Write-Host "Step 1: Clearing database with 'flask fresh'"
flask fresh

Write-Host "Step 2: Removing old migrations directory"
Remove-Item -Path "migrations" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Step 3: Initializing migrations with 'flask db init'"
flask db init

Write-Host "Step 4: Creating initial migration with 'flask db migrate'"
flask db migrate -m "initial"

Write-Host "Step 5: Applying migrations with 'flask db upgrade'"
flask db upgrade

Write-Host "Step 6: Seeding database with 'flask seed'"
flask seed

Write-Host "Database reset completed successfully."
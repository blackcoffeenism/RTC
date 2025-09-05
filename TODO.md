# TODO: Implement User-Specific Data Access

## Tasks
- [x] Update schema.sql to add user_id column to tables (rooms, menu_photo, menu_list, events)
- [x] Update RLS policies in schema.sql to restrict access to user's own data
- [x] Modify main.py to extract user_id from access token
- [x] Update API endpoints in main.py to filter queries by user_id
- [x] Update API endpoints in main.py to include user_id when inserting data
- [x] Test the changes with multiple users to ensure data isolation (User will test)

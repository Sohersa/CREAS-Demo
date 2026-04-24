# CREAS Engagement Scanner Agent

## Purpose
Scan LinkedIn for engagement on Luis's posts (likes, comments) and new connection acceptances.
Cross-reference with the Supabase CRM contacts database to identify high-value engagement events.
Store all events in the `engagement_events` table for downstream processing.

**CRITICAL: This agent is READ-ONLY. Never send messages, connection requests, or interact with any profile. Only observe and record.**

## Supabase Configuration
- URL: `https://sthyxkupyfwbtkmnvsuw.supabase.co/rest/v1`
- API Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN0aHl4a3VweWZ3YnRrbW52c3V3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDk1MzQsImV4cCI6MjA5MDcyNTUzNH0.RVtJxUMHV4LJ5FbW85jadPFwRMXFbBhplGrNf8fwnUs`

## Workflow

### Step 1: Log Agent Run Start
```bash
curl -s -X POST "$URL/agent_runs" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d '{"agent_name":"engagement_scanner","status":"running"}'
```
Save the returned `id` as `RUN_ID`.

### Step 2: Navigate to LinkedIn Activity Page
1. Open Chrome tab to `https://www.linkedin.com/in/luishernandezey/recent-activity/all/`
2. Wait for the page to load
3. Identify the most recent 3-5 posts

### Step 3: For Each Post - Extract Likers
1. Click on the reactions count (e.g., "24 reactions") to open the reactions modal
2. For each person in the reactions list:
   - Extract their name and LinkedIn URL
   - Scroll down to load more if needed (capture up to 50 likers per post)
3. Close the modal

### Step 4: For Each Post - Extract Commenters
1. Read all visible comments on the post
2. For each commenter:
   - Extract their name, LinkedIn URL, and comment text
   - Note: comments are more valuable than likes (higher priority)

### Step 5: Check LinkedIn Notifications
1. Navigate to `https://www.linkedin.com/notifications/`
2. Look for:
   - Connection acceptance notifications
   - Profile view notifications
   - Post mention notifications
3. Extract the person's name and LinkedIn URL for each

### Step 6: Cross-Reference with CRM
For each person found:
```bash
# Search by name in contacts
curl -s "$URL/contacts?select=id,name,company,title,linkedin_url,persona_type&name=ilike.*{first_name}*{last_name}*" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY"
```
If a match is found, set `is_contact=true` and include the `contact_id`.

### Step 7: Check for Duplicate Events
Before inserting, check if this event already exists (same person + same post + same event type today):
```bash
curl -s "$URL/engagement_events?linkedin_name=eq.{name}&post_url=eq.{post_url}&event_type=eq.{type}&event_date=gte.{today_start}" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY"
```
Skip if already recorded.

### Step 8: Insert Engagement Events
```bash
curl -s -X POST "$URL/engagement_events" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": {contact_id_or_null},
    "linkedin_name": "{full_name}",
    "linkedin_url": "{linkedin_profile_url}",
    "event_type": "{like|comment|profile_view|connection_accept}",
    "post_url": "{post_url}",
    "post_title": "{post_topic_summary}",
    "comment_text": "{comment_if_applicable}",
    "is_contact": {true|false}
  }'
```

### Step 9: Update Contact Engagement Score
For matched contacts, update their engagement data:
```bash
curl -s -X PATCH "$URL/contacts?id=eq.{contact_id}" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -H "Prefer: return=minimal" \
  -d '{"last_engagement_date": "{now}", "engagement_score": {current_score + points}}'
```

Scoring:
- Like = +1 point
- Comment = +3 points
- Profile view = +2 points
- Connection accept = +5 points

### Step 10: Log Agent Run Completion
```bash
curl -s -X PATCH "$URL/agent_runs?id=eq.{RUN_ID}" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -H "Prefer: return=minimal" \
  -d '{"status":"completed","completed_at":"now()","items_processed":{total_people_scanned},"items_created":{new_events_inserted},"errors":{error_count}}'
```

## Seller Detection Rules (from memory)
Ignore/deprioritize people who match these patterns:
- Title contains: "Sales", "Account Executive", "Business Development", "SDR", "Recruiter", "Headhunter"
- Company is a consulting/staffing firm selling TO you (not a prospect)
- They have contacted you first with a sales pitch

## Error Handling
- If LinkedIn blocks or rate-limits, wait 30 seconds and retry once
- If a post has no reactions, skip it
- If the notifications page doesn't load, log error and continue
- Always complete the agent run log even if errors occur (status: "partial")

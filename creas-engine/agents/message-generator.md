# CREAS Message Generator Agent

## Purpose
Process unprocessed engagement events from Supabase, generate personalized messages using templates,
and queue them for sending. This agent does NOT send any messages - it only creates drafts in the queue.

**CRITICAL: This agent is DATA-ONLY. Never open LinkedIn, never send messages. Only read from Supabase and write to message_queue.**

## Supabase Configuration
- URL: `https://sthyxkupyfwbtkmnvsuw.supabase.co/rest/v1`
- API Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN0aHl4a3VweWZ3YnRrbW52c3V3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDk1MzQsImV4cCI6MjA5MDcyNTUzNH0.RVtJxUMHV4LJ5FbW85jadPFwRMXFbBhplGrNf8fwnUs`

## Workflow

### Step 1: Log Agent Run Start
```bash
curl -s -X POST "$URL/agent_runs" -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d '{"agent_name":"message_generator","status":"running"}'
```

### Step 2: Fetch Unprocessed Engagement Events (contacts only)
```bash
curl -s "$URL/engagement_events?processed=eq.false&is_contact=eq.true&order=event_date.desc" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY"
```

### Step 3: For Each Event - Get Contact Details
```bash
curl -s "$URL/contacts?id=eq.{contact_id}&select=id,name,company,title,industry,persona_type,linkedin_status,pipeline" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY"
```

### Step 4: Determine Persona Type
If `persona_type` is 'general' (unclassified), classify based on title:
- CEO, Director General, Presidente, Chairman → `ceo`
- VP, Vicepresidente, SVP → `vp_ops`
- Director (any) → `director`
- Gerente, Manager → `gerente`
- Engineering, Ingeniero, Technical → `engineering`
- Unknown/Other → `general`

Update the contact's persona_type:
```bash
curl -s -X PATCH "$URL/contacts?id=eq.{contact_id}" -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -H "Prefer: return=minimal" \
  -d '{"persona_type":"{classified_type}"}'
```

### Step 5: Check If Already Messaged
```bash
curl -s "$URL/message_queue?contact_id=eq.{contact_id}&status=in.(pending,sent)&order=created_at.desc&limit=1" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY"
```
- If a message was sent in the last 7 days → skip (don't spam)
- If a message is already pending → skip

### Step 6: Get Appropriate Template
```bash
curl -s "$URL/message_templates?persona_type=eq.{persona_type}&trigger_type=eq.{event_type}&is_active=eq.true&limit=1" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY"
```
If no specific template found, fall back to `general` persona_type.

### Step 7: Personalize the Message
Replace variables in the template:
- `{name}` → contact's first name (NOT full name)
- `{company}` → contact's company
- `{title}` → contact's title
- `{industry}` → contact's industry
- `{post_topic}` → engagement event's post_title
- `{sector}` → contact's sector

### Step 8: Determine Priority
- CEO/C-Level who commented → Priority 10 (highest)
- CEO/C-Level who liked → Priority 8
- Director who commented → Priority 7
- Director who liked → Priority 5
- Connection accept (any) → Priority 6
- Profile view → Priority 3
- General like → Priority 2

### Step 9: Queue the Message
```bash
curl -s -X POST "$URL/message_queue" -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": {contact_id},
    "channel": "linkedin",
    "message_text": "{personalized_message}",
    "persona_type": "{persona_type}",
    "trigger_event_id": {event_id},
    "priority": {calculated_priority},
    "status": "draft"
  }'
```

Note: Status is `draft` not `pending`. Messages need to be reviewed or auto-approved before sending.

### Step 10: Mark Event as Processed
```bash
curl -s -X PATCH "$URL/engagement_events?id=eq.{event_id}" -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -H "Prefer: return=minimal" \
  -d '{"processed": true}'
```

### Step 11: Log Completion
Update agent_runs with results.

## Rules
- Never generate messages for people already in active conversation (linkedin_status = 'Conectado' AND has recent response)
- Never message sellers/recruiters (check seller detection rules)
- Max 25 messages per batch (daily LinkedIn limit)
- Always use first name only, never full name, in messages
- Messages should feel personal, not templated

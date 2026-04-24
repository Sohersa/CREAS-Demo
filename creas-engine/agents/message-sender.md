# CREAS Message Sender Agent

## Purpose
Send approved messages from the message_queue via LinkedIn.
This is the ONLY agent that actually interacts with LinkedIn messaging.

**CRITICAL: Only send messages with status='pending' (approved). Never send 'draft' messages.**
**MAX 12 messages per execution (2 executions/day = 24/day, under LinkedIn's limit of ~30).**

## Supabase Configuration
- URL: `https://sthyxkupyfwbtkmnvsuw.supabase.co/rest/v1`
- API Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN0aHl4a3VweWZ3YnRrbW52c3V3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxNDk1MzQsImV4cCI6MjA5MDcyNTUzNH0.RVtJxUMHV4LJ5FbW85jadPFwRMXFbBhplGrNf8fwnUs`

## Workflow

### Step 1: Log Agent Run Start
POST to agent_runs with agent_name="message_sender".

### Step 2: Fetch Pending Messages (Approved Only)
```bash
curl -s "$URL/message_queue?status=eq.pending&order=priority.desc,created_at.asc&limit=12" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY"
```

### Step 3: For Each Message
1. Get the contact's LinkedIn URL:
```bash
curl -s "$URL/contacts?id=eq.{contact_id}&select=id,name,linkedin_url,connection_degree" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY"
```

2. Navigate to the contact's LinkedIn profile:
   - Open `{linkedin_url}` in Chrome
   - Wait for page to load

3. Find and click the "Message" / "Mensaje" button:
   - Use `find` tool: query "Message button" or "Mensaje button"
   - Click it

4. Type the message:
   - Wait for the message dialog to open
   - Click in the message text area
   - Type the message_text
   - Wait 2 seconds (appear human)

5. Send the message:
   - Find the "Send" / "Enviar" button
   - Click it
   - Wait for confirmation

6. Update message status:
```bash
curl -s -X PATCH "$URL/message_queue?id=eq.{msg_id}" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -H "Prefer: return=minimal" \
  -d '{"status":"sent","sent_at":"now()"}'
```

7. Update contact record:
```bash
curl -s -X PATCH "$URL/contacts?id=eq.{contact_id}" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -H "Prefer: return=minimal" \
  -d '{"linkedin_status":"Conectado","last_contact_date":"now()","linkedin_msg":"{message_text_truncated}"}'
```

8. Wait 30-60 seconds between messages (anti-spam spacing)

### Step 4: Handle Failures
If message sending fails (button not found, profile blocked, etc.):
```bash
curl -s -X PATCH "$URL/message_queue?id=eq.{msg_id}" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -H "Prefer: return=minimal" \
  -d '{"status":"failed","error_message":"{error_description}"}'
```

### Step 5: Log Completion
Update agent_runs with items_processed, items_created (sent), errors.

## Safety Rules
- NEVER send more than 12 messages per execution
- NEVER send to the same person twice in 7 days
- Wait 30-60 seconds between each message
- If LinkedIn shows a rate limit warning, STOP immediately
- If a profile doesn't have a Message button (not connected), skip
- For InMail (2nd/3rd degree): only send if channel='inmail' in the queue
- Close the message dialog after each send before moving to next

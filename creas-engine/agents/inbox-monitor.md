# CREAS Inbox Monitor Agent

## Purpose
Monitor LinkedIn inbox for new responses to sent messages.
Classify responses and update the CRM pipeline accordingly.
Generate follow-up messages for non-responders.

**CRITICAL: This agent is READ-ONLY on LinkedIn. It reads messages but does NOT reply.
Follow-ups are queued in message_queue for the Message Sender agent.**

## Supabase Configuration
- URL: `https://sthyxkupyfwbtkmnvsuw.supabase.co/rest/v1`
- API Key: (same as other agents)

## Workflow

### Step 1: Log Agent Run Start
POST to agent_runs with agent_name="inbox_monitor".

### Step 2: Open LinkedIn Messaging
1. Navigate to `https://www.linkedin.com/messaging/`
2. Wait for inbox to load
3. Scan the conversation list for unread messages (bold text / blue dot)

### Step 3: For Each Unread Conversation
1. Click on the conversation to open it
2. Read the latest message(s)
3. Extract:
   - Sender name
   - Sender LinkedIn URL (from profile link in conversation)
   - Message content
   - Timestamp

### Step 4: Match to CRM Contact
```bash
curl -s "$URL/contacts?select=id,name,company,title,pipeline,persona_type&linkedin_url=ilike.*{linkedin_slug}*" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY"
```

### Step 5: Classify the Response
Analyze the message content and classify:

**POSITIVE** (pipeline → "Meeting Scheduled" or "Interested"):
- Agrees to meet / call
- Asks for more information
- Shows genuine interest
- Provides contact info (email, phone)
- Examples: "Si, platiquemos", "Me interesa", "Manda horarios", "Agendamos"

**QUESTION** (pipeline → "Engaged"):
- Asks about services, pricing, or capabilities
- Wants to know more before committing
- Examples: "Que tipo de proyectos?", "Cuanto cuesta?", "Tienen casos en mi industria?"

**NEGATIVE** (pipeline → "Not Interested"):
- Politely declines
- Says not the right time
- Not the right person
- Examples: "No gracias", "No es mi area", "Contacta a..."

**SELLER** (ignore):
- They're selling something TO you
- Recruiter pitch
- Generic sales message
- See seller detection criteria in memory

### Step 6: Update CRM
For positive/question responses:
```bash
curl -s -X PATCH "$URL/contacts?id=eq.{contact_id}" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -H "Prefer: return=minimal" \
  -d '{
    "pipeline": "{new_pipeline_stage}",
    "linkedin_response": "{message_summary}",
    "last_contact_date": "now()",
    "engagement_score": {current + 10}
  }'
```

### Step 7: Generate Follow-Ups for Non-Responders
Check for contacts who were messaged 3+ days ago with no response:
```bash
curl -s "$URL/message_queue?status=eq.sent&sent_at=lt.{3_days_ago}&select=id,contact_id,persona_type,follow_up_number" \
  -H "apikey: $KEY" -H "Authorization: Bearer $KEY"
```

For each non-responder (max follow_up_number = 2):
1. Check if they responded (search inbox or check linkedin_response field)
2. If no response, get follow_up template
3. Queue follow-up message with status='draft', follow_up_number + 1

### Step 8: Log Completion
Update agent_runs.

## Seller Detection Criteria
From user memory - ignore people whose messages match:
- Offering services (software, consulting, staffing)
- "Te podemos ayudar con..."
- "Tengo una solucion para..."
- Generic pitch templates
- Recruiter messages about job opportunities

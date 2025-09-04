# Songwriting API

Routes for AI-assisted songwriting collaboration.

## POST /songwriting/prompt
Generate an initial draft from a title, genre and exactly three themes.

## GET /songwriting/drafts/{draft_id}
Retrieve a draft created by the current user.

## PUT /songwriting/drafts/{draft_id}
Update a draft's lyrics, chords, themes, chord progression or album art.  Accessible to the creator and any co-writers.

## GET /songwriting/drafts/{draft_id}/versions
List saved versions of a draft.  Accessible to the creator and co-writers.

## GET /songwriting/drafts/{draft_id}/co_writers
Return the list of co-writer user IDs for a draft.  Only the creator and existing co-writers may view this list.

## POST /songwriting/drafts/{draft_id}/co_writers
Add a co-writer to a draft.  The user making the request must share a band with the new co-writer.  Returns the updated co-writer list.


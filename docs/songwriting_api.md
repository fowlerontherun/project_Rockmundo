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



## POST /songwriting/drafts/{draft_id}/complete
Finish the songwriting phase. The response contains a 1-100 song quality score,
a writing-time breakdown, and a one-time random polish success chance. The first
completion also sends a `songwriting_complete` inbox notification to the creator
and accepted co-writers.

## POST /songwriting/drafts/{draft_id}/polish
Run the single optional post-completion writing session. The session always adds
60 minutes to the writing-time breakdown. It can improve quality by 2-8 points
when the previously displayed random chance succeeds; failure never reduces
quality. A `songwriting_polish` inbox notification records the outcome.


## POST /songwriting/drafts/{draft_id}/skip-polish
Decline the optional final polish session and lock in the current songwriting
quality without adding any extra writing time. This lets the player make an
explicit choice between attempting polish and keeping the completed song as-is.

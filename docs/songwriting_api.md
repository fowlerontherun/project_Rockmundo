# Songwriting API

Routes for AI-assisted songwriting collaboration.

## POST /songwriting/prompt
Generate an initial draft from a title, genre and exactly three themes.

## GET /songwriting/drafts/{draft_id}
Retrieve a draft when the current user is its creator or an accepted co-writer.

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
completion also creates a private in-game inbox thread for the creator and each
accepted co-writer. Mail delivery raises the normal unread-mail notification; if
mail storage is unavailable, the system falls back to a
`songwriting_complete` notification so the result is not silently lost.

## POST /songwriting/drafts/{draft_id}/polish
Run the single optional post-completion writing session. The session always adds
60 minutes to the writing-time breakdown. It can improve quality by 2-8 points
when the previously displayed random chance succeeds; failure never reduces
quality. The outcome is delivered as another private inbox item.


## POST /songwriting/drafts/{draft_id}/skip-polish
Decline the optional final polish session and lock in the current songwriting
quality without adding any extra writing time. This lets the player make an
explicit choice between attempting polish and keeping the completed song as-is.

## POST /songwriting/drafts/{draft_id}/finalize
Create the canonical catalogue song from a completed draft after the polish choice
has been resolved. Requires `band_id`, `duration_sec`, and optional
`distribution_channels`. Only the draft creator can finalize, and they must be
a member of the target band.

Finalization persists the completed lyrics, chord progression, themes, quality
score, writing-time breakdown, and polish result in
`songwriting_song_metadata`. It is idempotent by draft ID: retrying returns the
existing song rather than creating a duplicate or sending another
`songwriting_finalized` inbox item.


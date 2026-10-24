# 002. Cutting time-to-first-token from 7.9 s to 3.0 s

**Status:** shipped. Measured before and after on the running system.

## Problem

Time-to-first-token (TTFB) for a chat request was 7.88 s. Users stared at a blank screen before anything appeared.

## What changed

TTFB dropped to 2.97 s, about 62% lower, through three changes:

1. **Heavy pre-model work moved behind the first streamed event.** Request validation, session checks, and context preparation used to run before the response started. They now run after the first status event is sent, so the client gets feedback immediately and the work overlaps with the connection already being open.
2. **Message persistence moved to the background.** Saving the user's message no longer blocks the response.
3. **The database moved from US East to Frankfurt**, closer to the API server. Round trips to the database are frequent, so distance mattered more than expected.

## A bug found along the way

While migrating the database, the connection string handling turned out to be wrong: a regex that stripped an SSL option corrupted the URL whenever another query parameter followed it. It was replaced with a proper URL parser. The old code had worked by accident because of parameter order.

## Lessons

- **Perceived latency and real latency are different problems.** Sending a status event first improved what the user experiences even where total work was unchanged.
- **Measure first.** The biggest wins came from moving and reordering work, not from optimizing any single function.
- **Infrastructure placement is a performance feature.**

## Not done yet

Several validation steps (request, attachment, session, lock acquisition) cost roughly 0.1 s each in one measurement taken before the database move. They have not been re-measured since, and they are candidates for running concurrently.

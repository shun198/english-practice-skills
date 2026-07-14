## English Summary

### Topic We Discussed
- **Synchronous vs. Asynchronous Requests**:  
  - Synchronous: Ensures tasks are executed in a strict order, ideal for predictable sequences or when one step depends on another’s immediate result.
  - Asynchronous: Ideal for independent tasks or when waiting on I/O, allowing other tasks to run while one is pending.

- **Await**: Pauses the function until the awaited operation completes, ensuring orderly flow in async code.

- **Concurrency**: Managing multiple tasks at once; it’s about juggling them efficiently, whether via async or threads.

- **I/O Bottlenecks**: Delays caused by waiting on external input/output—async helps by letting other tasks proceed while waiting.

### Key Questions We Explored
- When would you prefer synchronous for predictable sequences?
- How does “await” help control flow in FastAPI?

### Feedback on English
- Instead of “requesting asynchronously,” say “making an asynchronous request.”
- When searching for a word, say “I’m trying to remember the English term.”

### Useful Phrases for Next Time
- “Let’s break this down step by step.”
- “Could we clarify how these requests depend on one another?”
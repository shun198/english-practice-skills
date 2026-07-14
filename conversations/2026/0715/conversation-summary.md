## English Summary

### Topics We Covered

#### Synchronous vs. Asynchronous Requests
- A **synchronous request** waits for an operation to complete before continuing.
- An **asynchronous request** allows the application to work on other tasks while waiting for an I/O operation, such as:
  - calling an external API,
  - reading from a database,
  - uploading a file to Amazon S3,
  - or reading a file from disk.
- Synchronous processing is useful when the next step immediately depends on the previous result.
- Asynchronous processing is useful when the application spends significant time waiting on external systems.

#### Important Clarification
- Synchronous processing does **not** mean that one user's request must wait for every other user's request.
- A web server can handle multiple synchronous requests concurrently by using multiple workers or threads.
- The main difference is whether an individual execution flow blocks while waiting for an operation to finish.

#### Advantages of Synchronous Processing
- Easier to understand, debug, and test.
- Execution order is predictable.
- Appropriate when each step depends on the previous step.
- Often a good choice for short, simple operations.

#### Disadvantages of Synchronous Processing
- A worker may remain blocked while waiting for a database, file system, or external API.
- It may handle I/O-heavy workloads less efficiently.
- Long-running operations can increase response time.

#### Advantages of Asynchronous Processing
- A worker can handle other tasks while waiting for I/O.
- It can improve throughput for I/O-bound workloads.
- It is useful for applications that make many external API calls or database queries.
- It can reduce the number of workers required for high-concurrency workloads.

#### Disadvantages of Asynchronous Processing
- The code can be harder to understand and debug.
- Every library used in the asynchronous path should support async operations.
- Error handling, cancellation, timeouts, and resource management require careful design.
- Async does not automatically make CPU-intensive processing faster.

#### `async` and `await`
- `async def` defines a coroutine function in Python.
- `await` pauses the current coroutine until an asynchronous operation completes.
- While that coroutine is waiting, the event loop can run other tasks.
- `await` does not block the entire server, but the current coroutine still waits for the result.
- Using many `await` expressions is not necessarily a problem. The important question is whether independent operations are being awaited sequentially when they could run concurrently.

#### Concurrency
- **Concurrency** means that multiple tasks make progress during the same period.
- Async I/O is one way to achieve concurrency.
- Threads and processes are other approaches.
- Concurrency does not always mean that tasks execute at the exact same instant.

#### I/O Bottlenecks
- I/O means **input/output**.
- Common I/O operations include database access, network requests, file access, and cloud storage operations.
- I/O is often much slower than CPU operations.
- In synchronous code, a worker may remain idle while waiting for I/O.
- In asynchronous code, the event loop can work on another task during that waiting period.

#### Dependencies Between Asynchronous Tasks
- Asynchronous tasks can still depend on one another.
- When task B needs the result of task A, task B can `await` task A.
- Independent tasks can be started concurrently with `asyncio.gather()`.
- If one operation fails, the application should define:
  - whether the remaining tasks should be cancelled,
  - whether partial results are acceptable,
  - whether retries are allowed,
  - and how failures should be reported.

### Key Questions I Asked
- What is the difference between synchronous and asynchronous requests?
- When should I use a synchronous API rather than an asynchronous API?
- How do `async` and `await` work in FastAPI?
- What is a context manager?
- What is concurrency?
- Can I/O become a performance bottleneck?
- What happens when one asynchronous operation fails?
- Should dependent requests always be synchronous?
- What other concepts should I consider when designing async code?

### Python / FastAPI Example

```python
import asyncio
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.get("/sync-example")
def sync_example() -> dict[str, str]:
    # This is a regular synchronous endpoint.
    # FastAPI runs normal `def` endpoints in a thread pool.
    return {"message": "This endpoint is synchronous."}


async def fetch_user(client: httpx.AsyncClient, user_id: int) -> dict[str, Any]:
    response = await client.get(
        f"https://jsonplaceholder.typicode.com/users/{user_id}",
        timeout=5.0,
    )
    response.raise_for_status()
    return response.json()


async def fetch_posts(client: httpx.AsyncClient, user_id: int) -> list[dict[str, Any]]:
    response = await client.get(
        "https://jsonplaceholder.typicode.com/posts",
        params={"userId": user_id},
        timeout=5.0,
    )
    response.raise_for_status()
    return response.json()


@app.get("/users/{user_id}/profile")
async def get_user_profile(user_id: int) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            # These operations are independent, so they can run concurrently.
            user, posts = await asyncio.gather(
                fetch_user(client, user_id),
                fetch_posts(client, user_id),
            )

        return {
            "user": user,
            "posts": posts,
        }

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="The external API returned an error.",
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="The external API could not be reached.",
        ) from exc
```

### What This Example Demonstrates
- `async def` defines an asynchronous FastAPI endpoint.
- `async with` is an asynchronous context manager.
- `await` waits for an async operation without blocking the event loop.
- `asyncio.gather()` runs independent operations concurrently.
- Timeouts and exceptions are handled explicitly.
- The endpoint is most suitable for I/O-bound work, not CPU-heavy calculations.

### Specific Feedback On My English
- Use **“making an asynchronous request”** instead of **“requesting asynchronous requests.”**
- Use **“at random times”** instead of **“in a random timing.”**
- Use **“I haven’t thought about this scenario before”** instead of **“I haven’t even thought about this scenario.”**
- Use **“Are there any other concepts I should consider?”** instead of **“Is there any other things I have to consider?”**
- Use **“I haven’t considered I/O yet”** instead of **“I haven’t considered about I/Os.”**
- Use **“a performance bottleneck”** instead of **“a bottleneck for performances.”**
- Use **“the rest of the requests”** instead of **“rest of the requests.”**
- Use **“tasks that depend on other operations”** instead of **“tests that have to be dependent on other requests.”**

### Technical Clarity Feedback
- The explanation initially mixed up:
  - synchronous execution,
  - concurrency between users,
  - and request ordering.
- A clearer explanation would be:

> “A synchronous operation blocks its current execution flow until the result is available. An asynchronous operation allows the event loop to handle other tasks while waiting for I/O.”

- Dependent tasks do not always have to be implemented synchronously. They can still be asynchronous and executed in order by using `await`.
- Async is most effective for I/O-bound workloads. CPU-bound workloads usually require threads, processes, workers, or a task queue.

### Example Questions Or Phrases For Future Use
- “Could you walk me through the trade-offs between synchronous and asynchronous processing?”
- “Would this endpoint benefit from async I/O, or would synchronous code be simpler?”
- “These two operations are independent, so could we run them concurrently?”
- “This step depends on the previous result, so we need to await it before continuing.”
- “How should we handle cancellation if one of the concurrent operations fails?”
- “Do all the libraries in this code path support asynchronous I/O?”
- “Could this external API call become an I/O bottleneck?”
- “Would a timeout or retry policy be appropriate here?”
- “Let me confirm my understanding: async improves concurrency during I/O waits, but it does not make CPU-bound code faster. Is that correct?”

### Suggested Next Topic
- Multithreading vs. asynchronous programming
- Concurrency vs. parallelism
- When to use threads, processes, async I/O, or background job queues
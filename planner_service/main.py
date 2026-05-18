import asyncio
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def main():
    with tracer.start_as_current_span("planner_startup"):
        print("Planner Service: Cognition Engine Initialized.")
        print("Connected to NATS event bus. Awaiting Temporal workflows...")
        # TODO: Implement Temporal worker for LLM tasks

if __name__ == "__main__":
    asyncio.run(main())

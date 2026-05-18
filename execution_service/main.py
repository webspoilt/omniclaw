import asyncio
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def main():
    with tracer.start_as_current_span("execution_startup"):
        print("Execution Service: Sandboxed Runtime Initialized.")
        print("Connecting to Temporal for task assignments...")
        # TODO: Implement Temporal worker for tool execution (Playwright, etc.)

if __name__ == "__main__":
    asyncio.run(main())

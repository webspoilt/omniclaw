import asyncio

async def main():
    print("Kernel Observer: eBPF LLM Guard Initialized.")
    # TODO: Load eBPF C program to block prompt injections at syscall level
if __name__ == "__main__":
    asyncio.run(main())

import asyncio

thing = asyncio.Event()


async def test():
    await asyncio.sleep(3)
    thing.set()
    

async def main():
    t = asyncio.create_task(test())
    d = asyncio.create_task(asyncio.sleep(2))
    done, pending = await asyncio.wait([d, asyncio.create_task(thing.wait())], return_when=asyncio.FIRST_COMPLETED)
    
    print(thing.is_set())


asyncio.run(main(), debug=True)
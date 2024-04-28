from __future__ import annotations
import asyncio
import random
import os
import json
import aiomysql
from collections import deque
import pathlib
import numpy as np
import math
from aiohttp import web

_BINGO_QUEUE_SIZE:int = 7
_BINGO_CALL_INTERVAL:float = 4.0
_BINGO_MAX_NUM:int = 100
_SOCK_PATH = pathlib.Path(__file__).parent.resolve() / 'bingo.sock'

class BingoServer():
    def __init__(self):
        pass

    async def start_serving(self):
        self.api = self.__api()
        await self.api.start_serving()

        self.bingo_roll = asyncio.create_task(self.__bingo_roll())

        print("done")

    async def __bingo_roll(self):
        for call in random.sample(range(_BINGO_MAX_NUM), _BINGO_MAX_NUM):
            next_call = asyncio.create_task(asyncio.sleep(_BINGO_CALL_INTERVAL))
            await self.api.bingo_call(call)
            await next_call

    class __api():
        def __init__(self):
            self._next_bingo = 0
            self._call_log: deque = deque(maxlen=_BINGO_QUEUE_SIZE)

        async def __sse_handler_wrapper(self, request: web.Request):
            return ( await self.__sse_handler(self._call_log)(request) )

        async def start_serving(self):
            self._db_pool = await aiomysql.create_pool(host="localhost", port=3306, user="cheese", password="sudo", db="bingo", autocommit=True)
            async with self._db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(  """TRUNCATE TABLE space;
                                            TRUNCATE TABLE card;""")
            print("db prepped")

            pathlib.Path.unlink(_SOCK_PATH, True)
            api = await asyncio.start_unix_server(self._handler, _SOCK_PATH)
            await api.start_serving()
            _SOCK_PATH.chmod(0o777)

            sse_srv = web.Application()
            sse_srv.add_routes([web.get('/', self.__sse_handler_wrapper)])
            sse_srv_runner = web.AppRunner(sse_srv, handler_cancellation=True)
            await sse_srv_runner.setup()
            sse_site = web.TCPSite(sse_srv_runner)
            await sse_site.start()

        async def _handler(self, r: asyncio.StreamReader, w: asyncio.StreamWriter):
            query = (await r.read(200)).decode()
            print(query)
            for evt, data in json.loads(query).items():
                try:
                    task = asyncio.create_task(self.__evt_handler._evt_handlers[evt](self, data))
                    w.write(json.dumps(await task).encode())
                except Exception as e:
                    print(e)
            w.write_eof()

        class __sse_handler():
            _client_pool: set[web.StreamResponse] = set()

            def __init__(self, call_log: deque):
                self._call_log = call_log

            async def __call__(self, request: web.Request):
                resp = web.StreamResponse(headers={'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache'})
                await resp.prepare(request)
                self._client_pool.add(resp)
                try:
                    print("cum")
                    await resp.write(f"event: catchup\ndata: {json.dumps({'calls': list(self._call_log)})}\n\n".encode())
                    await asyncio.Future()
                except Exception as e:
                    self._client_pool.remove(resp)
                    print("dick")
                    print(e)
                    return resp
            
            @classmethod
            async def sse_event(cls, evt: str, data: dict):
                sse_client: web.StreamResponse
                for sse_client in cls._client_pool:
                    try:
                        await sse_client.write(f"event: {evt}\ndata: {json.dumps(data)}\n\n".encode())
                    except:
                        pass

        class __evt_handler():
            _evt_handlers = dict() 
            def __init__(self, f):
                self._evt_handlers.setdefault(f.__name__, f)

        async def bingo_call(self, call: int):
            self._call_log.appendleft(call)
            await self.__sse_handler.sse_event("call", {"call": call})

        @__evt_handler
        async def bingo(self, arg: dict):
            #going in the bingo bingo requet
            async with self._db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(    """SELECT card.id
                                        FROM card
                                        WHERE card.user_id = %s""", (arg['user_id'], ) )

                    for card_id in [card['id'] for card in await cur.fetchall()]:
                        completed_rows = 0
                        for i in range(3):
                            await cur.execute(    """SELECT card.spaces_left_%s
                                              FROM card
                                                WHERE card.id = %s""", (i, card_id, ) )
                            if (await cur.fetchone())[f'spaces_left_{i}'] == 0: completed_rows += 1
                        if completed_rows > self._next_bingo:
                            self._next_bingo += 1
                            print("bingo")
                            return {"resp": 1}
                    return {"resp": 0}
        
        @__evt_handler
        async def check_spot(self, arg: dict):
            if(arg['space_number'] not in self._call_log): return {'resp': 0}
            async with self._db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(   """UPDATE space
                                            INNER JOIN card ON space.card_id = card.id
                                            INNER JOIN user ON card.user_id = user.id
                                            SET called = 1
                                            WHERE number = %s AND card.user_id = %s ;""", (arg['space_number'], arg['user_id'], )
                                        )
                    if cur.rowcount:
                        await cur.execute(  """SELECT card.id
                                                from card
                                                INNER JOIN space
                                                ON space.card_id = card.id
                                                WHERE space.number = %s and card.user_id = %s;""", (arg['space_number'], arg['user_id'], ) )
                        card_id = (await cur.fetchone())['id']
                        await cur.execute(  """SELECT space.idx
                                                from space
                                                INNER JOIN card
                                                ON space.card_id = card.id
                                                WHERE number = %s AND card.id = %s ;""", (arg['space_number'], card_id, ))
                        row = math.floor( (await cur.fetchone())['idx'] / 9 )
                        await cur.execute(  """UPDATE card
                                                SET card.spaces_left_%s = card.spaces_left_%s - 1
                                                WHERE card.id = %s""", (row, row, card_id, ) )
                        return {'resp': 1}
                    return {'resp': 0}
        
        @__evt_handler
        async def request_cards(self, arg: dict):
            async with self._db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(  """SELECT card.id
                                            from card
                                            INNER JOIN user 
                                            ON card.user_id = user.id
                                            WHERE user.id = %s""", (arg['user_id'],))
                    if(cur.rowcount > 0):
                        cards = []
                        card_ids = await cur.fetchall()
                        for card_id in card_ids:
                            await cur.execute( """SELECT idx, number, called
                                                    from space as s
                                                    INNER JOIN 
                                                    card as c
                                                    ON s.card_id = c.id
                                                    INNER JOIN
                                                    user as u
                                                    ON c.user_id = u.id
                                                    WHERE s.card_id = %s""", (card_id['id'],))
                            cards.append(await cur.fetchall())
                        return {"resp": cards}
                    else:
                        cards = []
                        gen_rows = []
                        while True:
                            try:
                                thing = [random.sample([idx for idx in range(col * 10, col * 10 + 10)], 10) for col in range(9)]
                                gen_rows = random.sample([[row for row in [thing[idx].pop() for idx in np.random.choice(range(9), size=5, replace=False, p=[len(col)/np.sum([len(col) for col in thing]) for col in thing])]] for _ in range(18)], 18)
                            except:
                                continue
                            break
                        p = lambda d: zip(d.keys(), sorted(d.values()))
                        for i in range(6):
                            card_sorted = dict()
                            a = [sorted(gen_rows.pop())+[0] for _ in range(3)]
                            for j in range(9):
                                card_sorted.update( {k*9+j:v for k,v in p( { idx:row.pop(0) for idx, row in enumerate(a) if j*10 <= row[0] < (j+1)*10 } ) } )              
                            await cur.execute( """INSERT INTO card (user_id)
                                                    VALUES (%s)""", (arg['user_id'],))
                            card_id = cur.lastrowid
                            for key, item in card_sorted.items():                                    
                                await cur.execute ( """INSERT INTO space (idx, number, card_id)
                                                        VALUES (%s, %s, %s)""", (key, item, card_id,))
                            await cur.execute(  """SELECT idx, number, called
                                                        FROM space
                                                        WHERE card_id = (%s)""", card_id)
                            cards.append(await cur.fetchall())
                        return {'resp': cards}
        

async def main():
    bingo = BingoServer()
    await bingo.start_serving()
    await asyncio.Future()
    os.unlink(_SOCK_PATH)

if __name__ == "__main__":
    print(_SOCK_PATH)
    try:
        pathlib.Path.unlink(_SOCK_PATH)
    except OSError:
        pass
    asyncio.run(main(), debug=True)
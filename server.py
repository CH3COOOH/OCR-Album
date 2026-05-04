# -*- coding: utf-8 -*-
import json
from pathlib import Path
import asyncio
import websockets

import scanner

with open('config.json', 'r') as o:
    conf = json.load(o)

class WSServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.scanner = scanner.Scanner(conf['root'],
                                    conf['db_path'],
                                    n_thread=conf['torch_thread'],
                                    gpu=conf['use_gpu'])
        self._server = None

    # ====== Lifecycle hooks (leave empty as requested) ======
    async def on_server_start(self):
        pass

    async def on_server_stop(self):
        pass

    async def on_client_connect(self, ws):
        await ws.send(json.dumps({'type': 'hello', 'payload': conf['root']}))

    async def on_client_disconnect(self, ws):
        print('Client offline.')
        pass

    async def on_message_received(self, ws, message: str):
        j_msg = json.loads(message)
        if j_msg['cmd'] == 'create_db':
            pass
        elif j_msg['cmd'] == 'search':
            qu = j_msg['payload']
            an = self.scanner.query(qu)
            an_j = []
            for a in an:
                an_j.append({'path': Path(a[0]).as_posix(), 'text': a[1]})
            print(an_j)
            await ws.send(json.dumps({'type': 'search_result', 'payload': json.dumps(an_j)}))

    # ====== Core handler ======
    async def handler(self, ws):
        await self.on_client_connect(ws)
        try:
            async for message in ws:
                await self.on_message_received(ws, message)
        except websockets.ConnectionClosed:
            pass
        finally:
            await self.on_client_disconnect(ws)

    # ====== Start/Stop ======
    async def start(self):
        await self.on_server_start()
        self._server = await websockets.serve(self.handler, self.host, self.port)
        print(f"WebSocket server listening on ws://{self.host}:{self.port}")
        return self._server

    async def run_forever(self):
        await self.start()
        try:
            await asyncio.Future()  # run forever
        finally:
            await self.stop()

    async def stop(self):
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        await self.on_server_stop()


async def main():
    server = WSServer("localhost", 8765)
    await server.run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
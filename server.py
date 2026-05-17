# -*- coding: utf-8 -*-
import json
from pathlib import Path
import shutil
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
        self.root = Path(self.scanner.root).resolve()
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
        print(j_msg)
        try:
            cmd = j_msg.get('cmd')
            if cmd == 'create_db':
                pass
            elif cmd == 'search':
                qu = j_msg['payload']
                an = self.scanner.query(qu)
                an_j = []
                for a in an:
                    an_j.append({'path': Path(a[0]).as_posix(), 'text': a[1]})
                print(an_j)
                await ws.send(json.dumps({'type': 'search_result', 'payload': json.dumps(an_j)}))
            elif cmd == 'copy':
                await self._handle_copy(ws, j_msg)
            elif cmd == 'move':
                await self._handle_move(ws, j_msg)
            elif cmd == 'delete':
                await self._handle_delete(ws, j_msg)
            else:
                await self._send_error(ws, 'unknown_command', cmd, 'Unsupported command.')
        except Exception as e:
            await self._send_error(ws, 'command_failed', j_msg.get('cmd'), str(e))

    def _abs_path(self, rel_path):
        return (self.root / rel_path).resolve()

    def _resolve_source_paths(self, paths):
        if not isinstance(paths, list) or len(paths) == 0:
            raise ValueError('paths must be a non-empty list')

        resolved = []
        for raw_path in paths:
            src = Path(raw_path)
            if src.is_absolute():
                abs_src = src.resolve()
            else:
                abs_src = (self.root / src).resolve()
            if not abs_src.exists():
                raise FileNotFoundError(f'Source not found: {raw_path}')
            if abs_src != self.root and self.root not in abs_src.parents:
                raise ValueError(f'Source path outside root: {raw_path}')
            resolved.append(abs_src.relative_to(self.root))
        return resolved

    def _resolve_target_path(self, target):
        tgt = Path(target)
        abs_tgt = tgt.resolve() if tgt.is_absolute() else (self.root / tgt).resolve()
        if abs_tgt != self.root and self.root not in abs_tgt.parents:
            raise ValueError(f'Target path outside root: {target}')
        return abs_tgt.relative_to(self.root)

    async def _send_error(self, ws, error_type, cmd, message):
        payload = {
            'type': 'error',
            'error': error_type,
            'cmd': cmd,
            'message': message,
        }
        await ws.send(json.dumps(payload))

    async def _send_result(self, ws, cmd, detail):
        payload = {
            'type': 'op_result',
            'cmd': cmd,
            'status': 'ok',
            'detail': detail,
        }
        await ws.send(json.dumps(payload))

    async def _handle_copy(self, ws, j_msg):
        src_paths = self._resolve_source_paths(j_msg.get('paths', []))
        target = j_msg.get('target')
        if not target:
            raise ValueError('copy target is required')

        target_rel = self._resolve_target_path(target)
        target_abs = self._abs_path(target_rel)
        if target_abs.exists() and target_abs.is_dir():
            for src in src_paths:
                src_abs = self._abs_path(src)
                dest_rel = target_rel / src.name
                dest_abs = self._abs_path(dest_rel)
                dest_abs.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_abs, dest_abs)
        elif len(src_paths) > 1:
            target_abs.mkdir(parents=True, exist_ok=True)
            for src in src_paths:
                src_abs = self._abs_path(src)
                dest_rel = target_rel / src.name
                dest_abs = self._abs_path(dest_rel)
                dest_abs.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_abs, dest_abs)
        else:
            dest_rel = target_rel
            dest_abs = self._abs_path(dest_rel)
            dest_abs.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self._abs_path(src_paths[0]), dest_abs)

        await self._send_result(ws, 'copy', f'Copied {len(src_paths)} file(s).')

    async def _handle_move(self, ws, j_msg):
        src_paths = self._resolve_source_paths(j_msg.get('paths', []))
        target = j_msg.get('target')
        if not target:
            raise ValueError('move target is required')

        target_rel = self._resolve_target_path(target)
        target_abs = self._abs_path(target_rel)
        if target_abs.exists() and target_abs.is_dir():
            for src in src_paths:
                src_abs = self._abs_path(src)
                dest_rel = target_rel / src.name
                dest_abs = self._abs_path(dest_rel)
                dest_abs.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src_abs), str(dest_abs))
                self.scanner.db.delete_path(str(dest_rel))
                self.scanner.db.update_path(str(src), str(dest_rel))
        elif len(src_paths) > 1:
            target_abs.mkdir(parents=True, exist_ok=True)
            for src in src_paths:
                src_abs = self._abs_path(src)
                dest_rel = target_rel / src.name
                dest_abs = self._abs_path(dest_rel)
                dest_abs.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src_abs), str(dest_abs))
                self.scanner.db.delete_path(str(dest_rel))
                self.scanner.db.update_path(str(src), str(dest_rel))
        else:
            dest_rel = target_rel
            dest_abs = self._abs_path(dest_rel)
            dest_abs.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(self._abs_path(src_paths[0])), str(dest_abs))
            self.scanner.db.delete_path(str(dest_rel))
            self.scanner.db.update_path(str(src_paths[0]), str(dest_rel))

        await self._send_result(ws, 'move', f'Moved {len(src_paths)} file(s).')

    async def _handle_delete(self, ws, j_msg):
        src_paths = self._resolve_source_paths(j_msg.get('paths', []))
        for src in src_paths:
            src_abs = self._abs_path(src)
            if src_abs.is_dir():
                raise ValueError(f'Not a file: {src}')
            src_abs.unlink()
            self.scanner.db.delete_path(str(src))

        await self._send_result(ws, 'delete', f'Deleted {len(src_paths)} file(s).')

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
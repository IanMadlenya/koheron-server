#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import struct
import json

class KoheronClient:
    def __init__(self, unixsock=''):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(unixsock)
        self.load_devices()

    def load_devices(self):
        try:
            self.send_command(1, 1)
        except:
            raise RuntimeError('Failed to send initialization command')

        self.commands = self.recv_json()
        self.devices_idx = {}
        self.cmds_idx_list = [None]*(2 + len(self.commands))

        for device in self.commands:
            self.devices_idx[device['class']] = device['id']
            cmds_idx = {}
            for cmd in device['functions']:
                cmds_idx[cmd['name']] = cmd['id']
            self.cmds_idx_list[device['id']] = cmds_idx

    def get_ids(self, device_name, command_name):
        device_id = self.devices_idx[device_name]
        cmd_id = self.cmds_idx_list[device_id][command_name]
        return device_id, cmd_id

    # -------------------------------------------------------
    # Send/Receive
    # -------------------------------------------------------

    def send_command(self, device_id, cmd_id):
        def append(buff, value, size):
            if size <= 4:
                for i in reversed(range(size)):
                    buff.append((value >> (8 * i)) & 0xff)

        cmd = bytearray()
        append(cmd, 0, 4)          # RESERVED
        append(cmd, device_id, 2)  # dev_id
        append(cmd, cmd_id, 2)     # op_id
        if self.sock.send(cmd) == 0:
            raise RuntimeError('send_command: Socket connection broken')

    def recv_all(self, n_bytes):
        '''Receive exactly n_bytes bytes.'''
        data = []
        n_rcv = 0
        while n_rcv < n_bytes:
            try:
                chunk = self.sock.recv(n_bytes - n_rcv)
                if chunk == '':
                    break
                n_rcv += len(chunk)
                data.append(chunk)
            except:
                raise RuntimeError('recv_all: Socket connection broken.')
        return b''.join(data)

    def recv_dynamic_payload(self):
        reserved, class_id, func_id, length = struct.unpack('>IHHI', self.recv_all(struct.calcsize('>IHHI')))
        return self.recv_all(length)

    def recv_json(self):
        return json.loads(self.recv_dynamic_payload().decode('utf8'))

    def __del__(self):
        if hasattr(self, 'sock'):
            self.sock.close()

if __name__ == "__main__":
    client = KoheronClient('/tmp/koheron-server.sock')
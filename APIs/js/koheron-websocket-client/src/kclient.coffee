# Websocket based client for tcp-server
# (c) Koheron

class Device
    "use strict"

    constructor: (@devname, @id, @cmds) ->
        @status = ""

    show: ->
        console.log @devname + ":\n"
        console.log "  ID: " + @id + "\n"
        console.log "  Status: " + @status + "\n"
        console.log "  Commands:\n"
        (console.log "  - " + cmd + "\n" for cmd in @cmds)

    setStatus: (status) ->
        @status = status

    getCmdRef: (cmd_name) ->
        for cmd, idx in @cmds
            if cmd == cmd_name then return idx

        throw cmd_name + " : command not found"

class WebSocketPool
    "use strict"

    constructor: (@pool_size, url, onopen_callback) ->
        if window?
            if not window.WebSocket then throw "WebSocket not supported"
        else # NodeJS
            WebSocket = require('websocket').w3cwebsocket;

        @pool = []
        @free_sockets = []
        @socket_counter = 0

        for i in [0..@pool_size-1]
            websocket = new WebSocket url
            websocket.binaryType = 'arraybuffer'
            @pool.push(websocket)

            websocket.onopen = (evt) =>
                console.log "WebSocket " + @socket_counter.toString() + " connected to " + url + "\n"
                @free_sockets.push(@socket_counter)
                if @socket_counter == 0 then @waitForConnection(websocket, 100, onopen_callback)
                @socket_counter++

            websocket.onclose = (evt) =>
                console.log "disconnected\n"

            websocket.onerror = (evt) =>
                console.error "error: " + evt.data + "\n"
                websocket.close()

    waitForConnection : (websocket, interval, callback) ->
        if websocket.readyState == 1
            callback()
        else
            setTimeout( =>
                @waitForConnection(websocket, interval, callback)
            , interval)

    getSocket: (sockid) ->
        if sockid not in @free_sockets and sockid >= 0 and sockid < @pool_size
            return @pool[sockid]
        else
            console.error "Socket ID " + sockid.toString() + " not available"
            return

    requestSocket: (callback) ->
        if @free_sockets? and @free_sockets.length > 0
            sockid = @free_sockets[@free_sockets.length-1]
            @free_sockets.pop()
            callback(sockid)
        else # All sockets are busy. We wait a bit and retry.
            setTimeout( => 
                @requestSocket(callback)
            , 100)

    freeSocket: (sockid) ->
        if sockid not in @free_sockets and sockid >= 0 and sockid < @pool_size
            @free_sockets.push(sockid)
        else
            if sockid?
                console.error "Invalid Socket ID " + sockid.toString()
            else
                console.error "Undefined Socket ID"

    exit: ->
        for websocket in @pool
            websocket.close()

# === Helper functions to build binary buffer ===

###*
# Append an Uint8 to the binary buffer
# @param {Array.<number>} buffer The binary buffer
# @param {number} value The Uint8 to append
# @return {number} Number of bytes
###
appendUint8 = (buffer, value) ->
    buffer.push(value & 0xff)
    return 1

###*
# Append an Uint16 to the binary buffer
# @param {Array.<number>} buffer The binary buffer
# @param {number} value The Uint16 to append
# @return {number} Number of bytes
###
appendUint16 = (buffer, value) ->
    buffer.push((value >> 8) & 0xff)
    buffer.push(value & 0xff)
    return 2

###*
# Append an Uint32 to the binary buffer
# @param {Array.<number>} buffer The binary buffer
# @param {number} value The Uint32 to append
# @return {number} Number of bytes
###
appendUint32 = (buffer, value) ->
    buffer.push((value >> 24) & 0xff)
    buffer.push((value >> 16) & 0xff)
    buffer.push((value >> 8) & 0xff)
    buffer.push(value & 0xff)
    return 4

###*
# Convert a float to its binary representation
# http://stackoverflow.com/questions/2003493/javascript-float-from-to-bits
# @param {number} f The float to convert
# @return {number} Uint32 containing the float binary representation
###
floatToBytes = (f) ->
    buf = new ArrayBuffer(4);
    (new Float32Array(buf))[0] = f;
    return (new Uint32Array(buf))[0];

###*
# Append a Float32 to the binary buffer
# @param {Array.<number>} buffer The binary buffer
# @param {number} value The float to append
# @return {number} Number of bytes
###
appendFloat32 = (buffer, value) ->
    appendUint32(buffer, floatToBytes(value))

class CommandBase
    "use strict"

    # Binary buffer structure:
    # |      RESERVED     | dev_id  |  op_id  |   payload_size    |   payload
    # |  0 |  1 |  2 |  3 |  4 |  5 |  6 |  7 |  8 |  9 | 10 | 11 | 12 | 13 | 14 | ...

    # http://stackoverflow.com/questions/27050784/closure-annotation-for-variadic-function
    ###*
    # Build the binary buffer of a command
    # @type {function(number, string=, ...(number|boolean)):Uint8Array}
    ###
    constructor: (dev_id, cmd_ref, types_str='', params...) ->
        buffer = []
        appendUint32(buffer, 0) # RESERVED
        appendUint16(buffer, dev_id)
        appendUint16(buffer, cmd_ref)

        if types_str.length == 0
            appendUint32(buffer, 0) # Payload size
            return new Uint8Array(buffer)

        if types_str.length != params.length
            throw 'Invalid types string length'

        payload_size = 0
        payload = []
        for i in [0..(types_str.length-1)]
            switch types_str[i]
                when 'u'
                    payload_size += appendUint32(payload, params[i])
                when 'f'
                    payload_size += appendFloat32(payload, params[i])
                when 'b'
                    if params[i]
                        payload_size += appendUint8(payload, 1)
                    else
                        payload_size += appendUint8(payload, 0)
                else
                    throw "Unknown type " + types_str[i]

        appendUint32(buffer, payload_size)
        return new Uint8Array(buffer.concat(payload))

if window?
    ###* @param {...*} var_args ###
    window.Command = (var_args) ->
        CommandBase.apply(Object.create(Command.prototype), arguments)
else # NodeJS
    ###* @param {...*} var_args ###
    Command = (var_args) ->
        CommandBase.apply(Object.create(Command.prototype), arguments)

    exports.Command = Command

class @KClient
    "use strict"

    constructor: (IP, @websock_pool_size = 5) ->
        @url = "ws://" + IP + ":8080"
        @devices_list = []

    init: (callback) ->
        @websockpool = new WebSocketPool(@websock_pool_size, @url, => 
            @getCmds(callback)
        )

    exit: -> @websockpool.exit()

    # ------------------------
    #  Send
    # ------------------------

    send: (cmd) -> 
        @websockpool.requestSocket( (sockid) =>
            websocket = @websockpool.getSocket(sockid)
            websocket.send(cmd)
            @websockpool.freeSocket(sockid)
        )

    sendArray: (cmd, array) ->
        @websockpool.requestSocket( (sockid) =>
            websocket = @websockpool.getSocket(sockid)
            websocket.send(cmd)

            websocket.onmessage = (evt) =>
                tmp_array = new Uint32Array evt.data
                if tmp_array[0] != array.length
                    throw "Invalid handshake"
                websocket.send(array.buffer)
                @websockpool.freeSocket(sockid)
        )

    # ------------------------
    #  Receive
    # ------------------------

    readUint32Array: (cmd, fn) ->
        @websockpool.requestSocket( (sockid) =>
            websocket = @websockpool.getSocket(sockid)
            websocket.send(cmd)

            websocket.onmessage = (evt) =>
                array = new Uint32Array evt.data
                fn(array)
                @websockpool.freeSocket(sockid)
        )

    readFloat32Array: (cmd, fn) ->
        @websockpool.requestSocket( (sockid) =>
            websocket = @websockpool.getSocket(sockid)
            websocket.send(cmd)

            websocket.onmessage = (evt) =>
                array = new Float32Array evt.data
                fn(array)
                @websockpool.freeSocket(sockid)
        )

    readUint32: (cmd, fn) ->
        @websockpool.requestSocket( (sockid) =>
            websocket = @websockpool.getSocket(sockid)
            websocket.send(cmd)

            websocket.onmessage = (evt) =>
                array = new Uint32Array evt.data
                fn(array[0])
                @websockpool.freeSocket(sockid)
        )

    readInt32: (cmd, fn) ->
        @websockpool.requestSocket( (sockid) =>
            websocket = @websockpool.getSocket(sockid)
            websocket.send(cmd)

            websocket.onmessage = (evt) =>
                array = new Int32Array evt.data
                fn(array[0])
                @websockpool.freeSocket(sockid)
        )

    readTuple: (cmd, fn) ->
        @websockpool.requestSocket( (sockid) =>
            websocket = @websockpool.getSocket(sockid)
            websocket.send(cmd)

            websocket.onmessage = (evt) =>
                tuple = []
                elements = evt.data.split(":")

                for elmt in elements[0..elements.length-2]
                    toks = elmt.split("@")

                    switch toks[0]
                        when "i"
                            type = "int"
                            value = parseInt(toks[1], 10)
                        when "j"
                            type = "unsigned int"
                            value = parseInt(toks[1], 10)
                        when "f"
                            type = "float"
                            value = parseFloat(toks[1])
                        when "d"
                            type = "double"
                            value = parseFloat(toks[1])
                        when "c"
                            type = "char"
                            value = toks[1]
                        when "Ss"
                            type = "string"
                            value = toks[1]
                        else
                            type = toks[0]
                            value = toks[1]

                    tuple.push({
                       type: type
                       value: value
                    })

                fn(tuple)
                @websockpool.freeSocket(sockid)
        )

    # ------------------------
    #  Devices
    # ------------------------

    getCmds: (callback) ->
         @websockpool.requestSocket( (sockid) =>
            websocket = @websockpool.getSocket(sockid)
            websocket.send(Command(1,1))
            msg_num = 0

            websocket.onmessage = (evt) =>
                msg_num++
                cmds = []

                if msg_num >= 2 and evt.data != "EOC\n"
                    tokens = evt.data.split(":")
                    devname = tokens[1]
                    id = parseInt(tokens[0], 10)

                    for i in [2..tokens.length-1]
                        if tokens[i] != "" and tokens[i] != "\n"
                            cmds.push(tokens[i])

                    dev = new Device(devname, id, cmds)
                    #dev.show()
                    @devices_list.push(dev)

                if evt.data == "EOC\n"
                    console.log "Devices loaded\n"
                    callback()
                    @websockpool.freeSocket(sockid)
        )

    getDeviceList: (fn) ->
        @getDevStatus( () => fn(@devices_list) )

    showDevices: ->
        console.log "Devices:\n"
        (device.show() for device in @devices_list)

    getDevStatus: (callback) ->
        @websockpool.requestSocket( (sockid) =>
            websocket = @websockpool.getSocket(sockid)
            websocket.send(Command(1,3))

            @websocket.onmessage = (evt) =>
                if evt.data != "EODS\n"
                    tokens = evt.data.split(":")
                    dev_id = tokens[0]

                    for device in @devices_list
                        if device.id == dev_id
                            device.setStatus(tokens[2].trim())

                else
                    console.log "Devices status updated"
                    callback()
                    @websockpool.freeSocket(sockid)
        )

    getDevice: (devname) ->
        for device in @devices_list
            if device.devname == devname then return device

        throw "Device " + devname + " not found"

    getDeviceById: (id) ->
        for device in @devices_list
            if device.id == id then return device

        throw "Device ID " + id + " not found"

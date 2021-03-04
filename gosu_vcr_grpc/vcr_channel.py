import logging

from functools import cached_property

from grpclib.client import Channel, Stream


logger = logging.getLogger(__name__)


class LoggerMixin(logging.LoggerAdapter):
    extra = {}

    @cached_property
    def logger(self):
        return logging.getLogger(f"{self.__module__}.{type(self).__name__}")

    def process(self, msg, kwargs):
        return f"[{self}] {msg}", kwargs


class VcrRecordStream(LoggerMixin):
    def __init__(self, messages, exceptions, stream: Stream):
        self.debug("__init__()")
        self.messages = messages
        self.exceptions = exceptions
        self.stream = stream

    def _record_send(self, message, *, end):
        self.messages.append(dict(direction="send", message=message, end=end))

    def _record_recv(self, message):
        self.messages.append(dict(direction="recv", message=message))

    def _record_exception(self, exception):
        self.exceptions.append(exception)

    async def send_request(self, *, end: bool = False) -> None:
        self.debug(f"send_request(end={end})")
        return await self.stream.send_request(end=end)

    async def send_message(self, message, *, end: bool = False):
        self.debug(f"send_message({message}, end={end})")
        self._record_send(message=message, end=end)
        return await self.stream.send_message(message, end=end)

    async def end(self):
        self.debug("end()")
        return await self.stream.end()

    async def recv_initial_metadata(self):
        result = await self.stream.recv_initial_metadata()
        self.debug(f"recv_initial_metadata() -> {result}")
        return result

    async def recv_message(self):
        result = await self.stream.recv_message()
        self.debug(f"recv_message() -> {result}")
        self._record_recv(message=result)
        return result

    async def recv_trailing_metadata(self):
        result = await self.stream.recv_trailing_metadata()
        self.debug(f"recv_trailing_metadata() -> {result}")
        return result

    async def cancel(self):
        self.debug("cancel()")
        return await self.stream.cancel()

    async def __aenter__(self):
        await self.stream.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self.stream.__aexit__(exc_type, exc_val, exc_tb)
        except Exception as exc:
            self._record_exception(exc)
            raise


class VcrPlaybackStream:
    def __init__(self, messages, exceptions, cassette_path):
        self.messages = messages
        self.exceptions = exceptions
        self.cassette_path = cassette_path

    def _next(self):
        assert (
            self.messages
        ), f"Reached end of cassette {self.cassette_path} instead of message"
        return self.messages.pop(0)

    def _play_send(self, message, *, end):
        expected = self._next()
        observed = dict(direction="send", message=message, end=end)
        if observed != expected:
            with open("observed", "w") as f:
                f.write(str(observed))
            with open("expected", "w") as f:
                f.write(str(expected))

            breakpoint()
        assert (
            observed == expected
        ), f"Unexpected message in cassette {self.cassette_path}: {observed} != {expected}"

    def _play_recv(self):
        message = self._next()
        direction = message["direction"]
        assert (
            "recv" == direction
        ), f"Unexpected direction {direction} in cassette {self.cassette_path}"
        return message["message"]

    async def send_message(self, message, *, end: bool = False):
        return self._play_send(message=message, end=end)

    async def recv_message(self):
        return self._play_recv()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        assert (
            not self.messages
        ), f"Stream from cassette {self.cassette_path} has not played messages on exit: {self.messages}"
        if self.exceptions:
            raise self.exceptions.pop(0)


class VcrPlaybackChannel(Channel):
    def __init__(self, host, port, cassette, cassette_path, **kwargs):
        self.cassette_path = cassette_path
        assert (
            cassette
        ), f"Unexpected end of channel list in cassette {self.cassette_path}"
        channel_track = cassette.pop(0)
        expected_channel = (channel_track["host"], channel_track["port"])
        assert (host, port) == expected_channel, (
            f"Expected channel in cassette {self.cassette_path} "
            f"is {expected_channel}, observed channel is {host, port}"
        )
        self.streams = channel_track["streams"]
        super().__init__(host, port, **kwargs)

    def request(self, name, cardinality, request_type, reply_type, **kwargs):
        assert (
            self.streams
        ), f"Unexpected end of stream list in cassette {self.cassette_path}"
        recording = self.streams.pop(0)
        # Convert message types to str because protobuf stubs have problems with serializing their classes to yaml
        observed = (name, cardinality, str(request_type), str(reply_type))
        expected = (
            recording["name"],
            recording["cardinality"],
            recording["request_type"],
            recording["reply_type"],
        )
        assert (
            observed == expected
        ), f"Unexpected stream in cassette {self.cassette_path}: {observed} != {expected}"
        return VcrPlaybackStream(
            recording["messages"], recording["exceptions"], self.cassette_path
        )


class VcrRecordChannel(Channel, LoggerMixin):
    def __init__(self, host, port, cassette_path, cassette, **kwargs):
        self.streams = []
        self.cassette_path = cassette_path
        cassette.append(dict(host=host, port=port, streams=self.streams))
        super().__init__(host, port, **kwargs)

    def request(self, name, cardinality, request_type, reply_type, **kwargs):
        self.debug(f"request({name}, {cardinality}, {kwargs})")
        messages = []
        exceptions = []
        self.streams.append(
            dict(
                name=name,
                cardinality=cardinality,
                request_type=str(request_type),
                reply_type=str(reply_type),
                messages=messages,
                exceptions=exceptions,
            )
        )
        stream = super().request(name, cardinality, request_type, reply_type, **kwargs)
        return VcrRecordStream(messages, exceptions, stream)

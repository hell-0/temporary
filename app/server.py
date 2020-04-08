#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                user_name = decoded.replace("login:", "").replace("\r\n", "").strip()
                if user_name not in self.server.users:
                    self.login = user_name
                    self.server.users.append(user_name)
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    self.send_history()
                else:
                    self.transport.write(f"Логин {user_name} занят, попробуйте другой\n".encode())
                    self.transport.abort()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def send_history(self):
        if len(self.server.history) >= 10:
            for message in self.server.history[-10:]:
                self.transport.write(message.encode())
        else:
            for message in self.server.history:
                self.transport.write(message.encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.server.history.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    users: list
    history: list

    def __init__(self):
        self.clients = []
        self.users = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")

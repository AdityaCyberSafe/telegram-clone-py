import sys

# from .components.chat_list import ChatList
from PyQt5.QtWidgets import QApplication  # type: ignore
from typing import List

from .screens.connect_to_server import ConnectToServer
from .models import Chat, User, Message

chats: List[Chat] = [
    Chat(User("", "idk_a_public_key", "A"), [Message("hi", "A", "You", "now")],),
    Chat(
        User("", "idk_a_public_key", "B"),
        [Message("I use Arch Btw", "You", "B", "now")],
    ),
]

app = QApplication(sys.argv)
window = ConnectToServer()
window.show()
app.exec_()

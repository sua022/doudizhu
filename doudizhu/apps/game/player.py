import logging
from typing import List

from tornado.websocket import WebSocketHandler

from .protocol import Protocol as Pt
from .rule import rule

logger = logging.getLogger(__file__)

FARMER = 1
LANDLORD = 2


class Player(object):
    def __init__(self, uid: int, name: str, socket: WebSocketHandler = None):
        from .table import Table
        self.uid = uid
        self.name = name
        self.socket = socket
        self.table: Table = None
        self.ready = False
        self.seat = 0
        self.is_called = False
        self.role = FARMER
        self.hand_pokers: List[int] = []

    async def reset(self):
        self.ready = False
        self.is_called = False
        self.role = FARMER
        self.hand_pokers: List[int] = []
        await self.send([Pt.RSP_RESTART])

    async def send(self, packet):
        await self.socket.write_message(packet)

    async def handle_call_score(self, score):
        if 0 < score < self.table.call_score:
            logger.warning('Player[%d] CALL SCORE[%d] CHEAT', self.uid, score)
            return

        if score > 3:
            logger.warning('Player[%d] CALL SCORE[%d] CHEAT', self.uid, score)
            return

        self.is_called = True

        next_seat = (self.seat + 1) % 3

        call_end = score == 3 or self.table.all_called()
        if not call_end:
            self.table.whose_turn = next_seat
        if score > 0:
            self.table.last_shot_seat = self.seat
        if score > self.table.max_call_score:
            self.table.max_call_score = score
            self.table.max_call_score_turn = self.seat
        response = [Pt.RSP_CALL_SCORE, self.uid, score, call_end]
        for p in self.table.players:
            await p.send(response)

        if call_end:
            await self.table.call_score_end()

    async def handle_shot_poker(self, pokers):
        if pokers:
            if not rule.is_contains(self.hand_pokers, pokers):
                logger.warning('Player[%d] play non-exist poker', self.uid)
                return

            if self.table.last_shot_seat != self.seat and rule.compare_poker(pokers, self.table.last_shot_poker) < 0:
                logger.warning('Player[%d] play small than last shot poker', self.uid)
                return
        if pokers:
            self.table.history[self.seat] += pokers
            self.table.last_shot_seat = self.seat
            self.table.last_shot_poker = pokers
            for p in pokers:
                self.hand_pokers.remove(p)

        if self.hand_pokers:
            self.table.go_next_turn()

        response = [Pt.RSP_SHOT_POKER, self.uid, pokers]
        for p in self.table.players:
            await p.send(response)
        logger.info('Player[%d] shot[%s]', self.uid, str(pokers))

        if not self.hand_pokers:
            await self.table.on_game_over(self)
            return

    async def join_table(self, t):
        self.ready = True
        self.table = t
        t.on_join(self)

    async def leave_table(self):
        self.ready = False
        if self.table:
            await self.table.on_leave(self)
        # self.table = None

    def __str__(self):
        return f'{self.uid}-{self.name}'

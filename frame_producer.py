from time import sleep

from rtcbot import MostRecentSubscription
from rtcbot.base import ThreadedSubscriptionProducer
import cv2


class FrameProducer(ThreadedSubscriptionProducer):
    frame_number = 1

    def __init__(self, loop):
        super().__init__(MostRecentSubscription, loop=loop)
        self.cap = None
        self.read_new_frame = True

    def set_frame(self):
        self.read_new_frame = True

    def _producer(self):
        # self._setReady(True)
        # self.cap = cv2.VideoCapture('record0001.mp4')
        # while not self._shouldClose:
        #     ret, frame = self.cap.read()
        #     if ret:
        #         self._put_nowait(frame)
        # self._setReady(False)

        self._setReady(True)
        self.cap = cv2.VideoCapture(0)
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            self._put_nowait(frame)
            # sleep(0.04)
        self._setReady(False)

    def subscribe(self, subscription=None):
        return super().subscribe(subscription)

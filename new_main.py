import asyncio
from threading import Thread
import aiohttp_cors as aiohttp_cors
import requests as requests
from aiohttp import web
from aiortc import RTCConfiguration, RTCIceServer
from rtcbot import RTCConnection
from frame_producer import FrameProducer
from time import sleep
import json
import os

frame_producer = None
conn_list = []


def retrieve_offer():
    # https://backend.retrocausal.tech/offer/retrieve_offer/
    retrieved_offer = requests.get(url='https://backend.retrocausal.tech/offer/get_offer/?device=7c:70:db:0d:87:f7')
    offer = retrieved_offer.json()
    if not offer:
        return
    if 'error' in offer:
        return
    with open('offer.json', 'w') as r:
        json.dump(offer, r)
    # requests.delete(url='https://backend.retrocausal.tech/offer/remove_offer/?device=7c:70:db:0d:87:f7')


def consume_offer():
    device = '7c:70:db:0d:87:f7'
    # patch_url = url_for('put')

    while True:
        sleep(2)
        try:
            retrieve_offer()
            with open('offer.json', 'r') as r:
                offer = json.load(r)
            if offer:
                del offer['device']
                response = requests.post('http://localhost:8080/connect', data=json.dumps(offer), headers={
                        'Content-Type': 'application/json'
                    })
                data = json.loads(response.content.decode('utf-8'))
                data['device'] = device
                requests.patch('https://backend.retrocausal.tech/offer/answer_offer/', data=data)
                os.remove('offer.json')
                # print('I consumed an offer')
        except Exception as e:
            # print(e)
            print('error in offer handler.')


async def connect(request):
    print("inside connect function")
    client_offer = await request.json()
    rtc_connection = RTCConnection()
    # rtc_connection = RTCConnection(rtcConfiguration=RTCConfiguration(
    #     [RTCIceServer(urls='turn:13.232.171.210:3478', username="retrortc", credential="retrocausal")]))
    conn_list.append(rtc_connection)
    global frame_producer
    frame_producer = FrameProducer(loop=RTCServer.event_loop)
    producer = frame_producer
    rtc_connection.video.putSubscription(producer)
    server_answer = await rtc_connection.getLocalDescription(client_offer)
    return web.json_response(server_answer)


async def cleanup(app=None):
    if conn_list:
        for con in conn_list:
            con.close()


def add_cors_permission(app):
    cors = aiohttp_cors.setup(app,
                              defaults={
                                  "*": aiohttp_cors.ResourceOptions(allow_headers=["Access-Control-Allow_Origin"])
                              })
    resource = cors.add(app.router.add_resource('/connect'))
    cors.add(
        resource.add_route("POST", connect),
        {
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers='*',
                allow_headers='*',
            )
        }
    )


def web_rtc_server():
    print('running WEB RTC server')
    app = web.Application()
    add_cors_permission(app)
    app.on_shutdown.append(cleanup)
    runner = web.AppRunner(app)
    return runner


class RTCServer(Thread):
    event_loop = None
    runner = None
    site = None
    is_running = False

    def run(self) -> None:
        print('started running RTC server')
        RTCServer.is_running = True
        RTCServer.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(RTCServer.event_loop)
        # global frame_producer
        # if not frame_producer:
        #     frame_producer = FrameProducer(loop=RTCServer.event_loop)
        RTCServer.runner = web_rtc_server()
        RTCServer.event_loop.run_until_complete(RTCServer.runner.setup())
        RTCServer.site = web.TCPSite(RTCServer.runner, '0.0.0.0', 8080)
        RTCServer.event_loop.run_until_complete(RTCServer.site.start())
        RTCServer.event_loop.run_forever()

    @staticmethod
    def stop():
        pass


RTCServer().start()
consume_offer()

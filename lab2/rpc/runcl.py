import rpc
import logging
import time

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

def handle_result(result):
    print(f"[Callback] Ergebnis erhalten: {result.value}")



cl = rpc.Client()
cl.run()

base_list = rpc.DBList({'foo'})

#Asynchronous call with callback
cl.append('bar', base_list, callback=handle_result)


for i in range(4):
    print(f"[Client] macht Task{i}")
    time.sleep(1)

cl.stop()

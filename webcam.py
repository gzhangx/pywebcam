#based on https://github.com/damiencorpataux/pymjpeg
import cv2
import io
import socket
import struct
import time
import pickle
import zlib

from http.server import HTTPServer, BaseHTTPRequestHandler

boundary = '--boundarydonotcross'

def request_headers():
    return {
        'Cache-Control': 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0',
        'Connection': 'close',
        'Content-Type': 'multipart/x-mixed-replace;boundary=%s' % boundary,
        'Expires': 'Mon, 3 Jan 2000 12:34:56 GMT',
        'Pragma': 'no-cache',
    }

def image_headers(len):
    return {
        'X-Timestamp': time.time(),
        'Content-Length': len,
        #FIXME: mime-type must be set according file content
        'Content-Type': 'image/jpeg',
    }

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((socket.gethostname(), 9000))
s.listen(5)

#cam = cv2.VideoCapture(0)

#cam.set(3, 640);
#cam.set(4, 480);
#ret, frame = cam.read()
#print('done read',ret,frame.shape)
img_counter = 0
cam = None

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]


def nouse():
    client_socket, address = s.accept()
    print(f"Connection from {address} has been established!")

    ret, frame = cam.read()
    result, frame = cv2.imencode('.jpg', frame, encode_param)

    data = pickle.dumps(frame, 0)
    size = len(data)

    print("{}: {}".format(img_counter, size))
    client_socket.send(struct.pack(">L", size) + data)
    print("ooga")
    img_counter += 1

connCount = 0
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global connCount, cam
        connCount = connCount+1
        print("Connection count " + str(connCount))
        if cam is None:
            cam = cv2.VideoCapture(0)
            cam.set(3, 640);
            cam.set(4, 480);       
        print("cam allocated")
        
        try:
            self.send_response(200)
            # Response headers (multipart)
            for k, v in request_headers().items():
                self.send_header(k, v) 
            # Multipart content
            while True:
                ret, oframe = cam.read()
                result, frame = cv2.imencode('.jpg', oframe, encode_param)
                data = frame.tobytes() #pickle.dumps(frame, 0)
                size = len(data)

                #print('done read',ret,oframe.shape,size, result)
                # Part boundary string
                self.end_headers()
                self.wfile.write(bytes(boundary, 'utf-8'))
                self.end_headers()
                # Part headers
                for k, v in image_headers(size).items():
                    self.send_header(k, v) 
                self.end_headers()
                # Part binary
                #for chunk in pymjpeg.image(filename):
                self.wfile.write(data)
                time.sleep(0.5)
        except (ConnectionResetError, ConnectionAbortedError) as e:
            print("client disconnected")
        connCount = connCount - 1
        if connCount <= 0:
            print("stopping cam")
            cam.release()
            cam = None

    def log_message(self, format, *args):
        return

httpd = HTTPServer(('', 8081), MyHandler)
httpd.serve_forever()

cam.release()
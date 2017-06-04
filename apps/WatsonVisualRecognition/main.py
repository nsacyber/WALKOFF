from apps import App
from watson_developer_cloud import VisualRecognitionV3 as vr
import json


class Main(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.engine = vr('2016-05-20', api_key=self.get_device().get_password())

    def recognize_text_from_remote_url(self, args={}):
        result = self.engine.recognize_text(images_url=args['url']())
        return json.dumps(result['images'][0]['text'])

    def recognize_text_from_local_file(self, args={}):
        result = self.engine.recognize_text(images_file=args['path']())
        return json.dumps(result['images'][0]['text'])

    def detect_faces_from_remote_url(self, args={}):
        result = self.engine.detect_faces(images_url=args['url']())
        return json.dumps(result['images'][0]['faces'])

    def detect_faces_from_local_file(self, args={}):
        result = self.engine.detect_faces(images_file=args['path']())
        return json.dumps(result['images'][0]['faces'])

    def classify_from_remote_url(self, args={}):
        result = self.engine.classify(images_url=args['url']())
        return json.dumps(result['images'][0]['classifiers'])

    def classify_from_local_file(self, args={}):
        result = self.engine.classify(images_file=args['path']())
        return json.dumps(result['images'][0]['classifiers'])

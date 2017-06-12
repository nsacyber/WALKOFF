from apps import App, action
from watson_developer_cloud import VisualRecognitionV3 as vr
import json


class Main(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.engine = vr('2016-05-20', api_key=self.get_device().get_password())

    @action
    def recognize_text_from_remote_url(self, url):
        result = self.engine.recognize_text(images_url=url)
        return json.dumps(result['images'][0]['text'])

    @action
    def recognize_text_from_local_file(self, path):
        result = self.engine.recognize_text(images_file=path)
        return json.dumps(result['images'][0]['text'])

    @action
    def detect_faces_from_remote_url(self, url):
        result = self.engine.detect_faces(images_url=url)
        return json.dumps(result['images'][0]['faces'])

    @action
    def detect_faces_from_local_file(self, path):
        result = self.engine.detect_faces(images_file=path)
        return json.dumps(result['images'][0]['faces'])

    @action
    def classify_from_remote_url(self, url):
        result = self.engine.classify(images_url=url)
        return json.dumps(result['images'][0]['classifiers'])

    @action
    def classify_from_local_file(self, path):
        result = self.engine.classify(images_file=path)
        return json.dumps(result['images'][0]['classifiers'])

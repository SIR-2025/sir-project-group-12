import argparse
import collections
import os

import cv2
import numpy as np
import torch
import torchvision
from numpy import array
from sklearn.neighbors import KNeighborsClassifier

from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import (
    BoundingBox,
    BoundingBoxesMessage,
    CompressedImageMessage,
    CompressedImageRequest,
    SICMessage,
)
from sic_framework.core.service_python2 import SICService


class DNNFaceRecognitionComponent(SICService):

    # loading resnet takes some time
    COMPONENT_STARTUP_TIMEOUT = 15
    model_path = None
    cascade_path = None

    def __init__(self, *args, **kwargs):
        super(DNNFaceRecognitionComponent, self).__init__(*args, **kwargs)
        self.save_image = False
        self.img_timestamp = None

        # Initialize face recognition data
        self.device = "cpu"
        if torch.cuda.is_available():
            self.device = "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"

        # import is relative, so only works when this file is main
        from sic_framework.services.face_recognition_dnn.model import resnet50

        self.model = resnet50(include_top=False, num_classes=8631)
        if not os.path.isfile(DNNFaceRecognitionComponent.model_path):
            raise FileNotFoundError(
                f"Model path {DNNFaceRecognitionComponent.model_path} is not correct."
            )
        else:
            model_path = DNNFaceRecognitionComponent.model_path
        self.model.load_state_dict(torch.load(model_path))
        self.model.to(self.device)

        if not os.path.isfile(DNNFaceRecognitionComponent.cascade_path):
            raise FileNotFoundError(
                f"Cascade path {DNNFaceRecognitionComponent.cascade_path} is not correct."
            )
        else:
            cascadePath = DNNFaceRecognitionComponent.cascade_path
        self.faceCascade = cv2.CascadeClassifier(cascadePath)

        # Define min window size to be recognized as a face_img
        self.minW = 150
        self.minH = 150

        self.ids = []
        self.next_id = 1

        self.classifier = KNeighborsClassifier(n_neighbors=1)

        # maxlen=number of face embeddings we remember for classification
        self.features_history = collections.deque([], maxlen=3000)

    @staticmethod
    def get_inputs():
        return [CompressedImageMessage, CompressedImageRequest]

    @staticmethod
    def get_output():
        return BoundingBoxesMessage

    def on_message(self, message):
        bboxes = self.detect(message.image)
        self.output_message(bboxes)

    def on_request(self, request):
        return self.detect(request.image)

    def detect(self, image):
        id = 0

        img = array(image)[:, :, ::-1].astype(np.uint8)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        face_boxes = self.faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(self.minW), int(self.minH)),
        )

        faces = []

        for x, y, w, h in face_boxes:
            face = img[y : y + h, x : x + w, :]
            face = cv2.resize(face, (224, 224))

            tf = torchvision.transforms.ToTensor()

            face_tensor = tf(face)[np.newaxis, ...].to(self.device)

            features = self.model(face_tensor)
            features = features.detach().cpu().numpy().squeeze()
            self.features_history.append(features)
            feat_hist_arr = np.array(self.features_history)

            # predict id if a face has been seen before
            if len(self.ids) >= 1:
                id = self.classifier.predict([features])[0]

                # simple thresholding to figure out if it is a new face (for which we need to exclude the new face
                # itself)
                dist = np.min(np.linalg.norm(feat_hist_arr[:-1] - features, axis=1))

                if dist > 15:  # very magic trial by error number
                    self.logger.info("-------------------------------------------")
                    self.logger.info("New Face!, high distance of {}".format(dist))
                    self.logger.info("-------------------------------------------")
                    id = self.next_id
                    self.next_id += 1

                else:
                    self.logger.info("Recognized face {}".format(id))

            # update kNN classifier
            self.ids.append(id)
            self.classifier.fit(feat_hist_arr, self.ids)

            face = BoundingBox(x, y, w, h, identifier=id)

            faces.append(face)

        return BoundingBoxesMessage(faces)


class DNNFaceRecognition(SICConnector):
    component_class = DNNFaceRecognitionComponent


def main():
    parser = argparse.ArgumentParser(
        description="Run face recognition with  a model file and cascade file"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to the model file (e.g., model.pt)",
    )
    parser.add_argument(
        "--cascadefile",
        type=str,
        required=True,
        help="Path to the cascade classifier XML file",
    )
    args = parser.parse_args()

    # pass model files to component
    DNNFaceRecognitionComponent.model_path = args.model
    DNNFaceRecognitionComponent.cascade_path = args.cascadefile

    SICComponentManager([DNNFaceRecognitionComponent])


if __name__ == "__main__":
    main()

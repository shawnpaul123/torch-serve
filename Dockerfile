## I built the Torch Serve image locally before running this, cf github torchserve:
## https://github.com/pytorch/serve/tree/master/docker
FROM pytorch/torchserve:latest

USER root

# Set up utilities and copy files
RUN apt-get update
RUN apt-get install -y libgl1-mesa-glx
RUN apt-get install -y libglib2.0-0
RUN apt-get install -y python3-distutils

# Copy local files into image
COPY ./resources/ /home/model-server/resources/

RUN chmod -R a+rw /home/model-server/

# Running as non-root 
USER model-server

# Installing Python dependencies 
RUN pip3 install --upgrade pip
RUN pip install torch-model-archiver
RUN pip install opencv-python
RUN python3 -c "import cv2"
RUN pip install -r /home/model-server/resources/yolov5/requirements.txt

# Exposing ports & setting PYTHONPATH for Torch Serve
EXPOSE 8080 8081
ENV PYTHONPATH "${PYTHONPATH}:/home/model-server/resources/yolov5/"

# Build and ship ML model (.mar)
RUN python /home/model-server/resources/yolov5/models/export.py --weights /home/model-server/resources/best.pt --img 416 --batch-size 16 --inplace --include torchscript
RUN torch-model-archiver --model-name asl_classifier \
--version 0.1 --serialized-file /home/model-server/resources/best.torchscript.pt \
--handler /home/model-server/resources/torchserve_handler.py \
--extra-files /home/model-server/resources/index_to_name.json,/home/model-server/resources/torchserve_handler.py
RUN mv asl_classifier.mar /home/model-server/model-store/asl_classifier.mar

# Serve model
CMD [ "torchserve", "--start", "--model-store", "/home/model-server/model-store/", "--models", "asl_classifier.mar" ]


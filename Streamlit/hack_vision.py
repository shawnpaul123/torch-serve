from streamlit_webrtc import webrtc_streamer
import av
import os, glob
import streamlit as st
from collections import deque
from PIL import Image
import datetime
from skimage.transform import resize
from azure_interact import main

def clean_up_folders():
    loc = './img_preprocess/*'
    files = glob.glob(loc)
    for f in files:
        os.remove(f)


class variable_holder:
    def __init__(self):
        self.min_frame_value = 0
        self.max_frame_value = 1024
        self.frame_value = None
        self.img_size = 416
        self.batchsize = [0,2,8,16]
        self.img_write_loc = './img_preprocess/'
        self.save_img_format = "rgb24"
        self.show_img_format = "bgr24"
        self.frame_prob_threshold = None

def proceed_to_demo():
    st.markdown("""
    # Pytorch Annual Hackathon

    ## ASL To Text


    ### Demonstration of Near-Real Time Application using Pytorch and Microsoft Azure

    This demo shows the following:
    * selection of inputs to pass into a streamlit app
    * running of backend model services or pre-made demo video
    * confidence factor for each frame
    * batch size [Beta]

    """)

    var_go_button = st.checkbox('Hit Me To Demo!')
    
    if var_go_button:
        return True

def get_inputs():   
    v_h = variable_holder()
    st.text('BETA features are still under development')
    backend = st.selectbox('Choose if you wish to pre-run demo backend', ['Pre-Run','Run Now'])
    frame_percent =  st.slider('Choose Frame Selection Probability',min_value = 0,max_value = 100) 
    batch_size = st.selectbox('Select Max Batch Size[Beta]',v_h.batchsize)


    return [backend,frame_percent,batch_size]

if __name__ == '__main__':

    values_map = {
    0:'A',
    1:'B',
    2:'C',
    3:'D',
    4:'E',
    5:'F',
    6:'G',
    7:'H',
    8:'I',
    9:'J',
    10:'K',
    11:'L',
    12:'M',
    13:'N',
    14:'O',
    15:'P',
    16:'Q',
    17:'R',
    18:'S',
    19:'T',
    20:'U',
    21:'V',
    22:'W',
    23:'X',
    24:'Y',
    25:'Z'
    }

    
    #clean_up_folders()
    demo = proceed_to_demo()

    #start the demo
    if demo:
        #get the inputs
        [backend,frame_percent,batch_size] = get_inputs()

        if frame_percent !=0 and batch_size !=0:
            st.header("Sample Video Unprocessed")
            data = 'video_test.mov'
            st.video(data, format='video/mp4', start_time=0)            
        
        
            
            if backend == 'Pre-Run':
                pass

            if backend == 'Run Now':
                st.header('Uploading to BackEnd to get Model Outputs')
                frame_percent = int(frame_percent/100)
                st.spinner()                
                main(values_map,frame_percent)
                


        #call api function to send to azure only selected frames
        show_video = st.checkbox('Hit Me Show Video!')
        if show_video:
            st.header("Video Processed")
            data = 'my_video.mp4'
            st.video(data, format='video/mp4', start_time=0)
                



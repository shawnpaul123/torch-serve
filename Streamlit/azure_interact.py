from os import listdir
from os.path import isfile, join
import os
import yaml
import glob
from azure.storage.blob import ContainerClient
import requests
import cv2
from PIL import Image
import moviepy.video.io.ImageSequenceClip

class variable_holder:
    def __init__(self):
        self.min_frame_value = 0
        self.max_frame_value = 1024
        self.frame_value = None
        self.img_size = 224
        self.batchsize = [0,2,8,16]
        self.img_write_loc = './img_preprocess/'
        self.save_img_format = "rgb24"
        self.show_img_format = "bgr24"
        self.frame_prob_threshold = None
        
#deletes all files from the folder     
def clean_up_folders(path):
    loc = path +'*'
    files = glob.glob(loc)
    for f in files:
        os.remove(f)        

#load config vars
def load_config():
    dir_root = os.path.dirname(os.path.abspath(__file__))
    with open(dir_root + "/config.yml", 'r') as yamlfile:
        return yaml.load(yamlfile,Loader=yaml.FullLoader)

#get all the frames
def get_files(dir):
    with os.scandir(dir) as entries:
        for entry in entries:
            if entry.is_file() and not entry.name.startswith('.'):
                yield entry

#upload to blob container
def upload(file,connection_string,container_name):
    container_client = ContainerClient.from_connection_string(connection_string,container_name)
    print('Uploading to Azure')    
    blob_client = container_client.get_blob_client("img1")
    with open(file.path,'rb') as data:
        blob_client.upload_blob(data)
        print(f'{file.name} uploaded to blob storage')

#Create a function to delete image in azure blob storage
def delete(frame, connection_string, container_name):
    container_client = ContainerClient.from_connection_string(connection_string, container_name)
    print("Deleting files to blob storage...")
    blob_client = container_client.get_blob_client("img1")
    blob_client.delete_blob()
    #container_client.delete_blob(frame)
    print(f'Deleted from blob storage')

#exif stripping and sizeing of images
def read_and_write_to_format(mypath,size):

    for path in sorted([f for f in listdir(mypath) if isfile(join(mypath, f))]):
        image = Image.open(mypath + path)
        image = image.resize((size,size))
        # next 3 lines strip exif
        new_path = path.rsplit('/', 1)[0]
        #resizing
        
        if not os.path.exists('./img_postprocess/'):
            os.makedirs('./img_postprocess/')  

        image.save('./img_postprocess/' + new_path)


#imprint model outputs on frames
def process_images(resp,path,map_letter,conf_thresh):
    
    img = cv2.imread(path)
    size = img[0].shape[1], img[0].shape[0]

    return_array = sum(resp,[])[0]
    
    x1,y1,x2,y2 = return_array[0], return_array[1], return_array[2] - return_array[0], return_array[3] - return_array[1]
    confidence = return_array[4]
    print(confidence)
    #if confidence less than threshold - just return the image
    if confidence < conf_thresh:
        return img

    #put bounding boxes
    letter = map_letter[return_array[5]]
    img = cv2.rectangle(img, (int(x1),int(y1)), (int(x2), int(y2)), (255,0,0), 2)
    
    #create boxes  
    font                   = cv2.FONT_HERSHEY_SIMPLEX
    bottomLeftCornerOfText = (10,100)
    fontScale              = 3
    fontColor              = (255,0,0)
    lineType               = 3

    #add ASL charachter
    img = cv2.putText(img,letter,
    bottomLeftCornerOfText, 
    font, 
    fontScale,
    fontColor,
    lineType)
    return img
   

#convert initial video to multiple frames
def decompose_video():
    path = 'video_test.mov'    
    vc = cv2.VideoCapture(path)
    c=1

    if vc.isOpened():
        rval , frame = vc.read()
    else:
        rval = False
    
    try:
        while rval:
            
            
            rval, frame = vc.read()
            cv2.imwrite('./img_preprocess/' + str(c) + '.jpg',frame)
            c = c + 1
            
        vc.release()
    except:
        pass


#get all frames - processed//unprocessed
def get_image_files():
    mypath = './img_postprocess/'
    get_unprocess_img_names = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    mypath = './img_prevideo/'
    get_process_img_names = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    missing_processed_frames = list(set(get_unprocess_img_names) - set(get_process_img_names))
    missing_processed_frames = ['./img_postprocess/{}'.format(f) for f in missing_processed_frames]
    get_process_img_names = ['./img_prevideo/{}'.format(f) for f in get_process_img_names]
    all_frames = missing_processed_frames + get_process_img_names
    #print(all_frames[0].split('/',-1)[-1])
    all_frames.sort(key = lambda x: int(x.split('/')[-1].split('.')[0]))
    #print(all_frames)
    assert len(all_frames) == len(get_process_img_names) + len(missing_processed_frames)    
    return all_frames
#create video from model imprinted frames
def create_video():
    fps=10
    image_files = get_image_files()
    #image_files = sorted([os.path.join(image_folder,img) for img in os.listdir(image_folder) if img.endswith(".jpg")])
    clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(image_files, fps=fps)
    clip.write_videofile('my_video.mp4')


#run the script
def main(values,thresh):
    size = (3,416)
    size_ = 416
    mypath = './img_preprocess/'
    config = load_config()

    #clear all folders
    path = './img_preprocess/'
    clean_up_folders(path)
    path = './img_prevideo/'
    clean_up_folders(path)
    path = './img_postprocess/'
    clean_up_folders(path)
    print('cleaned folders')
    #decompose video into first batch of frames
    decompose_video()
    print('decomposed video')
    #write to appropriate format - 416v416 and EXIF stripping
    read_and_write_to_format(mypath,size_)
    #get all the frames 
    frames = get_files(config["source_folder"])
    counter = 0
    for frame in frames:
        ###################################################
        #upload but if blob exists - delete and then upload
        try:
            upload(frame, config["azure_storage_connectionstring"],config['container_name'])
        except:            
            delete(frame, config["azure_storage_connectionstring"], config["container_name"])
            
        
        
        # Making a get request to get the json of the image
        response = requests.get('https://prod-05.northcentralus.logic.azure.com:443/workflows/9d0aa73d77754b40821db349edfda90c/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=8VtSemSIBJiiYWrz2eKjJIFTNpP_iI-mIO0-ktYJeRE')
       ###################################################
       #if the response is an error - go the start of the loop

        if not isinstance(response.json(), list):
            continue
        
        if len(sum(response.json(),[])) == 0:
            continue

        ###################################################

        else:
            
            cv2_img = process_images(resp=response.json(), path = frame.path, map_letter=values,conf_thresh=thresh) 
            model_frame_path = './img_prevideo/{}'.format(frame.name)      
            cv2.imwrite(model_frame_path, cv2_img)            
            

        
    print('got responses for everything')
    #Clearing blob for next upload
    print('deleting blob')
    delete(frames, config["azure_storage_connectionstring"], config["container_name"])
    #create video and then return true
    print('creating video')
    
    create_video()
    
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

    thresh = 0.5

    main(values_map,thresh)


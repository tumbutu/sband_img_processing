import sys, getopt

#-----------------------
#define needed constants
#-----------------------
MPTEG_INDICATOR     = bytes.fromhex('47 01 02')
MPTEG_HEADER_SIZE   = 4
MPTEG_PACKET_SIZE   = 188
JPEG_HEAD           = bytes.fromhex('FF D8')
JPEG_TAIL           = bytes.fromhex('FF D9')
JPEG_TAG_SIZE       = 2

def pre_checks(argv):
    global inputfile, outputfile
    inputfile   = ''
    outputfile  = ''
    
    opts, args = getopt.getopt(argv[1:],"hi:o:",["ifile=","ofile="])
    
    for opt, arg in opts:
      
      if opt == '-h':
         print (argv[0],' -i <input_file> -o <output_file>')
         sys.exit()
      elif opt in ("-i", "--ifile"):
         inputfile = arg
      elif opt in ("-o", "--ofile"):
         outputfile = arg

def load_file():
    try:
        srcFile = open(inputfile, 'rb')
        global srcArr
        srcArr = srcFile.read()
        srcFile.close()
    except:
        print("ERROR: failed to open ",inputfile)
        sys.exit()

def find_mpteg_tags():
    global mtp_count
    mtp_count = srcArr.count(MPTEG_INDICATOR)
    
def find_jpeg_tags():
    global jh_idx, jt_idx
    jh_idx = srcArr.find(JPEG_HEAD)
    jt_idx = srcArr.find(JPEG_TAIL)
    
def slice_array_by_jpeg_tag():
    global jpeg_go_from_head, jpeg_come_to_tail
    global in_head_idx, in_tail_idx, head_grp_size, tail_grp_size
    
    #---------------------------------------------------------------
    #slice the data piece surrounded by the jpeg tags, tags included 
    #---------------------------------------------------------------
    if(jh_idx > jt_idx):
        jpeg_go_from_head = srcArr[jh_idx : ]
        jpeg_come_to_tail = srcArr[ : jt_idx + JPEG_TAG_SIZE]   #include jpeg closing tag
        
        head_grp_size = len(jpeg_go_from_head);
        tail_grp_size = len(jpeg_come_to_tail);
        
        #print(hex(jpeg_go_from_head[0]), '...', hex(jpeg_go_from_head[-1]), 'size: ', head_grp_size)
        #print(hex(jpeg_come_to_tail[0]), '...', hex(jpeg_come_to_tail[-1]), 'size: ', tail_grp_size)
        
    else:
        print("error: jpeg tail comes before head")
        sys.exit()

def mtpeg_header_count():
    global in_head_count, in_tail_count
    
    in_head_count = jpeg_go_from_head.count(MPTEG_INDICATOR)
    in_tail_count = jpeg_come_to_tail.count(MPTEG_INDICATOR)
        
def find_mtpeg_first_header_index():
    global in_head_idx, in_tail_idx
    
    in_head_idx = jpeg_go_from_head.find(MPTEG_INDICATOR)
    in_tail_idx = jpeg_come_to_tail.find(MPTEG_INDICATOR)
    
    #print(in_head_idx)
    #print(in_tail_idx)

def slice_data_by_mtpeg_header_and_save():
    global outputfile
    myArr = 0
    
    if not outputfile:
        outputfile = 'output.jpg'
    f_wrt = open(outputfile, 'wb')
           
    #-----------------------
    #process the head bundle
    #-----------------------
    rem_size = head_grp_size
    srt_idx = 0
    end_idx = in_head_idx
    
    while(rem_size > 0):
        if(rem_size >= MPTEG_PACKET_SIZE):
            myArr = jpeg_go_from_head[srt_idx : end_idx]
            rem_size = rem_size - MPTEG_PACKET_SIZE
            srt_idx = srt_idx + len(myArr) + MPTEG_HEADER_SIZE
            end_idx = srt_idx + MPTEG_PACKET_SIZE - MPTEG_HEADER_SIZE
        else:
            myArr = jpeg_go_from_head[srt_idx + MPTEG_HEADER_SIZE : ]
            rem_size = rem_size - MPTEG_PACKET_SIZE
            
        f_wrt.write(myArr)
        
    #-----------------------
    #process the tail bundle
    #-----------------------
    rem_size = tail_grp_size
    srt_idx = in_tail_idx
    end_idx = MPTEG_PACKET_SIZE
    
    while(rem_size > 0):
                
        if(rem_size >= MPTEG_PACKET_SIZE):
            srt_idx = srt_idx + MPTEG_HEADER_SIZE 
            myArr = jpeg_come_to_tail[srt_idx : end_idx]
            rem_size = rem_size - MPTEG_PACKET_SIZE
            srt_idx = srt_idx + len(myArr)
            end_idx = srt_idx + MPTEG_PACKET_SIZE
            
        else:         
            myArr = jpeg_come_to_tail[srt_idx + MPTEG_HEADER_SIZE : ]
            rem_size = rem_size - MPTEG_PACKET_SIZE
            
        f_wrt.write(myArr)

    f_wrt.close()
             
if __name__ == "__main__":
    #-----------
    #check flags
    #-----------
    pre_checks(sys.argv)
    
    #-------------
    #load the file
    #-------------
    load_file()
    
    #-----------------------
    #find index of jpeg tags
    #-----------------------
    find_jpeg_tags()
    
    #--------------------------
    #bundle up data by jpeg tag
    #--------------------------
    slice_array_by_jpeg_tag()
    
    #-----------------------------------------------
    #count the number of mtpeg header in each bundle
    #-----------------------------------------------
    #mtpeg_header_count()
    
    #--------------------------------------
    #find the first mtpeg index in each grp
    #--------------------------------------
    find_mtpeg_first_header_index()
    
    #--------------------------
    #slice the two array group 
    #by header & mtpeg size 188
    #--------------------------
    slice_data_by_mtpeg_header_and_save()
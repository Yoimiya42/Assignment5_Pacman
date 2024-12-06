

import pickle

msg = 'Hello'

msg_bytes = pickle.dumps(msg)
print(msg_bytes) # b'\x80\x04\x95\x08\x00\x00\x00\x00\x00\x00\x00\x8c\x04Ming\x94.'
len_msg_bytes = len(msg_bytes)
print(len_msg_bytes)  # 19
num = 1152
lenbytes1 = num.to_bytes(4, byteorder = 'little')
lenbytes2 = num.to_bytes(4, byteorder = 'big')
print(lenbytes1)  # little endian :
print(lenbytes2)  # big endian    : 


    

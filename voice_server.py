import socket
import pyaudio
import wave
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib
import tkinter as tk

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
OUTPUT_FILENAME = "received.wav"  # Name of the received audio file
INPUT_FILENAME = "response.wav"   # Name of the response audio file
SERVER_IP = '127.0.0.1'
PORT = 12345

def generate_key(password):
    key = hashlib.sha256(password.encode()).digest()
    return key

# Encrypt data using AES
def encrypt_data(data, key):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return cipher.nonce, tag, ciphertext

# Decrypt data using AES
def decrypt_data(nonce, tag, ciphertext, key):
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext

def record_audio(filename, record_seconds):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
    frames = []
    print("Recording...")
    for i in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Finished recording.")
    
    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def play_audio(filename):
    wf = wave.open(filename, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    print("Playing audio...")
    data = wf.readframes(CHUNK)
    while data:
        stream.write(data)
        data = wf.readframes(CHUNK)
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Audio playback finished.")

def receive_and_play(client):
    response_data = b""
    try:
        client.settimeout(5)  # Set a timeout of 5 seconds
        while True:
            chunk = client.recv(1024)
            if not chunk:
                break
            response_data += chunk
    except socket.timeout:
        print("Timeout occurred. No more data to receive.")
    
    with open(OUTPUT_FILENAME, 'wb') as f:
        f.write(response_data)
    print("Response message received from server.")

    # Decrypt the received message
    key = generate_key("your_password")  # Use the same password as used for encryption
    with open(OUTPUT_FILENAME, 'rb') as f:
        encrypted_data = f.read()
    nonce = encrypted_data[:16]  # Nonce size for AES is 16 bytes
    tag = encrypted_data[16:32]  # Tag size for AES is 16 bytes
    ciphertext = encrypted_data[32:]
    decrypted_data = decrypt_data(nonce, tag, ciphertext, key)

    # Write the decrypted audio to a file
    with open("decrypted_audio.wav", 'wb') as f:
        f.write(decrypted_data)

    # Play the decrypted audio file
    play_audio("decrypted_audio.wav")

def send_response(client):
     key = generate_key("your_password")  # Use the same password as used for encryption
     with open(INPUT_FILENAME, 'rb') as f:
         audio_data = f.read()
         nonce, tag, ciphertext = encrypt_data(audio_data, key)
         encrypted_response = nonce + tag + ciphertext
        
        # Send the encrypted response message to the client
     with open(INPUT_FILENAME, 'wb') as f:
         f.write(encrypted_response)
    # Send the response message to the server
     with open(INPUT_FILENAME, 'rb') as f:
         response_data = f.read()
         print("Sending response message...")
         client.sendall(response_data)
         print("Response message sent to server.")

def perform_action(choice, client, record_seconds=None):
    if choice == "Record Audio":
        record_audio(INPUT_FILENAME, record_seconds)
        print("Response recorded.")
    elif choice == "Send":
        send_response(client)
    elif choice == "Receive and Play Audio":
        receive_and_play(client)

def on_action_button_click(selected_choice):
    # selected_choice = choice_var.get()
    # client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # client.connect((SERVER_IP, PORT))
    # server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server.bind((SERVER_IP, PORT))
    # server.listen(1)
    # print("Server is listening...")

    #client, addr = server.accept()
    #client.settimeout(10)  # Set a timeout of 10 seconds
    print("Connection from", addr)
    if selected_choice == "Record Audio":
        record_seconds = int(record_seconds_var.get())
        perform_action(selected_choice, client, record_seconds)
    else:
        perform_action(selected_choice, client)
   # client.close()
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((SERVER_IP, PORT))
server.listen(1)
print("Server is listening...")

client, addr = server.accept()
client.settimeout(10)  # Set a timeout of 10 seconds
# Create GUI
root = tk.Tk()
root.title("Audio Communication Server")

# Record Seconds Slider
record_seconds_var = tk.StringVar()
record_seconds_label = tk.Label(root, text="Record Seconds:")
record_seconds_label.pack()
record_seconds_slider = tk.Scale(root, from_=1, to=30, orient=tk.HORIZONTAL, variable=record_seconds_var)
record_seconds_slider.pack()

# Action Choice
choice_var = tk.StringVar()
choice_var.set("Record Audio")
action_label = tk.Label(root, text="Choose Action:")
action_label.pack()
record_radio = tk.Radiobutton(root, text="Record Audio", variable=choice_var, value="Record Audio")
record_radio.pack(anchor=tk.W)
send_radio = tk.Radiobutton(root, text="Send", variable=choice_var, value="Send")
send_radio.pack(anchor=tk.W)
receive_radio = tk.Radiobutton(root, text="Receive and Play Audio", variable=choice_var, value="Receive and Play Audio")
receive_radio.pack(anchor=tk.W)

# Action Button
action_button = tk.Button(root, text="Perform Action", command=lambda: on_action_button_click(choice_var.get()))
action_button.pack()

root.mainloop()

client.close()
server.close()
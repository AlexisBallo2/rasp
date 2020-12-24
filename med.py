import os
import time
from twilio.rest import Client
import pyaudio
import wave
import numpy


# Your Account Sid and Auth Token from twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = 'ACa9a1bd66eb0ce4a1ea81eec84069318c'
auth_token = 'bf1055b0719b90937a656806e93fbb3b'
client = Client(account_sid, auth_token)


system_command = 'ls' # passed to os.system() on audio trigger
threshold = 0.03 # volume threshold to trigger at, 0 is nothing 1 is max volume
min_delay = 1 # min seconds between attempts
last_run = 0 # helper for min_delay behavior

audio_sample_rate = 48e3
audio_frame_samples = 1024*7

left_channel = 1
right_channel = 1

def audio_data():
  try:
    _ = audio_data.stream
  except AttributeError:
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=2,
                     rate=int(audio_sample_rate),
                     input=True,
                     frames_per_buffer=audio_frame_samples)
    audio_data.stream = stream

  # When reading from our 16-bit stereo stream, we receive 4 characters (0-255) per
  # sample. To get them in a more convenient form, numpy provides
  # fromstring() which will for each 16 bits convert it into a nicer form and
  # turn the string into an array.
  raw_data = audio_data.stream.read(audio_frame_samples) # always read a whole buffer.
  samples  = numpy.fromstring(raw_data, dtype=numpy.int16)
  # Normalize by int16 max (32767) for convenience, also converts everything to floats
  normed_samples = samples / float(numpy.iinfo(numpy.int16).max)
  # split out the left and right channels to return separately.
  # audio data is stored [left-val1, right-val1, left-val2, right-val2, ...]
  # so just need to partition it out.
  left_samples = normed_samples[left_channel::2]
  right_samples = normed_samples[right_channel::2]
  return left_samples, right_samples

audio_data() # toss out first read
while True:
  left,right = audio_data() #add left,right
  if max(left) > threshold and time.time() - last_run > min_delay:
    print('audio:', max(left))

    form_1 = pyaudio.paInt16 # 16-bit resolution
    chans = 1 # 1 channel
    samp_rate = 44100 # 44.1kHz sampling rate
    chunk = 4096 # 2^12 samples for buffer
    record_secs = 5 # seconds to record
    dev_index = 2 # device index found by p.get_device_info_by_index(ii)
    wav_output_filename = 'sound.wav' # name of .wav file

    audio = pyaudio.PyAudio() # create pyaudio instantiation

    # create pyaudio stream
    stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index,input = True, \
                        frames_per_buffer=chunk)
    print("recording")
    frames = []

    # loop through stream and append audio chunks to frame array
    for ii in range(0,int((samp_rate/chunk)*record_secs)):
        data = stream.read(chunk)
        frames.append(data)

    print("finished recording")

    # stop the stream, close it, and terminate the pyaudio instantiation
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # save the audio frames as .wav file
    wavefile = wave.open(wav_output_filename,'wb')
    wavefile.setnchannels(chans)
    wavefile.setsampwidth(audio.get_sample_size(form_1))
    wavefile.setframerate(samp_rate)
    wavefile.writeframes(b''.join(frames))
    wavefile.close()

    message = client.messages.create(
         from_='+14432470186',
         to='+14434017876',
         media_url =['http://c118666e687e.ngrok.io/wav'],
     )

    print(message.sid)


    #Client("").send_message(str(max(right)), "audio test", "gs2817", "1", "4", "2", "https://www.pushsafer.com", "Open Pushsafer", "0", "2", "60", "600", "1", "", "", "")
    last_run = time.time()


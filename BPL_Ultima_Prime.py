
import traceback
import socket
import time
import threading
import requests
import datetime
import sys


UDP_IP = "192.168.1.46"  # Replace with your desired IP address
UDP_PORT = 8001  # Replace with your desired port number


observations = []
SP02_WAVE = []
RESPIRATION_WAVE = []
ECG_WAVE = []
PATIENT_ID = sys.argv[1]
PATIENT_NAME = sys.argv[2]
DEVICE_ID = sys.argv[3]
middleware_URL = sys.argv[4]
data_from_loop1 = []

ECG_3Lead_array = []
ECG_5Leads_array = []
SP02_array = []
RESP_array = []
SPO2_pulse_array = []
Temp_wave_1 = []
Temp_wave_2 = []
NIBP_array = []
dataQueue = []
dataIncoming = False


# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 128)  # or 256

# Bind socket to a local port and address
sock.bind(('', 8001))


def create_observation(observation_id, status, value, unit, interpretation, low_limit, high_limit):
    global PATIENT_ID
    global PATIENT_NAME
    global DEVICE_ID
    # Get the current date and time
    date_time = datetime.datetime.now().strftime("%H:%M:%S")
    # Create the observation dictionary
    observation = {
        "observation_id": observation_id,
        "device_id": DEVICE_ID,
        "date-time": date_time,
        "patient-id": PATIENT_ID,
        "patient-name": PATIENT_NAME,
        "status": status,
        "value": value,
        "unit": unit,
        "interpretation": interpretation,
        "low-limit": low_limit,
        "high-limit": high_limit
    }
    return observation


def generate_waveform_data(observation_id,  wave_name, resolution,
                           sampling_rate, data_baseline, data_low_limit, data_high_limit, data):
    global PATIENT_ID
    global PATIENT_NAME
    global DEVICE_ID
    date_time_wf = datetime.datetime.now().strftime("%H:%M:%S")
    Str_data = " ".join(str(value) for value in data)
    waveform_data = {
        "observation_id": observation_id,
        "device_id": DEVICE_ID,
        "date-time": date_time_wf,
        "patient-id": PATIENT_ID,
        "patient-name": PATIENT_NAME,
        "wave-name": wave_name,
        "resolution": resolution,
        "sampling rate": sampling_rate,
        "data-baseline": data_baseline,
        "data-low-limit": data_low_limit,
        "data-high-limit": data_high_limit,
        "data": Str_data
    }
    return waveform_data


def generate_blood_pressure_observation(sys_value, dia_value, map_value):
    current_datetime = datetime.datetime.now().strftime("%H:%M:%S")
    global PATIENT_ID
    global PATIENT_NAME
    global DEVICE_ID

    nibp_observation = {
        "observation_id": "blood-pressure",
        "device_id": DEVICE_ID,
        "date-time": current_datetime,
        "patient-id": PATIENT_ID,
        "patient-name": PATIENT_NAME,
        "status": "final",
        "systolic": {
            "value": sys_value,
            "unit": "mmHg",
            "interpretation": "normal",
            "Low-limit": 100,
            "high-limit": 160
        },
        "diastolic": {
            "value": dia_value,
            "unit": "mmHg",
            "interpretation": "normal",
            "low-limit": 60,
            "high-limit": 100
        },
        "map": {
            "value": map_value,
            "unit": "mmHg",
            "interpretation": "normal",
            "low-limit": 70,
            "high-limit": 120
        }
    }

    return nibp_observation


def ECG_5Leads(ECG_5Leads_array):
    ecg_hr1 = ECG_5Leads_array[3]
    ecg_hr2 = ECG_5Leads_array[4]
    collective_binary_ecg_hr = (
        (ecg_hr2 & 0b00000001) << 8) | ecg_hr1
    # Prints: 0b101011101
    bin_ecg_hr = bin(collective_binary_ecg_hr)
    dec_ecg_hr = int(bin_ecg_hr, 2)
    if (((ECG_5Leads_array[20] >> 4) & 0b00000001) != 0b00000001) and dec_ecg_hr != 488:
        print("\nECG PULSE BPM : " + str(dec_ecg_hr))
        observation_ecg_hr = create_observation(
            observation_id="heart-rate",
            status="Message-Leads Off",
            value=dec_ecg_hr,
            unit="bpm",
            interpretation="NA",
            low_limit=40,
            high_limit=120
        )
        observations.append(observation_ecg_hr)
    else:
        print(
            "\nECG PULSE BPM : Nil [ECG Probe Not Connected]")

    ECG_waveform = ECG_5Leads_array[24:]
    print("ECG Waveform ")
    ECG_Lead_two = []
    for i in range(0, len(ECG_waveform), 7):
        ECG_Lead_two.extend(ECG_waveform[i:i+2])

    binary_array = []

    for num in ECG_Lead_two:
        # Convert each element to binary representation with 8 digits
        binary = bin(num)[2:].zfill(8)
        binary_array.append(binary)

    joined_array = []

    for i in range(0, len(binary_array), 2):
        binary_1 = binary_array[i]
        binary_2 = binary_array[i + 1]
        # Join last 5 bits of binary_1 with first 7 bits of binary_2
        joined_binary = binary_1[-5:] + binary_2[:7]
        joined_array.append(joined_binary)

    for binary in joined_array:
        decimal = int(binary, 2)  # Convert binary to decimal
        ECG_WAVE.append(4096-(decimal))


def ECG_3Leads(ECG_3Lead_array):
    ecg_hr1 = ECG_3Lead_array[3]
    ecg_hr2 = ECG_3Lead_array[4]
    collective_binary_ecg_hr = (
        (ecg_hr2 & 0b00000001) << 8) | ecg_hr1
    bin_ecg_hr = bin(collective_binary_ecg_hr)
    dec_ecg_hr = int(bin_ecg_hr, 2)
    if (((ECG_3Lead_array[8] >> 4) & 0b00000001) != 0b00000001) and dec_ecg_hr != 488:
        print("\nECG PULSE BPM : " + str(dec_ecg_hr))
        observation_ecg_hr = create_observation(
            observation_id="heart-rate",
            status="Message-Leads Off",
            value=dec_ecg_hr,
            unit="bpm",
            interpretation="NA",
            low_limit=40,
            high_limit=120
        )
        observations.append(observation_ecg_hr)
    else:
        print(
            "\nECG PULSE BPM : Nil [ECG Probe Not Connected]")

    ECG_waveform = ECG_3Lead_array[10:]
    print("ECG Waveform ")

    ECG_Lead_two = []
    for i in range(0, len(ECG_waveform), 3):
        ECG_Lead_two.extend(ECG_waveform[i:i+2])

    binary_array = []

    for num in ECG_Lead_two:
        # Convert each element to binary representation with 8 digits
        binary = bin(num)[2:].zfill(8)
        binary_array.append(binary)

    # print(binary_array)
    joined_array = []

    for i in range(0, len(binary_array), 2):
        binary_1 = binary_array[i]
        binary_2 = binary_array[i + 1]
        # Join last 5 bits of binary_1 with first 7 bits of binary_2
        joined_binary = binary_1[-5:] + binary_2[:7]
        joined_array.append(joined_binary)

    for binary in joined_array:
        decimal = int(binary, 2)  # Convert binary to decimal
        ECG_WAVE.append(4096-(decimal))


def SPO2(SPO2_array):
    SpO2_Value = (SPO2_array[4])
    if (50 <= SpO2_Value <= 100):
        print("\nSPO2 %         : " + str(SpO2_Value))
    else:
        print(
            "\nSPO2 %        : Nil [SPO2 Probe Not Connected]")
    if (SpO2_Value > 100) or (SpO2_Value < 50):
        SpO2_Value = None
    else:
        SpO2_Value = SpO2_Value

    observation_spo2 = create_observation(
        observation_id="SpO2",
        status="Message-Leads Off",
        value=SpO2_Value,
        unit="%",
        interpretation=2,
        low_limit=90,
        high_limit=100
    )
    observations.append(observation_spo2)

    SPO2_WaveForm = SPO2_array[5:]
    print("SPO2_WaveForm : ")
    for i in range(int(len(SPO2_WaveForm)/2)):
        SP02_WAVE.append(128-(SPO2_WaveForm[i*2] & 0x7f))


def RESPIRATION_data(RESP_array):

    RR_value = RESP_array[3]
    if(RR_value != 0):
        print("\nRR             : " + str(RR_value))
    else:
        print(
            "\nRR            : Nil [ECG Probe Not Connected]\n")

    if(RR_value == 255):
        RR_value = 0
    else:
        RR_value = RR_value
    observation_Resp1 = create_observation(
        observation_id="respiratory-rate",
        status="Message-Leads Off",
        value=RR_value,
        unit="bpm",
        interpretation=4,
        low_limit=10,
        high_limit=30
    )
    observations.append(observation_Resp1)

    # rr waveform
    RR_WaveForm = RESP_array[7:]
    print("Respiration Rate Waveform ")
    alternate_elements = RR_WaveForm[::2]
    for i in alternate_elements:
        RESPIRATION_WAVE.append(i)


def SPO2_PULSE_data(SPO2_pulse_array):
    hr1 = SPO2_pulse_array[3]
    hr2 = SPO2_pulse_array[4]
    collective_binary = ((hr2 & 0b00000001) << 8) | hr1
    bin_hr = bin(collective_binary)  # Prints: 0b101011101
    dec_hr = int(bin_hr, 2)
    if ((hr2 >> 3) & 0b00000001 != 0b00000001) and dec_hr != 488:
        print("\nPULSE BPM       : " + str(dec_hr))
        observation_hr = create_observation(
            observation_id="pulse-rate",
            status="Message-Leads Off",
            value=dec_hr,
            unit="bpm",
            interpretation="normal",
            low_limit=40,
            high_limit=120
        )
        observations.append(observation_hr)
    else:
        print(
            "\nPULSE BPM     : Nil [SPO2 Probe Not Connected]")
        dec_hr = 0


def TEMPERATURE1_data(Temp_wave_1):

    if(Temp_wave_1[4] != (255)):
        T1temp8bits = Temp_wave_1[4]
        T1temp4bits = Temp_wave_1[5]
        collective_binary_temper_1 = (
            (T1temp4bits & 0b00001111) << 8) | T1temp8bits

        dec_Temp1 = collective_binary_temper_1/10
        print("\nTemperature_1 : " + str(dec_Temp1))
    else:
        dec_Temp1 = None
        print(
            "\nTemperature_1 : Nil [Probe Not Connected]")
    observation_temp1 = create_observation(
        observation_id="body-temperature1",
        status="Message-Leads Off",
        value=dec_Temp1,
        unit="C",
        interpretation=3,
        low_limit=36,
        high_limit=38
    )
    observations.append(observation_temp1)


def TEMPERATURE2_data(Temp_wave_2):
    if(Temp_wave_2[4] != (255)):
        T2temp8bits = Temp_wave_2[4]
        T2temp4bits = Temp_wave_2[5]
        collective_binary_temper_2 = (
            (T2temp4bits & 0b00001111) << 8) | T2temp8bits
        # bin_Temper2=bin(collective_binary_temper_2)
        # dec_Temp2=int(bin_Temper2,2)
        dec_Temp2 = collective_binary_temper_2/10
        print("\nTemperature_2 : " + str(dec_Temp2))
    else:
        dec_Temp2 = None
        print(
            "\nTemperature_2 : Nil [Probe Not Connected]")
    observation_temp2 = create_observation(
        observation_id="body-temperature2",
        status="Message-Leads Off",
        value=dec_Temp2,
        unit="C",
        interpretation=3,
        low_limit=36,
        high_limit=38
    )
    observations.append(observation_temp2)


def NIBP_data(NIBP_array):

    elements_to_print = NIBP_array[0:]
    if elements_to_print.count(251) > 1:
        elements_to_print = elements_to_print[8:]

    # for i in  elements_to_print:
    #     print(i)

    if len(elements_to_print) >= 6:
        SYS = elements_to_print[7]
        DIA = elements_to_print[8]
        MAP = elements_to_print[9]

    # nibp = str(SYS) + " / " + str(DIA)
        nibp = ""
        if (SYS is not None and DIA is not None and MAP is not None):
            nibp_result = generate_blood_pressure_observation(SYS, DIA, MAP)
            observations.append(nibp_result)


def loop1():
    global current_time
    global dataQueue
    global dataIncoming
    global nibp
    SYS = None
    DIA = None
    int_values = []
    index_fb = []
    last_incoming_time = 0

    while True:
        try:
            # current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")

            # data_deque=deque()
            # Check for incoming messages
            data, addr = sock.recvfrom(4096)
            # print("length dataaaaaaaaaaaaaa = " + str(sys.getsizeof(data)))
            int_values = [int(x) for x in data]

            # print("Message as list of integer values:" + str(int_values))

            if addr[0] == "192.168.1.190":
                message = b'\xff\xd0\x2E\xff\x00\x00\x00\x00\x00\x00\x00\x00'
                sock.sendto(message, ('192.168.1.255', 8001))
            if len(int_values) > 500:
                dataQueue.append(int_values)
                dataIncoming = True
                last_incoming_time = time.time()
            print(dataIncoming)
            print(last_incoming_time)
            if time.time()-last_incoming_time > 5:
                dataIncoming = False

            # Send periodic broadcast messages

            if not dataIncoming:

                message = b'\xff\xda\x2E\x05\x00\x02\x00\x01\x1f\x41'
                sock.sendto(message, ('192.168.1.190', 8001))

            # print("Current time Nibp:", current_time[:-3])

            time.sleep(.1)
        except Exception as e:
            print("Crash in Loop 1")
            traceback.print_exc()


def loop2():
    last_time = 0
    global dataQueue

    global observations
    global SPO2_WaveForm
    global RESPIRATION_WAVE
    global ECG_WAVE

    while True:
        try:

            # print(len(dataQueue))
            if len(dataQueue) > 0:
                print("-------------------------------------------------------")
                print(len(dataQueue))
                data_from_loop1 = dataQueue[0]
                # print(data_from_loop1)
                i = 8
                split_data = []
                while i < len(data_from_loop1)-2:
                    a = data_from_loop1[i+1]
                    b = data_from_loop1[i+2]
                    c = (a << 8) | b
                    split_data.append(data_from_loop1[i:(i+c)+3])
                    i = (i+c)+3
                print(split_data)

                for i in split_data:
                    if i[0] == 237:
                        ECG_5Leads(i)
                    elif i[0] == 238:
                        ECG_3Leads(i)
                    elif i[0] == 248:
                        RESPIRATION_data(i)
                    elif i[0] == 250:
                        SPO2(i)
                    elif i[0] == 193:
                        TEMPERATURE1_data(i)
                    elif i[0] == 194:
                        TEMPERATURE2_data(i)
                    elif i[0] == 251:
                        NIBP_data(i)
                    elif i[0] == 249:
                        SPO2_PULSE_data(i)

                dataQueue.pop(0)
            time.sleep(.1)
        except Exception as e:
            print("Crash in Loop 2")
            traceback.print_exc()


def loop3():
    global observations
    global SP02_WAVE
    global ECG_WAVE
    global RESPIRATION_WAVE
    global middleware_URL
    while True:
        try:
            if len(SP02_WAVE) > 180:
                print("Spo2_time : " + str(round(time.time() * 1000)) +
                      "  Length : " + str(len(SP02_WAVE)))
                spo2_waveform = generate_waveform_data(
                    "waveform", "Pleth", "NA", "96/sec", 0, 0, 150, SP02_WAVE)
                observations.append(spo2_waveform)

                SP02_WAVE.clear()
            if len(ECG_WAVE) > 480:
                ecg_waveform = generate_waveform_data(
                    "waveform", "II", "1.5uV", "248/sec", 2047, 0, 4095, ECG_WAVE)
                observations.append(ecg_waveform)
                ECG_WAVE.clear()
            if len(RESPIRATION_WAVE) > 180:
                # print(" RES_time : " + str(round(time.time() * 1000)) + "  Length : "  + str(len(RESPIRATION_WAVE)))
                respiration_waveform = generate_waveform_data(
                    "waveform", "Respiration", "NA", "99/sec", 0, 0, 255, RESPIRATION_WAVE)
                observations.append(respiration_waveform)
                # print(RESPIRATION_WAVE)
                RESPIRATION_WAVE.clear()
            array_of_observations = [observations]
            # Print the array of arrays of observations
            # print(array_of_observations)

            url = "http://" + str(middleware_URL)+"/update_observations"

            # json_data=json.dumps(array_of_observations)

            # Send the data as a POST request to the middleware endpoint
            # if(len(ECG_WAVE)>700 and len(SP02_WAVE)>280 and len(RESPIRATION_WAVE)>290):
            if len(observations) > 0:
                print("length of observations =  " + str(len(observations)))
                while len(observations) > 500:
                    del observations[0]
                response = requests.post(
                    url, json=array_of_observations, timeout=6)

                # # Check the response from the middleware
                if response.status_code == 200:
                    print('Data sent successfully')
                else:
                    print('Error sending data: ', response.status_code)

                    # print(array_of_observations)
                observations.clear()

            # print(array_of_observations)
            time.sleep(.1)
        except Exception as e:
            print("Crash in Loop 3")
            traceback.print_exc()


# Start the threads
thread1 = threading.Thread(target=loop1)
thread2 = threading.Thread(target=loop2)
thread3 = threading.Thread(target=loop3)
# thread4= threading.Thread(target=loop4)
thread1.start()
thread2.start()
thread3.start()
# thread4.start()


# Keep the main thread running

# Wait for the threads to finish
thread1.join()
thread2.join()
thread3.join()
# thread4.join()

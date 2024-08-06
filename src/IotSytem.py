import RPi.GPIO as GPIO
import Adafruit_DHT
import time
import paho.mqtt.client as mqtt
from cryptography.fernet import Fernet

# Configurer les GPIO pour les capteurs
PIR_PIN = 5
DHT_PIN = 4
FLAME_SENSOR_PIN = 26

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(FLAME_SENSOR_PIN, GPIO.IN)

DHT_SENSOR = Adafruit_DHT.DHT22

#key = Fernet.generate_key()
#print(key.decode())

# Use a previously generated key for encryption
encryption_key = b'FoksY1YDiuD4mwhfOk882_iMFHSXYGj6SX73gfJ5YUM='
cipher_suite = Fernet(encryption_key)

# Configuration MQTT
BROKER = 'test.mosquitto.org'
PORT = 1883
TOPIC_TEMP = 'iot_pfe/temp'
TOPIC_HUM = 'iot_pfe/hum'
TOPIC_FLAME = 'iot_pfe/flame_sensor'
TOPIC_MOTION = 'iot_pfe/motion_sensor'
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

client.on_connect = on_connect
client.connect(BROKER, PORT, 60)

def read_pir():
    """Lire l'état du capteur PIR"""
    return GPIO.input(PIR_PIN)

def read_dht22():
    """Lire les données de température et d'humidité du capteur DHT22"""
    humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
    if humidity is not None and temperature is not None:
        return temperature, humidity
    else:
        return None, None

def read_flame_sensor():
    """Lire l'état du capteur de flamme"""
    return GPIO.input(FLAME_SENSOR_PIN)

def encrypt_data(data):
    """Encrypt the data using Fernet"""
    return cipher_suite.encrypt(data.encode())

try:
    client.loop_start()  # Démarrer la boucle réseau en arrière-plan
    
    while True:
        # Lire les données du PIR
        pir_state = read_pir()
        print('motion state ==>',pir_state)
        if pir_state:
            pir_message = "Motion Detected!"
            
        else:
            pir_message = "No Motion"
        print(pir_message)
        encrypted_pir = encrypt_data(str(pir_state))        
        client.publish(TOPIC_MOTION, encrypted_pir)

        # Lire les données du DHT22
        temperature, humidity = read_dht22()
        if temperature is not None and humidity is not None:
            temp_message = f"{temperature:.1f}"
            hum_message = f"{humidity:.1f}"
            encrypted_temp = encrypt_data(temp_message)
            encrypted_hum = encrypt_data(hum_message)
            client.publish(TOPIC_TEMP, encrypted_temp)
            client.publish(TOPIC_HUM, encrypted_hum)            
        else:
            temp_message = "Failed to retrieve data from DHT22"
            hum_message = "Failed to retrieve data from DHT22"

        print(f"Temperature: {temp_message}C, Humidity: {hum_message}%")

         # Lire les données du capteur de flamme
        flame_state = read_flame_sensor()
        print('flamme state ==>',flame_state)
        if flame_state == 0:
            flame_message = "Flame Detected!"
            encrypted_flame = encrypt_data(str(1))
        else:
            flame_message = "No Flame"
            encrypted_flame = encrypt_data(str(0))
        print(flame_message)
        
        
        client.publish(TOPIC_FLAME, encrypted_flame)
        time.sleep(3)

except KeyboardInterrupt:
    print("Program terminated")
finally:
    GPIO.cleanup()
    client.loop_stop()  # Arrêter la boucle réseau en arrière-plan
    client.disconnect()
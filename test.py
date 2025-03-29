import requests

# Define API endpoint
url = "http://127.0.0.1:8000/admin/call/1002"  # Replace 1001 with an existing employee ID

# Open the audio file in binary mode
with open("test.wav", "rb") as audio_file:
    files = {"audio_file": ("test.wav", audio_file, "audio/wav")}
    data = {"duration": "4500"}  # Form-data field for duration (in seconds)

    # Send the request
    response = requests.post(url, files=files, data=data)

# Print the response
print(response.json())

import requests
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Status:
    status: str
    filename: str
    timestamp: datetime
    explanation: str

    def is_done(self):
        return self.status == 'done'


class WebAppClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def upload(self, file_path):
        url = f"{self.base_url}/upload"
        with open(file_path, 'rb') as file:
            response = requests.post(url, files={'file': file})

        if response.status_code == 200:
            json_data = response.json()
            return json_data['uid']
        else:
            raise Exception(f"Upload failed with status code {response.status_code}")

    def status(self, uid):
        url = f"{self.base_url}/status/{uid}"
        params = uid
        response = requests.get(url, params=params)

        if response.status_code == requests.codes.ok:
            json_data = response.json()
            status = json_data['status']
            filename = json_data['filename']
            timestamp = datetime.strptime(json_data['timestamp'], '%Y-%m-%d %H:%M:%S')
            explanation = json_data['explanation']
            return Status(status, filename, timestamp, explanation)
        else:
            raise Exception(f"Status retrieval failed with status code {response.status_code}")

    def run_client(self):
        print("Welcome to the Web App Client!")
        while True:
            print("\nSelect an option:")
            print("1. Upload file")
            print("2. Check status")
            print("0. Exit")
            choice = input("Enter your choice: ")

            if choice == '1':
                file_path = WebAppClient.select_file()
                if file_path:
                    try:
                        uid = self.upload(file_path)
                        print(f"File uploaded successfully. UID: {uid}")
                    except Exception as e:
                        print(f"Upload failed: {str(e)}")
            elif choice == '2':
                uid = input("Enter the UID: ")
                try:
                    status = self.status(uid)
                    print(f"Status: {status.status}")
                    print(f"Filename: {status.filename}")
                    print(f"Timestamp: {status.timestamp}")
                    print(f"Explanation: {status.explanation}")
                except Exception as e:
                    print(f"Status retrieval failed: {str(e)}")
            elif choice == '0':
                break
            else:
                print("Invalid choice. Please try again.")

    @staticmethod
    def select_file():
        try:
            from tkinter import Tk
            from tkinter.filedialog import askopenfilename
        except ImportError:
            print("File selection requires Tkinter. Make sure Tkinter is installed.")
            return None

        root = Tk()
        root.withdraw()
        file_path = askopenfilename()
        return file_path


if __name__ == '__main__':
    client = WebAppClient('http://127.0.0.1:5000')
    client.run_client()

from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 

import os
import sys
import json
import asyncio
import requests
import websockets
import simpleobsws

from datetime import date
from threading import Thread
from websockets.exceptions import InvalidStatusCode

class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.obs_ws = None
        self.obs_ws_connected = False
        self.switcher_thread = None
        self.switcher_running = False

        self.asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.asyncio_loop)

        self.setWindowTitle("FTC Livestream Switcher")
        self.init()
        self.show()
  
    def init(self):
        layout = QGridLayout()
        layout.setColumnStretch(1, 4)

        self.scoring_url_textbox = QLineEdit()
        self.scoring_url_textbox.setPlaceholderText('ex: 10.5.29.200')

        self.obs_url_textbox = QLineEdit()
        self.obs_url_textbox.setText('localhost')
        self.obs_port_textbox = QSpinBox()
        self.obs_port_textbox.setMinimum(1)
        self.obs_port_textbox.setMaximum(65535)
        self.obs_port_textbox.setValue(4444)
        self.obs_password_textbox = QLineEdit()
        self.obs_password_textbox.setPlaceholderText('optional')
        # self.obs_password_textbox.setEchoMode(QLineEdit.Password)

        self.get_scenes_button = QPushButton('Refresh Scenes')
        self.get_scenes_button.clicked.connect(self.get_scenes_onclick)
        self.obs_field_1_scene_combobox = QComboBox()
        self.obs_field_1_scene_combobox.setEnabled(False)
        self.obs_field_2_scene_combobox = QComboBox()
        self.obs_field_2_scene_combobox.setEnabled(False)

        self.get_events_button = QPushButton('Refresh Events')
        self.get_events_button.clicked.connect(self.get_events_onclick)
        self.events_combobox = QComboBox()
        self.events_combobox.setEnabled(False)

        self.select_recording_folder_button = QPushButton('Recording Folder')
        self.select_recording_folder_button.clicked.connect(self.select_recording_folder_onclick)
        self.recording_folder_textbox = QLabel()
        self.recording_folder_textbox.setText('Use OBS value')

        self.start_switcher_button = QPushButton('Start Switcher')
        self.start_switcher_button.clicked.connect(self.start_switcher_onclick)

        layout.addWidget(QLabel('OBS URL'), 0, 0)
        layout.addWidget(self.obs_url_textbox, 0, 1)
        layout.addWidget(QLabel('OBS Port'), 1, 0)
        layout.addWidget(self.obs_port_textbox, 1, 1)
        layout.addWidget(QLabel('OBS Password'), 2, 0)
        layout.addWidget(self.obs_password_textbox, 2, 1)
        layout.addWidget(self.get_scenes_button, 3, 0, 1, 2)
        layout.addWidget(QLabel('Field 1 Scene'), 4, 0)
        layout.addWidget(self.obs_field_1_scene_combobox, 4, 1)
        layout.addWidget(QLabel('Field 2 Scene'), 5, 0)
        layout.addWidget(self.obs_field_2_scene_combobox, 5, 1)

        layout.addWidget(QLabel('FTC Scoring URL'), 6, 0)
        layout.addWidget(self.scoring_url_textbox, 6, 1)
        layout.addWidget(self.get_events_button, 7, 0)
        layout.addWidget(self.events_combobox, 7, 1)

        # set recording path not supported by obswebsockets
        # layout.addWidget(self.select_recording_folder_button, 8, 0)
        # layout.addWidget(self.recording_folder_textbox, 8, 1)
        
        layout.addWidget(self.start_switcher_button, 8, 0, 1, 2)
    
        self.setLayout(layout)

    def get_scoring_url(self):
        return 'http://' + self.scoring_url_textbox.text()
    
    def get_events_from_scorekeeper(self):
        endpoint = self.get_scoring_url() + '/api/v1/events/'
        response = requests.get(endpoint).json()
        return response['eventCodes']

    def show_error(self, message: str):
        msgBox = QMessageBox()
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.Ok)
        return msgBox.exec()

    def get_events_onclick(self):
        try:
            events = self.get_events_from_scorekeeper()
        except requests.exceptions.InvalidURL:
            self.events_combobox.setEnabled(False)
            self.events_combobox.clear()
            self.show_error('Could not connect to the scorekeeper.')
            return

        self.events_combobox.setEnabled(True)
        self.events_combobox.clear()
        self.events_combobox.addItems(events)
    
    def get_obs_ws_url(self):
        return 'ws://' + self.obs_url_textbox.text() + ':' + self.obs_port_textbox.text()
    
    def get_obs_ws_pw(self):
        return self.obs_password_textbox.text()

    async def connect_obs(self):
        if self.obs_ws_connected:
            return True

        self.obs_ws = simpleobsws.WebSocketClient(url=self.get_obs_ws_url(), password=self.get_obs_ws_pw())
        try:
            connected = await self.obs_ws.connect()
            identified = await self.obs_ws.wait_until_identified(timeout=1)
            if not identified:
                self.show_error('Could not authenticate with OBS')
            else:
                self.obs_ws_connected = True
                return self.obs_ws_connected
        except InvalidStatusCode as e:
            self.show_error('Could not connect to OBS, reason ' + str(e.status_code))
        return self.obs_ws_connected
    
    def connect_obs_proxy(self):
        return self.asyncio_loop.run_until_complete(self.connect_obs())
    
    async def get_obs_scenes(self):
        request = simpleobsws.Request('GetSceneList')
        response = await self.obs_ws.call(request, timeout=5)
        if response.ok():
            return [s['sceneName'] for s in response.responseData['scenes']]
        return []

    def get_scenes_onclick(self):
        if not self.connect_obs_proxy():
            return
        
        scenes = self.asyncio_loop.run_until_complete(self.get_obs_scenes())
        scenes.sort()
        if len(scenes) < 1:
            return
        
        self.obs_field_1_scene_combobox.clear()
        self.obs_field_2_scene_combobox.clear()
        self.obs_field_1_scene_combobox.setEnabled(True)
        self.obs_field_1_scene_combobox.addItems(scenes)
        self.obs_field_2_scene_combobox.setEnabled(True)
        self.obs_field_2_scene_combobox.addItems(scenes)
        
    def select_recording_folder_onclick(self):
        folderpath = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folderpath == '':
            return
        
        self.recording_folder_textbox.setText(folderpath)
    
    async def set_recording_folder_obs(self):
        request = simpleobsws.Request('GetSceneList')
        response = await self.obs_ws.call(request, timeout=5)
        if response.ok():
            return [s['sceneName'] for s in response.responseData['scenes']]
        return []

    async def start_switcher(self):
        scoring_url = self.scoring_url_textbox.text()
        scoring_event = self.events_combobox.currentText()
        field_1_scene = self.obs_field_1_scene_combobox.currentText()
        field_2_scene = self.obs_field_2_scene_combobox.currentText()

        async with websockets.connect('ws://' + scoring_url + '/api/v2/stream/?code=' + scoring_event) as scoring_ws:
            while self.switcher_running:
                try:
                    response = await asyncio.wait_for(scoring_ws.recv(), 0.5)
                    scoring_response = json.loads(response)
                except asyncio.exceptions.TimeoutError:
                    continue
                
                print('Received response of type', scoring_response['updateType'])
                if scoring_response['updateType'] == 'MATCH_LOAD':
                    # set filename -- obs websocket is missing this endpoint now?
                    # filename = "%YY-%MM-%DD " + scoring_event + " " + scoring_response['payload']['shortName']
                    # data = {"filenameFormat": filename}
                    # request = simpleobsws.Request('SetFilenameFormat', data)
                    # result = await self.obs_ws.call(request)
                    # print(result)

                    # set scene in obs
                    field = field_1_scene if scoring_response['payload']['field'] == 1 else field_2_scene
                    data = {"sceneName": field}
                    request = simpleobsws.Request('SetCurrentProgramScene', data)
                    result = await self.obs_ws.call(request)
                    print(result)

                elif scoring_response['updateType'] == 'MATCH_START':
                    if scoring_response['payload']['shortName'][0] == 'T':
                        print("Test match detected; ignoring")
                        continue
                    # set filename -- obs websocket is missing this endpoint now?
                    # filename = "%YY-%MM-%DD " + scoring_event + " " + scoring_response['payload']['shortName']
                    # data = {"filenameFormat": filename}
                    # request = simpleobsws.Request('SetFilenameFormat', data)
                    # result = await self.obs_ws.call(request)
                    # print(result)

                    # set scene in obs
                    field = field_1_scene if scoring_response['payload']['field'] == 1 else field_2_scene
                    data = {"sceneName": field}
                    request = simpleobsws.Request('SetCurrentProgramScene', data)
                    result = await self.obs_ws.call(request)
                    print(result)

                    # start recording
                    request = simpleobsws.Request('StartRecord')
                    try:
                        result = await self.obs_ws.call(request)
                    except Exception as e:
                        print(e)
                    print(result)
                
                elif scoring_response['updateType'] == 'MATCH_POST' or scoring_response['updateType'] == 'MATCH_ABORT':
                    if scoring_response['payload']['shortName'][0] == 'T':
                        print("Test match detected; ignoring")
                        continue
                    
                    await asyncio.sleep(5)
                    request = simpleobsws.Request('StopRecord')
                    result = await self.obs_ws.call(request)

                    filename = "{} {} {}.mkv".format(date.today().strftime('%Y-%m-%d'), scoring_event, scoring_response['payload']['shortName'])
                    dirname = os.path.dirname(result.responseData['outputPath'])
                    os.rename(result.responseData['outputPath'], dirname + '/' + filename)
                    print(result)

    def start_switcher_proxy(self):
        self.switcher_task = self.asyncio_loop.create_task(self.start_switcher())
        if not self.asyncio_loop.is_running():
            self.asyncio_loop.run_forever()

    def start_switcher_onclick(self):
        # previous switcher running; cancel it
        if self.switcher_running:
            self.asyncio_loop.stop()
            self.switcher_task.cancel()
            self.switcher_running = False
            self.start_switcher_button.setText('Start Switcher')
            return

        if not self.connect_obs_proxy():
            return
        
        error_msg = None
        if self.obs_field_1_scene_combobox.currentText() == '':
            error_msg = 'Select a scene for Field 1'
        elif self.obs_field_2_scene_combobox.currentText() == '':
            error_msg = 'Select a scene for Field 2'
        elif self.events_combobox.currentText() == '':
            error_msg = 'Select an event code'
        
        if error_msg is not None:
            self.show_error(error_msg)
            return

        self.start_switcher_button.setText('Stop Switcher')
        self.switcher_running = True
        self.switcher_thread = Thread(target=self.start_switcher_proxy, daemon=True)
        self.switcher_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec())
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtGui import QPixmap, QImage, QImageReader
import sys
import cv2
from detect import detect_vehicles  # Import the updated detect_vehicles function

class TrafficLightControl(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.vehicle_count = 0
        self.mode = "Automatic"
        self.start_time = QTime.currentTime()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_from_camera)
        self.timer.start(1000)  # Update every second

    def initUI(self):
        layout = QVBoxLayout()

        # Create a QLabel to display the camera feed
        self.camera_label = QLabel(self)
        self.camera_label.setFixedSize(640, 480)
        layout.addWidget(self.camera_label)

        # Create a QLabel to display the four-way traffic signal image
        self.signal_image_label = QLabel(self)
        self.signal_image_label.setPixmap(QPixmap('traffic_signal.png'))  # Update with your image path
        layout.addWidget(self.signal_image_label)

        self.mode_label = QLabel('Mode: Automatic', self)
        layout.addWidget(self.mode_label)

        self.vehicle_count_label = QLabel('Vehicle Count: 0', self)
        layout.addWidget(self.vehicle_count_label)

        self.timer_label = QLabel('Elapsed Time: 0:00:00', self)
        layout.addWidget(self.timer_label)

        self.auto_mode_btn = QPushButton('Automatic Mode', self)
        self.auto_mode_btn.clicked.connect(self.set_auto_mode)
        layout.addWidget(self.auto_mode_btn)

        self.manual_mode_btn = QPushButton('Manual Mode', self)
        self.manual_mode_btn.clicked.connect(self.set_manual_mode)
        layout.addWidget(self.manual_mode_btn)

        self.update_signal_btn = QPushButton('Update Signal', self)
        self.update_signal_btn.clicked.connect(self.update_signal)
        layout.addWidget(self.update_signal_btn)

        self.setLayout(layout)
        self.setWindowTitle('Traffic Light Control')
        self.setGeometry(100, 100, 800, 600)

    def set_auto_mode(self):
        self.mode = "Automatic"
        self.mode_label.setText(f"Mode: {self.mode}")

    def set_manual_mode(self):
        self.mode = "Manual"
        self.mode_label.setText(f"Mode: {self.mode}")

    def update_signal(self):
        if self.mode == "Automatic":
            if self.vehicle_count > 10:
                self.show_message("Longer green light for high vehicle count.")
                # Update the traffic signal image based on your logic
                self.signal_image_label.setPixmap(QPixmap('traffic_signal_high.png'))  # Update with your image path
            else:
                self.show_message("Shorter green light for low vehicle count.")
                # Update the traffic signal image based on your logic
                self.signal_image_label.setPixmap(QPixmap('traffic_signal_low.png'))  # Update with your image path
        else:
            self.show_message("Manual mode: Traffic light can be changed manually.")
            # Update the traffic signal image based on your logic
            self.signal_image_label.setPixmap(QPixmap('traffic_signal_manual.png'))  # Update with your image path

    def show_message(self, message):
        QMessageBox.information(self, "Signal Update", message)

    def update_from_camera(self):
        # Capture video frame
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            frame, self.vehicle_count = detect_vehicles(frame)
            # Convert frame to QImage
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
            self.camera_label.setPixmap(QPixmap.fromImage(q_image))
            cap.release()

        # Update the elapsed time
        elapsed_time = self.start_time.elapsed() / 1000  # Elapsed time in seconds
        minutes, seconds = divmod(elapsed_time, 60)
        hours, minutes = divmod(minutes, 60)
        self.timer_label.setText(f"Elapsed Time: {int(hours)}:{int(minutes):02}:{int(seconds):02}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TrafficLightControl()
    window.show()
    sys.exit(app.exec_())

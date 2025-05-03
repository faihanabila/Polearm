import cv2
import csv
import os
from datetime import datetime
from pyzbar import pyzbar
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class BarcodeDetector:
    def __init__(self):
        self.detected_barcodes = set()

    def process_frame(self, frame):
        img = frame.copy()
        barcodes = pyzbar.decode(img)
        detected = []

        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            barcode_type = barcode.type
            barcode_text = f"{barcode_data} ({barcode_type})"

            self._annotate_frame(img, barcode, barcode_text)

            if (barcode_data, barcode_type) not in self.detected_barcodes:
                self.detected_barcodes.add((barcode_data, barcode_type))
                detected.append((barcode_data, barcode_type))

        return img, detected

    def _annotate_frame(self, img, barcode, text):
        (x, y, w, h) = barcode.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

class WebcamBarcodeNode(Node):
    def __init__(self):
        super().__init__('webcam_barcode_node')
        self.get_logger().info("Starting webcam barcode node...")

        # --- SETTING KAMERA ---
        self.cap1 = cv2.VideoCapture(2)  # Ganti sesuai /dev/videoX
        self.cap2 = cv2.VideoCapture(4)

        if not self.cap1.isOpened() or not self.cap2.isOpened():
            self.get_logger().error("ERROR: Tidak dapat membuka salah satu kamera!")
            return

        self.detector = BarcodeDetector()

        # --- PUBLISHER ROS 2 ---
        self.publisher_1 = self.create_publisher(String, 'barcode_data_cam1', 10)
        self.publisher_2 = self.create_publisher(String, 'barcode_data_cam2', 10)

        # --- FILE CSV OUTPUT ---
        results_dir = os.path.expanduser("~/polearm/src/barcode_detection/barcode_detection/results")
        os.makedirs(results_dir, exist_ok=True)
        self.csv_filename = os.path.join(results_dir, "barcode_results.csv")

        with open(self.csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Data', 'Type', 'Camera'])

    def run(self):
        while rclpy.ok():
            ret1, frame1 = self.cap1.read()
            ret2, frame2 = self.cap2.read()

            if not ret1 or not ret2:
                self.get_logger().error("ERROR: Gagal membaca frame dari kamera!")
                break

            annotated1, detected1 = self.detector.process_frame(frame1)
            cv2.imshow("Barcode Scanner Cam 1", annotated1)
            for data, btype in detected1:
                if (data, btype) not in self.detector.detected_barcodes:
                    self.publisher_1.publish(String(data=data))
                    self.save_to_csv(data, btype, "Cam1")

            annotated2, detected2 = self.detector.process_frame(frame2)
            cv2.imshow("Barcode Scanner Cam 2", annotated2)
            for data, btype in detected2:
                if (data, btype) not in self.detector.detected_barcodes:
                    self.publisher_2.publish(String(data=data))
                    self.save_to_csv(data, btype, "Cam2")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap1.release()
        self.cap2.release()
        cv2.destroyAllWindows()
        self.get_logger().info("Barcode scanner ditutup.")

    def save_to_csv(self, data, btype, camera):
        with open(self.csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now().isoformat(), data, btype, camera])

def main(args=None):
    rclpy.init(args=args)
    node = WebcamBarcodeNode()
    node.run()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

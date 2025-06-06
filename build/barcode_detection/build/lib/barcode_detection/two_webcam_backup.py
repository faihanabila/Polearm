import cv2
import csv
import os
from datetime import datetime
from pyzbar import pyzbar
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class BarcodeDetector:
    def __init__(self, logger):
        self.detected_barcodes = set()
        self.logger = logger

    def process_frame(self, frame):
        img = frame.copy()
        barcodes = pyzbar.decode(img)
        new_detections = []

        if not barcodes:
            cv2.putText(img, "Tidak ada barcode terdeteksi", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        for barcode in barcodes:
            data = barcode.data.decode("utf-8")
            btype = barcode.type
            key = (data, btype)

            if key not in self.detected_barcodes:
                self.detected_barcodes.add(key)
                text = f"{data} ({btype})"
                color = (0, 255, 0)
                new_detections.append((data, btype))
                self.logger.info(f"[NEW] {text}")
            else:
                text = "Barcode telah terdeteksi"
                color = (100, 100, 100)

            self._annotate_frame(img, barcode, text, color)

        return img, new_detections

    def _annotate_frame(self, img, barcode, text, color):
        (x, y, w, h) = barcode.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        cv2.putText(img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)


class WebcamBarcodeNode(Node):
    def __init__(self):
        super().__init__('webcam_barcode_node')
        self.get_logger().info("Memulai node barcode webcam...")

        self.cap1 = cv2.VideoCapture(2)
        self.cap2 = cv2.VideoCapture(4)

        if not self.cap1.isOpened() or not self.cap2.isOpened():
            self.get_logger().error("ERROR: Tidak dapat membuka salah satu kamera!")
            return

        self.detector = BarcodeDetector(self.get_logger())

        self.publisher_1 = self.create_publisher(String, 'barcode_data_cam1', 10)
        self.publisher_2 = self.create_publisher(String, 'barcode_data_cam2', 10)

        results_dir = os.path.expanduser("~/polearm/src/barcode_detection/barcode_detection/results")
        os.makedirs(results_dir, exist_ok=True)
        self.csv_filename = os.path.join(results_dir, "barcode_results.csv")

        self.csv_file = open(self.csv_filename, mode='a', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)

        if os.stat(self.csv_filename).st_size == 0:
            self.csv_writer.writerow(['Timestamp', 'Data', 'Type', 'Camera'])

    def run(self):
        while rclpy.ok():
            ret1, frame1 = self.cap1.read()
            ret2, frame2 = self.cap2.read()

            if not ret1 or not ret2:
                self.get_logger().error("ERROR: Gagal membaca frame dari kamera!")
                break

            # Kamera 1
            annotated1, detected1 = self.detector.process_frame(frame1)
            cv2.imshow("Barcode Scanner Cam 1", annotated1)
            for data, btype in detected1:
                self.publisher_1.publish(String(data=data))
                self.save_to_csv(data, btype, "Cam1")

            # Kamera 2
            annotated2, detected2 = self.detector.process_frame(frame2)
            cv2.imshow("Barcode Scanner Cam 2", annotated2)
            for data, btype in detected2:
                self.publisher_2.publish(String(data=data))
                self.save_to_csv(data, btype, "Cam2")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cleanup()

    def save_to_csv(self, data, btype, camera):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # TANPA milidetik
        row = [timestamp, data, btype, camera]
        self.csv_writer.writerow(row)
        self.csv_file.flush()
        self.get_logger().info(f"[CSV] {row}")

    def cleanup(self):
        self.cap1.release()
        self.cap2.release()
        cv2.destroyAllWindows()
        self.csv_file.close()
        self.get_logger().info("Barcode scanner ditutup.")


def main(args=None):
    rclpy.init(args=args)
    node = WebcamBarcodeNode()
    node.run()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

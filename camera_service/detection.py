"""Live face detection preview (no identity recognition, recording, or network upload).

Uses OpenCV's bundled Haar cascade for a baseline detector. Production accuracy
requires independent evaluation and replacement with a modern detector.
"""
import argparse
import cv2

def main():
    parser = argparse.ArgumentParser(description="Local face detection preview")
    parser.add_argument("--source", default="0", help="Webcam index or RTSP stream")
    parser.add_argument("--scale", type=float, default=1.1)
    args = parser.parse_args()
    source = int(args.source) if args.source.isdigit() else args.source
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    if detector.empty():
        raise RuntimeError("OpenCV face detector could not be loaded")
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError("Camera unavailable")
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            boxes = detector.detectMultiScale(gray, scaleFactor=args.scale, minNeighbors=5, minSize=(55,55))
            for (x,y,w,h) in boxes:
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,200,255), 2)
            cv2.putText(frame, f"Faces: {len(boxes)} | detection only", (16,32),
                        cv2.FONT_HERSHEY_SIMPLEX, .7, (0,220,220), 2)
            cv2.imshow("Smart Gate - Face Detection (no recognition)", frame)
            if cv2.waitKey(1) & 0xff in (27,ord("q")):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

"""Local-only live camera preview. No recording, identity matching or uploads."""
import argparse
import cv2

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="0", help="Camera index or RTSP URL")
    args = parser.parse_args()
    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError("Camera unavailable. Check device permissions and source.")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            cv2.putText(frame, "LOCAL PREVIEW - NO RECORDING", (18, 32), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 220, 220), 2)
            cv2.imshow("University Smart Gate - Camera Preview", frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

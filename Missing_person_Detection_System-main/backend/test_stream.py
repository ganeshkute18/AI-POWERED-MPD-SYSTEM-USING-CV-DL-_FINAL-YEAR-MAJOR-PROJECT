"""
Quick test script to run real-time detection against a webcam and save one annotated frame.
Run with the project's venv python from the `backend` folder:

& .\venv\Scripts\Activate.ps1
python test_stream.py

Press 'q' to quit the live window. The script saves `test_output.jpg` when a match is found or after the run.
"""

import os
import time
import cv2
from realtime_detector import RealTimeDetector, VideoStreamProcessor

BACKEND_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BACKEND_DIR, 'best.pt')
EMB_FILE = os.path.join(BACKEND_DIR, 'stored_embeddings.json')

print(f"Test stream using model: {MODEL_PATH}")

def main():
    detector = RealTimeDetector(embeddings_file=EMB_FILE, threshold=0.55, frame_skip=1, model_path=MODEL_PATH)
    vsp = VideoStreamProcessor(detector)

    try:
        print("Opening webcam (0)...")
        vsp.open_camera(0, camera_name='webcam_test')
    except Exception as e:
        print(f"Failed to open camera: {e}")
        return

    frame_count = 0
    saved = False

    def callback(result, annotated):
        nonlocal frame_count, saved
        frame_count += 1

        # display
        try:
            cv2.imshow('test_stream', annotated)
        except Exception:
            pass

        # print matches if any
        if result.get('matches'):
            print(f"Matches at frame {frame_count}: {result['matches']}")
            if not saved:
                out_path = os.path.join(BACKEND_DIR, 'test_output.jpg')
                cv2.imwrite(out_path, annotated)
                print(f"Saved annotated frame to: {out_path}")
                saved = True

        # allow quick exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            vsp.stop()

        # stop after some frames
        if frame_count > 400:
            vsp.stop()

    try:
        print("Starting stream processing. Press 'q' to quit.")
        vsp.process_stream(callback)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        vsp.stop()
        cv2.destroyAllWindows()
        print("Test finished")

if __name__ == '__main__':
    main()

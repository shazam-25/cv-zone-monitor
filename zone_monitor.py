"""
Defines a polygonal zone in the center of the frame and checks if the
bottom-center anchor point of any detected person or object enters
that zone.
"""

# Import Libraries
import cv2
import numpy as np
from ultralytics import YOLO

# Load lightweight YOLOv8 nano model
try:
    model = YOLO("models/yolov8n.pt")
except Exception as exc:
    raise RuntimeError("Could not load the YOLO model.") from exc

# Open webcam (0) or replace with a path to an .mp4 file
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Could not open webcam. Check camera permissions or use a video file.")


# Define a polygon Region of Interest (ROI) [x, y] coordinates
# Adjust these points based on your camera resolution (default 640x640)
ZONE_POLYGON = np.array([
    [150, 120],
    [490, 120],
    [490, 400],
    [150, 400]
], np.int32)

# Target COCO class IDs (0 = person, 39 = bottle, 67 = cell phone)
TARGET_CLASSES = [0, 39, 67]

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    # Resize for consistent frame rate and coordinate mapping
    frame = cv2.resize(frame, (640, 640))
    zone_intrusion = False

    # Run YOLOv8 inference
    results = model(frame, classes=TARGET_CLASSES, conf=0.45, verbose=False)

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])

            # Calculate bottom-center point of the bounding box
            anchor_x = int((x1 + x2) / 2)
            anchor_y = int(y2)

            # Check if anchor point is inside the defined polygon
            is_inside = cv2.pointPolygonTest(ZONE_POLYGON, (anchor_x, anchor_y), False) >= 0

            if is_inside:
                zone_intrusion = True
                box_color = (0, 0, 255) # Red for alert
            else:
                box_color = (0, 255, 0) # Green for safe

            # Draw bounding box, label, and anchor dot
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
            cv2.circle(frame, (anchor_x, anchor_y), 5, box_color, -1)
            cv2.putText(
                frame, f"{label} {conf:.2f}", (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2
            )

    # Draw the monitoring zone overlay
    zone_color = (0, 0, 255) if zone_intrusion else (255, 200, 0)
    cv2.polylines(frame, [ZONE_POLYGON], isClosed=True, color=zone_color, thickness=2)

    if zone_intrusion:
        cv2.putText(
            frame, "ALERT: ZONE BREACH DETECTED", (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2
        )

    cv2.imshow("Real-Time CV Zone Monitor", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
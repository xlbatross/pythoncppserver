import cv2
import numpy as np

def getPoint(face_landmarks, img_w, img_h):
    face_3d = []
    face_2d = []
    for idx in [33, 263, 1, 61, 291, 199]:
        lm = face_landmarks.landmark[idx]
        x, y = int(lm.x * img_w), int(lm.y * img_h)
        # get the 2d coordinates
        face_2d.append([x, y])
        # get the 3d coodinates
        face_3d.append([x, y, lm.z])

    # Convert it to the NumPy Array
    face_2d = np.array(face_2d, dtype=np.float64)
    # Convert it to the NumPy Array
    face_3d = np.array(face_3d, dtype=np.float64)
    # the camera matrix
    focal_length = 1 * img_w

    cam_matrix = np.array([ [focal_length, 0, img_h / 2],
                            [0, focal_length, img_w / 2],
                            [0, 0, 1]])
    
    # The Distance Matrix
    dist_matrix = np.zeros((4, 1), dtype=np.float64)

    # Solve Pnp
    success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)

    # Get rotational matrix
    rmat, jac = cv2.Rodrigues(rot_vec)

    # Get angels
    angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

    # get the y rotation degree
    x = angles[0] * 360
    y = angles[1] * 360
    z = angles[2] * 360

    # See Where the user's head tiliing

    return (y < -10 or y > 10 or x < -5 or x > 15)
    
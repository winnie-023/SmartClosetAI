# app/services/image_analysis.py
import cv2
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import os
import uuid

def extract_dominant_colors(image_path, num_colors=3):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.reshape((image.shape[0] * image.shape[1], 3))
    kmeans = KMeans(n_clusters=num_colors)
    labels = kmeans.fit_predict(image)
    counts = Counter(labels)
    colors = kmeans.cluster_centers_.astype(int).tolist()
    return colors

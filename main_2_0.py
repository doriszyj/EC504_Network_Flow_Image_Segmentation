'__author__' == 'qiuxuan.lin'       
# coding: utf-8                     
# Python 2.7.11


from datetime import datetime
import time
from IPython import embed
import gc
import sys
sys.path.append('/Users/Shane/Documents/EC504_Network_Flow_Image_Segmentation/')
from image_process.GMM.proba import proba_gmm
from max_flow.mincut_fordfulkerson import mincut
from image_process.graph_utils import graph_penalty
from sklearn import decomposition
import cv2
import numpy as np
from math import*
from scipy.misc import imresize

# functions used to normalize and cal. scores
def sigmoid_array(x):
  return 1 / (1 + np.exp(-x))


if __name__ == '__main__':
    # Read image file
    if len(sys.argv[1]) < 3:
        print "Please specify the name of your image!"
        exit()

    image_in = sys.argv[1]
    img = cv2.imread(image_in)


    original_height, original_width = img.shape[:2]
    print "Your image is in size %d * %d" %(original_height, original_width)

    # Downsample the image to your ideal size
    # 1. input your desired ratio
    scalestring = input("Enter your desired scale ratio( a divisible  number pls...):  ")
    scale_ratio = int(scalestring)

    # store new width and new height
    w, h  = original_width/ scale_ratio, original_height/scale_ratio
    img_down = imresize(img, (h, w, 3))
    Z = img_down.reshape((-1,3))
    Z = np.float32(Z)

    # cv2.imshow('HelloWorld!', img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()



    kstring = input("How many colors do you see in this pic? ")
    K = int(kstring) + 2 #human eye perceive less colors


    print "Getting likelihood scores. Time at", datetime.now()


    centroid, pixel_proba, model = proba_gmm(Z,K, 'diag')
    pca = decomposition.PCA(2, whiten= True)
    reduced_proba = pca.fit_transform(pixel_proba)
    reduced_proba = sigmoid_array(reduced_proba) # map PCA results into (0,1) space
    label = reduced_proba.argmax(axis = 1)
    center = centroid[1:3]   # randomly take some centroid color, for visualization purpose only

    res = center[label.flatten()] # original picture
    res2 = res.reshape((img_down.shape)) # likelihood calculated

    # # Take a look at the cluster results
    #
    # cv2.imshow('Clustering results', res2)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    a = np.ceil(np.array(reduced_proba[:,0])*7).reshape(w*h)
    b = np.ceil(np.array(reduced_proba[:,1])*7).reshape(w*h)

    # embed()

    print "Initializing graph adjacency matrix..."
    n = len(a) #total number of pixels - internal "nodes"
    V = n+2 # including source and sink, V is the dim. of the input matrix
    graph = [[0 for col in range(V)] for row in range(V)]

    gp = graph_penalty()

    gp.width, gp.height = w, h
    gp.dist_penalty(graph)

    for i in range(1,n+1):
        graph[0][i], graph[i][n+1] = int(a[i-1]), int(b[i-1])


    src = 0  # source node
    sink = n + 1  # sink node

    print "Matrix dimension  V = ",V

    start = time.time()

    visited_nodes = mincut(graph, src, sink, V)

    end = time.time()
    print "Maxflow total time taken: %f minute"%((end - start)/ 60)


    final_label = np.array(visited_nodes[1:w*h +1])
    final_label = final_label * 1
    center[0] , center[1]= [0,0,0] , [255,255,255]
    res_new = center[final_label.flatten()]
    res_new2 = res_new.reshape((h,w,3))

    res2_restore = imresize(res_new2, (original_height, original_width, 3))

    print "Reconstructing Image, mouse over to check the images and hit 'return' to quit program ...", datetime.now()

    cv2.imshow('Original Image', img)
    cv2.imshow('GMMed with PCA', res2)
    cv2.imshow('MinCut result', res2_restore)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    gc.collect()
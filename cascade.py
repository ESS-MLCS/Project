# -*- coding: utf-8 -*-
"""Untitled3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1bIKcfMKW4beGLA2IeIX-7p10hUdECksv
"""

# Commented out IPython magic to ensure Python compatibility.
import time 
 
import numpy as np 
import matplotlib.pyplot as plt 

import json 
import time 
import pickle 
import sys 
import csv 
import os 
import os.path as osp 
import shutil 

import pandas as pd

from IPython.display import display, HTML
 
# %matplotlib inline 
plt.rcParams['figure.figsize'] = (10.0, 8.0) # set default size of plots 
plt.rcParams['image.interpolation'] = 'nearest' 
plt.rcParams['image.cmap'] = 'gray' 
 
# for auto-reloading external modules 
# see http://stackoverflow.com/questions/1907993/autoreload-of-modules-in-ipython 
# %load_ext autoreload
# %autoreload 2

# Some suggestions of our libraries that might be helpful for this project
from collections import Counter          # an even easier way to count
from multiprocessing import Pool         # for multiprocessing
from tqdm import tqdm                    # fancy progress bars

# Load other libraries here.
# Keep it minimal! We should be easily able to reproduce your code.
# We only support sklearn and pytorch.
import torchvision.datasets as datasets
import torchvision.transforms as transforms
import torch.utils.data as data
import torchvision

# We preload pytorch as an example
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, TensorDataset
from torch.utils.data.sampler import SubsetRandomSampler
from torch.autograd import Variable

np.random.seed(200)

compute_mode = 'cpu'

if compute_mode == 'cpu':
    device = torch.device('cpu')
elif compute_mode == 'gpu':
    # If you are using pytorch on the GPU cluster, you have to manually specify which GPU device to use
    # It is extremely important that you *do not* spawn multi-GPU jobs.
    os.environ["CUDA_VISIBLE_DEVICES"] = '0'    # Set device ID here
    device = torch.device('cuda')
else:
    raise ValueError('Unrecognized compute mode')

saved_model = "target.pth"
batch_size_train = 64
batch_size_test = 1
learning_rate = 0.001
num_epochs = 10

# (1)load data 
#torchvision dataloaders to download MNIST dataset.
transform = transforms.Compose([transforms.ToTensor()])
dataset = datasets.MNIST(root = './data', train = [True, False], transform = transform, download=True)
trainSet, testSet = torch.utils.data.random_split(dataset, [50000, 10000])

train_loader = data.DataLoader(trainSet, batch_size=batch_size_train, shuffle=True)
test_loader  = data.DataLoader(testSet, batch_size=batch_size_test, shuffle=True)

class Target(nn.Module):
    def __init__(self):
        super(Target, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x)

def train(train_loader, test_loader, model, file_name):
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Train Network
    for epoch in range(num_epochs):
        for batch_idx, (data, targets) in enumerate(tqdm(train_loader)):
            # Get data to cuda if possible
            data = data.to(device=device)
            targets = targets.to(device=device)

            # forward
            scores = model(data)
            loss = criterion(scores, targets)

            # backward
            optimizer.zero_grad()
            loss.backward()

            # gradient descent or adam step
            optimizer.step()
    torch.save(model, file_name)

target = Target().to(device)

train(train_loader, test_loader, target, saved_model)

!pip install torchattacks
from torchattacks import *

epsilon = 0.1
seen = set()
rows, cols = 10, 4
fig, ax = plt.subplots(nrows = rows, ncols = cols, figsize=(10, 10))
ax_x = 0  

for x, y in (testSet):
  if y not in seen:
    ax[ax_x][0].set_axis_off()
    ax[0][0].title.set_text("Clean Image")

    ax[ax_x][1].set_axis_off()
    ax[0][1].title.set_text("FSGM with \nepsilon=0.1")

    ax[ax_x][2].set_axis_off()
    ax[0][2].title.set_text("FSGM with \nepsilon=0.4")

    ax[ax_x][3].set_axis_off()
    ax[0][3].title.set_text("Cascade of \nFGSM + PGD + BIM + FAB \neach with epsilon=0.1")

    x1 = torch.unsqueeze(x, 1)
    y1 = torch.unsqueeze(torch.tensor(y), 0)
    
    # clean image
    ax[ax_x][0].imshow(torch.squeeze(x))

    # perturbation by FGSM using epsilon = 8/255
    atk1 = FGSM(target, epsilon)
    adv_fgsm = atk1(x1, y1)
    ax[ax_x][1].imshow(torch.squeeze(adv_fgsm))

    # perturbation by FGSM using epsilon = 4 * 8/255
    atk2 = FGSM(target, 4*epsilon)
    adv_fgsm2 = atk2(x1, y1)
    ax[ax_x][2].imshow(torch.squeeze(adv_fgsm2))

    # Perturbation using 4 different attack methods
    atk_1 = FGSM(target, epsilon)
    adv_x_1 = atk_1(x1, y1)

    atk_2 = PGD(target, eps=epsilon, alpha=2/255, steps=4) 
    adv_x_2 = atk_2(adv_x_1, y1) 

    atk_3 = BIM(target, eps=epsilon, alpha=0.1, steps=4) 
    adv_x_3 = atk_3(adv_x_2, y1) 

    atk_4 = FAB(target, eps=epsilon) 
    adv_x_4 = atk_4(adv_x_3, y1) 

    ax[ax_x][3].imshow(torch.squeeze(adv_x_4))


    ax_x += 1
    seen.add(y)
  
  if len(seen) == 10:
    break

plt.savefig("images.png")
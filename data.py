
import numpy as np
import torch
import logging
import os

from os.path import splitext
from os import listdir

from glob import glob

from PIL import Image

from torch.utils.data import Dataset, random_split


import glob
import os

import torchvision.transforms as T
from PIL import Image
from torch.utils.data import Dataset


class ClsDataset(Dataset):
    """Dataset Caltech 256
    Class number: 257
    Train data number: 24582
    Test data number: 6027

    """
    def __init__(self, dataroot, transforms=None, train=True):
        # Initial parameters
        self.dataroot = dataroot
        self.train = train
        if transforms: # Set default transforms if no transformation provided.
            self.transforms = transforms
        else:
            self.transforms = T.Compose([
                # T.RandomHorizontalFlip(),
                # T.RandomRotation((0, 30)),
                T.Resize((256, 256)),
                T.RandomResizedCrop((224, 224)),
                T.ToTensor(),
                T.Normalize((.485, .456, .406), (.229, .224, .225))
            ])
        
        # Metadata of dataset
        classes = [i.split('/')[-1] for i in glob.glob(os.path.join(dataroot, 'data', '*'))]
        self.class_num = len(classes)
        self.classes = [i.split('.')[1] for i in classes]
        self.class_to_idx = {i.split('.')[1]: int(i.split('.')[0])-1 for i in classes}
        self.idx_to_class = {int(i.split('.')[0])-1: i.split('.')[1] for i in classes}
        
        # Split file and image path list.
        self.split_file = os.path.join(dataroot, 'trainset.txt') if train else os.path.join(dataroot, 'testset.txt')
        with open(self.split_file, 'r') as f:
            self.img_paths = f.readlines()
            self.img_paths = [i.strip() for i in self.img_paths]
        self.targets = [self.class_to_idx[i.split('/')[1].split('.')[1]] for i in self.img_paths]
        self.img_paths = [os.path.join(dataroot, i) for i in self.img_paths]

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        img_path = self.img_paths[idx]
        img = Image.open(img_path).convert('RGB')
        img_tensor = self.transforms(img)
        target = self.targets[idx]

        return (img_tensor, target)

    def __repr__(self):
        repr = """Caltech-256 Dataset:
\tClass num: {}
\tData num: {}""".format(self.class_num, self.__len__())
        return repr



from torchvision.transforms import ToTensor, Lambda, Compose
from torch.utils.data import DataLoader, random_split
from torchvision import transforms

from pytorch_lightning import LightningDataModule


BATCH_SIZE = 32

class ClsDataModule(LightningDataModule):

    def __init__(self, 
                 train_dataset, 
                 test_dataset,
                 batch_size:int,
                 num_workers:int,
                 val_split_ratio:float):
        super().__init__()
        self.train_dataset = train_dataset
        self.test_dataset = test_dataset

        self.batch_size = batch_size
        self.num_workers = num_workers
        self.val_split_ratio = val_split_ratio

    def prepare_data(self): # ????????????????????????download??????????????????????????????????????????
        pass


    def setup(self, stage=None):
        if stage == 'fit' or stage is None:
            full = self.train_dataset
            
            n_train = int(len(full)*self.val_split_ratio)
            n_val = len(full) - n_train
            
            self.train, self.val = train, val = random_split(full, [n_train, n_val])

        # Assign test dataset for use in dataloader(s)
        if stage == 'test' or stage is None:
            self.test = self.test_dataset


    def train_dataloader(self):
        return DataLoader(self.train, batch_size=self.batch_size,num_workers=self.num_workers)

    def val_dataloader(self):
        if self.val_split_ratio == 0.0:
            return None # return None will force trainer to disable Validation loop.
        else:
            return DataLoader(self.val, batch_size=self.batch_size,num_workers=self.num_workers)

    def test_dataloader(self):
        return DataLoader(self.test, batch_size=self.batch_size,num_workers=self.num_workers)
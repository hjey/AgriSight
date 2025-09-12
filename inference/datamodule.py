import os
import glob
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
import pytorch_lightning as pl
import albumentations as A
from albumentations.pytorch import ToTensorV2
import cv2
import segmentation_models_pytorch as smp
from torchmetrics import JaccardIndex
from torchmetrics.classification import F1Score as TorchF1Score
import matplotlib.pyplot as plt
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping, LearningRateMonitor
from pytorch_lightning.loggers import CSVLogger
from pathlib import Path
import warnings
import torch
import torch.nn as nn
import torch.nn.functional as F

from transformers import SegformerForSemanticSegmentation, SegformerConfig, get_cosine_schedule_with_warmup
from torch.utils.data.dataloader import default_collate


class AgricultureVisionDataset(Dataset):
    def __init__(self, root_dir, split='train', transform=None):
        self.root_dir = root_dir
        self.split = split
        self.transform = transform
        
        # RGB와 NIR 디렉토리 모두 정의
        self.rgb_dir = os.path.join(root_dir, split, 'images', 'rgb')
        self.nir_dir = os.path.join(root_dir, split, 'images', 'nir')
        self.labels_base_dir = os.path.join(root_dir, split, 'labels')
        self.masks_dir = os.path.join(root_dir, split, 'masks')
        self.boundaries_dir = os.path.join(root_dir, split, 'boundaries')

        # RGB 기준으로 파일명 수집
        self.image_filenames = [
            os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(os.path.join(self.rgb_dir, '*.jpg')) + glob.glob(os.path.join(self.rgb_dir, '*.png'))
        ]
        self.image_filenames.sort()

        self.label_categories = []
        if os.path.exists(self.labels_base_dir):
            self.label_categories = [d for d in os.listdir(self.labels_base_dir) if os.path.isdir(os.path.join(self.labels_base_dir, d))]
            self.label_categories.sort()

        print(f"Loaded {len(self.image_filenames)} images for {split} split using RGB+NIR (4 channels).")
        if self.label_categories:
            print(f"Detected label categories: 🍏🍏🍏{self.label_categories}")

    def __len__(self):
        return len(self.image_filenames)

    def __getitem__(self, idx):
        img_basename = self.image_filenames[idx]

        # RGB 이미지 로드
        rgb_path_jpg = os.path.join(self.rgb_dir, f"{img_basename}.jpg")
        rgb_path_png = os.path.join(self.rgb_dir, f"{img_basename}.png")
        
        if os.path.exists(rgb_path_jpg):
            rgb_img = np.array(Image.open(rgb_path_jpg).convert("RGB"))
        elif os.path.exists(rgb_path_png):
            rgb_img = np.array(Image.open(rgb_path_png).convert("RGB"))
        else:
            raise FileNotFoundError(f"RGB image not found for {img_basename}")
        
        # NIR 이미지 로드
        nir_path_jpg = os.path.join(self.nir_dir, f"{img_basename}.jpg")
        nir_path_png = os.path.join(self.nir_dir, f"{img_basename}.png")
        
        if os.path.exists(nir_path_jpg):
            nir_img = np.array(Image.open(nir_path_jpg).convert("L"))
        elif os.path.exists(nir_path_png):
            nir_img = np.array(Image.open(nir_path_png).convert("L"))
        else:
            # NIR이 없으면 제로 채널로 대체
            nir_img = np.zeros_like(rgb_img[:,:,0])        
        
        # 4채널로 결합 (RGB + NIR)
        img = np.concatenate([rgb_img, nir_img[:,:,np.newaxis]], axis=2)
        
        masks_list = []
        
        # label_categories만 사용 (boundaries는 제외)
        for category in self.label_categories:
            label_path = os.path.join(self.labels_base_dir, category, f"{img_basename}.png")
            if os.path.exists(label_path):
                # 중요: 마스크를 255로 나누지 않고 255인 부분만 1로 변환
                mask = np.array(Image.open(label_path).convert("L"))
                binary_mask = (mask == 255).astype(np.float32)  # 255인 부분만 1, 나머지는 0
                masks_list.append(binary_mask)
            else:
                masks_list.append(np.zeros_like(img[:,:,0], dtype=np.float32))
        
        # 마스크 스택
        masks = np.stack(masks_list, axis=-1).astype(np.float32)
        
        if self.transform:
            augmented = self.transform(image=img, mask=masks)
            img = augmented['image']
            masks = augmented['mask']
            
        return img, masks


def get_baseline_train_transforms(image_size=(256, 256)):
    """Simple baseline augmentation"""
    return A.Compose([
        A.Resize(image_size[0], image_size[1], interpolation=cv2.INTER_NEAREST),
        A.HorizontalFlip(p=0.5),  # 기본적인 flip만
        A.VerticalFlip(p=0.5),
        A.Normalize(mean=(0.485, 0.456, 0.406, 0.5), std=(0.229, 0.224, 0.225, 0.25)),
        ToTensorV2(),
    ])    

def get_optimized_train_transforms(image_size=(256, 256)):
    """Agriculture Vision 데이터셋 최적화 증강"""
    return A.Compose([
        # 리사이즈
        A.Resize(image_size[0], image_size[1], interpolation=cv2.INTER_NEAREST),
        
        # 기본 Geometric 증강 (농업 현실적 범위)
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        
        # 드론 촬영 현실적 변화 시뮬레이션
        A.ShiftScaleRotate(
            shift_limit=0.08,      # 드론 위치 미세 변화
            scale_limit=0.1,       # 고도 변화 (10% 이내)
            rotate_limit=5,       # 현실적인 회전 (5도 이내), 인위적인 검은 배경 최소화
            p=0.6,
            border_mode=cv2.BORDER_REFLECT_101
        ),
        
        # 농업 환경 특화 증강
        A.RandomBrightnessContrast(
            brightness_limit=0.15,  # 구름/그림자 효과
            contrast_limit=0.15,    # 대기 조건 변화
            p=0.4
        ),
        
        # 센서 노이즈 시뮬레이션 (약하게)
        A.GaussNoise(var_limit=(5, 20), p=0.25),
        
        # 4채널 특화: 일부 채널 드롭아웃 (NIR 센서 오류 시뮬레이션)
        A.ChannelDropout(
            channel_drop_range=(1, 1),  # 1개 채널만 드롭
            fill_value=0,
            p=0.1  # 낮은 확률로 적용
        ),
        
        # 작은 영역 드롭아웃 (잡음/가림 효과)
        A.CoarseDropout(
            max_holes=5,
            max_height=12,
            max_width=12,
            p=0.15,
            fill_value=0,
            mask_fill_value=0
        ),
        
        # 4채널용 정규화 (Agriculture Vision 데이터셋 통계 기반)
        A.Normalize(
            mean=[0.485, 0.456, 0.406, 0.408],  # NIR 채널 평균값 조정
            std=[0.229, 0.224, 0.225, 0.237]    # NIR 채널 표준편차 조정
        ),
        ToTensorV2(),
    ])
    
def get_val_test_transforms(image_size=(256, 256)):
    return A.Compose([
        A.Resize(image_size[0], image_size[1], interpolation=cv2.INTER_NEAREST),
        # 4채널용 normalize
        A.Normalize(mean=(0.485, 0.456, 0.406, 0.5), std=(0.229, 0.224, 0.225, 0.25)),
        ToTensorV2(),
    ])

def denormalize_4ch(tensor, mean=[0.485, 0.456, 0.406, 0.408], std=[0.229, 0.224, 0.225, 0.237]):
    """4채널 텐서 역정규화 (시각화용)"""
    import torch
    
    # tensor와 같은 디바이스에 mean, std 배치
    mean = torch.tensor(mean, device=tensor.device).view(4, 1, 1)
    std = torch.tensor(std, device=tensor.device).view(4, 1, 1)
    
    # 역정규화
    denorm_tensor = tensor * std + mean
    
    # RGB 채널만 추출해서 시각화 (0-1 범위로 클램핑)
    rgb_tensor = denorm_tensor[:3].clamp(0, 1)
    
    return rgb_tensor
    
class AgricultureVisionDataModule(pl.LightningDataModule):
    def __init__(self, config):
        super().__init__()
        self.config = config 
        
        # 각 변수를 config 딕셔너리에서 가져옵니다.
        self.root_dir = config['DATASET_ROOT_PATH']
        self.batch_size = config['BATCH_SIZE']
        self.num_workers = config['NUM_WORKERS']
        self.image_size = tuple(config['IMAGE_SIZE'])

        self.train_transform = get_baseline_train_transforms(self.image_size)
        self.val_test_transform = get_val_test_transforms(self.image_size)

        self.num_mask_channels = None
        self.label_categories = None
    
    def setup(self, stage=None):
        print(f"Setting up datasets for stage: {stage}")
        print(f"Root directory: {self.root_dir}")
        
        # 각 split 디렉토리 존재 확인
        train_dir = os.path.join(self.root_dir, 'train')
        val_dir = os.path.join(self.root_dir, 'val')
        test_dir = os.path.join(self.root_dir, 'test')
        
        print(f"Train dir exists: {os.path.exists(train_dir)}")
        print(f"Val dir exists: {os.path.exists(val_dir)}")
        print(f"Test dir exists: {os.path.exists(test_dir)}")
        
        if os.path.exists(test_dir):
            test_files = os.listdir(test_dir)
            print(f"Test dir contents: {test_files[:5]}...")
    
        self.train_dataset = AgricultureVisionDataset(
            root_dir=self.root_dir, split='train', transform=self.train_transform
        )
        self.val_dataset = AgricultureVisionDataset(
            root_dir=self.root_dir, split='val', transform=self.val_test_transform
        )
        self.test_dataset = AgricultureVisionDataset(
            root_dir=self.root_dir, split='test', transform=self.val_test_transform
        )

        print(f"Train dataset size: {len(self.train_dataset)}")
        print(f"Val dataset size: {len(self.val_dataset)}")
        print(f"Test dataset size: {len(self.test_dataset)}")
        
        if len(self.test_dataset) == 0:
            print("Warning: Test dataset is empty! Using validation dataset for testing.")
            self.test_dataset = self.val_dataset
            
        if self.train_dataset:
            _, sample_masks = self.train_dataset[0]
            print(f"Sample masks shape: {sample_masks.shape}")
            
            # 마스크가 [H, W, C] 형태라면 마지막 차원이 채널 수
            if len(sample_masks.shape) == 3:
                self.num_mask_channels = sample_masks.shape[-1]
            else:
                print(f"Unexpected mask shape: {sample_masks.shape}")
                self.num_mask_channels = 6
                
            self.label_categories = self.train_dataset.label_categories
            print(f"Detected {self.num_mask_channels} mask channels. Label categories: 🍏{self.label_categories}")
        else:
            raise RuntimeError("Train dataset not initialized. Cannot determine mask channels.")


    def custom_collate_fn(self, batch):
        images = [item[0] for item in batch]
        masks = [item[1] for item in batch]

        # 이미지 배치 생성
        collated_images = default_collate(images)
        # print(f"DEBUG_COLLATE: Collated images batch shape: {collated_images.shape}")

        # 마스크 처리 - 더 명확하게
        collated_masks_list = []
        for mask in masks:
            if isinstance(mask, np.ndarray):
                mask_tensor = torch.from_numpy(mask).float()
            else:
                mask_tensor = mask.float()
                
            if mask_tensor.ndim == 3:
                if mask_tensor.shape[-1] == len(self.train_dataset.label_categories):  # [H, W, C]
                    mask_tensor = mask_tensor.permute(2, 0, 1)  # [C, H, W]
            collated_masks_list.append(mask_tensor)
        collated_masks = default_collate(collated_masks_list)
        return collated_images, collated_masks

    def train_dataloader(self):
        loader = DataLoader(
            self.train_dataset, 
            batch_size=self.batch_size, 
            shuffle=True, 
            num_workers=self.num_workers,
            collate_fn=self.custom_collate_fn # 여기에 추가
        )
        print(f"Train dataloader created with {len(loader)} batches (num_workers={self.num_workers})")
        return loader

    def val_dataloader(self):
        loader = DataLoader(
            self.val_dataset, 
            batch_size=self.batch_size, 
            shuffle=False, 
            num_workers=self.num_workers,
            collate_fn=self.custom_collate_fn # 여기에 추가
        )
        print(f"Val dataloader created with {len(loader)} batches (num_workers={self.num_workers})")
        return loader

    def test_dataloader(self):
        loader = DataLoader(self.test_dataset, batch_size=self.batch_size, shuffle=False, num_workers=self.num_workers)
        print(f"Test dataloader created with {len(loader)} batches")
        return loader
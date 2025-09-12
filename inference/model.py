import os
import numpy as np
from PIL import Image
import torch
import pytorch_lightning as pl
import albumentations as A
import segmentation_models_pytorch as smp
from torchmetrics import JaccardIndex
from torchmetrics.classification import F1Score as TorchF1Score
import matplotlib.pyplot as plt
from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
from losses import CombinedTverskyFocalLoss

from transformers import SegformerForSemanticSegmentation, SegformerConfig

def _create_overlay_image(original_image_tensor, masks_tensor, label_categories, alpha=0.5):
    """
    이미지와 마스크를 오버레이하여 PIL 이미지를 생성합니다.
    Agriculture-Vision 데이터셋에 최적화된 버전
    """
    try:
        print(f"Input validation - Original: {original_image_tensor.shape}, Masks: {masks_tensor.shape}")
        
        # GPU 텐서를 CPU로 이동하고 numpy로 변환
        if original_image_tensor.is_cuda:
            original_image_tensor = original_image_tensor.cpu()
        if masks_tensor.is_cuda:
            masks_tensor = masks_tensor.cpu()
        
        image_np = original_image_tensor.detach().numpy()
        mask_np = masks_tensor.detach().numpy()
        
        if not isinstance(label_categories, (list, tuple)):
            raise ValueError(f"label_categories must be list/tuple, got {type(label_categories)}")
        if not hasattr(mask_np, "shape"):
            raise ValueError(f"masks_tensor must be Tensor/ndarray, got {type(mask_np)}")
        
        # 마스크 차원 변환
        if len(mask_np.shape) == 3:
            if mask_np.shape[-1] == len(label_categories):  # (H, W, C) 형태
                mask_np = np.transpose(mask_np, (2, 0, 1))  # (C, H, W)로 변환

        # Agriculture-Vision 특화 이미지 전처리
        # 정규화된 이미지를 원래 이미지로 복원
        if image_np.shape[0] == 4:  # RGB+NIR인 경우
            # RGB 채널만 사용하고 정규화 해제
            rgb_tensor = image_np[:3]  # RGB 채널만 선택
            mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1)
            std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1)
            rgb_tensor = rgb_tensor * std + mean  # 정규화 해제
            rgb_tensor = np.clip(rgb_tensor, 0, 1)
            image_np = rgb_tensor
        elif image_np.shape[0] == 3:  # RGB만 있는 경우
            if image_np.min() < 0:  # 정규화된 경우
                mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1)
                std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1)
                image_np = image_np * std + mean
                image_np = np.clip(image_np, 0, 1)
        elif image_np.shape[0] == 1:  # 그레이스케일인 경우
            image_np = np.repeat(image_np, 3, axis=0)
        else:
            print(f"Warning: Unexpected image channels: {image_np.shape[0]}, using first 3 channels")
            image_np = image_np[:3]
        
        # (C, H, W) -> (H, W, C)로 변환
        image_np = np.transpose(image_np, (1, 2, 0))
        
        # 값 범위 확인 및 조정
        if image_np.max() > 1.0:
            image_np = image_np / 255.0
        image_np = np.clip(image_np, 0, 1)
        
        # PIL 이미지로 변환
        base_img_pil = Image.fromarray((image_np * 255).astype(np.uint8)).convert("RGBA")
        
        # 마스크가 있는 경우에만 오버레이 적용
        if alpha > 0 and len(mask_np.shape) >= 2:
            # 마스크 색상 정의
            mask_colors = {
                'cloud_shadow': (255, 0, 0, int(255 * alpha)),     # 빨강
                'double_plant': (255, 255, 0, int(255 * alpha)),   # 노랑
                'planter_skip': (0, 255, 255, int(255 * alpha)),   # 시안
                'standing_water': (128, 0, 128, int(255 * alpha)), # 보라
                'waterway': (255, 165, 0, int(255 * alpha)),       # 주황
                'weed_cluster': (255, 0, 255, int(255 * alpha))    # 마젠타
            }
            
            final_img = base_img_pil.copy()
            
            # 다중 클래스 마스크 처리
            if len(mask_np.shape) == 3:  # (C, H, W)
                print('label_categories: ', label_categories)
                for i, category in enumerate(label_categories):
                    if i < mask_np.shape[0]:
                        class_mask = mask_np[i] > 0.5
                        if np.any(class_mask):
                            # 마스크 색상 생성
                            colored_mask_np = np.zeros((*class_mask.shape, 4), dtype=np.uint8)
                            color = mask_colors.get(category, (128, 128, 128, int(255 * alpha)))
                            colored_mask_np[class_mask] = color
                            
                            # 오버레이 적용
                            colored_mask_pil = Image.fromarray(colored_mask_np, 'RGBA')
                            final_img = Image.alpha_composite(final_img, colored_mask_pil)
            else:  # (H, W) 단일 마스크
                class_mask = mask_np > 0.5
                if np.any(class_mask):
                    colored_mask_np = np.zeros((*class_mask.shape, 4), dtype=np.uint8)
                    colored_mask_np[class_mask] = (0, 255, 0, int(255 * alpha))  # 기본 초록색
                    
                    colored_mask_pil = Image.fromarray(colored_mask_np, 'RGBA')
                    final_img = Image.alpha_composite(final_img, colored_mask_pil)
            
            return final_img
        else:
            return base_img_pil
        
    except Exception as e:
        
        print(f"Error in _create_overlay_image: {str(e)}")
        print(f"Original tensor shape: {original_image_tensor.shape if hasattr(original_image_tensor, 'shape') else 'No shape'}")
        print(f"Masks tensor shape: {masks_tensor.shape if hasattr(masks_tensor, 'shape') else 'No shape'}")
        print(f"Label categories: {label_categories}")
        import traceback
        traceback.print_exc()
        
        # 에러 시 기본 이미지 반환
        try:
            if original_image_tensor.is_cuda:
                original_image_tensor = original_image_tensor.cpu()
            image_np = original_image_tensor.detach().numpy()
            
            if image_np.shape[0] >= 3:
                image_np = image_np[:3]
            elif image_np.shape[0] == 1:
                image_np = np.repeat(image_np, 3, axis=0)
            else:
                image_np = np.zeros((3, 256, 256))
                
            image_np = np.transpose(image_np, (1, 2, 0))
            image_np = np.clip(image_np, 0, 1) if image_np.max() <= 1.0 else np.clip(image_np / 255.0, 0, 1)
            
            return Image.fromarray((image_np * 255).astype(np.uint8))
        except:
            # 최후의 수단: 검은색 이미지
            return Image.fromarray(np.zeros((256, 256, 3), dtype=np.uint8))
        

class SegmentationModel(pl.LightningModule):
    def __init__(self, backbone_model_name, num_classes, label_categories, learning_rate=1e-4, pretrained=True):
        super().__init__()
        
        # self.save_hyperparameters()
        self.backbone_model_name = backbone_model_name
        self.num_classes = num_classes
        # self.label_categories = label_categories
        self.label_categories = [
            'cloud_shadow',
            'double_plant',
            'planter_skip',
            'standing_water',
            'waterway',
            'weed_cluster'
        ]

        print(f"Initializing custom segmentation model with backbone: {self.backbone_model_name}")
        print(f"Initializing model with num_classes: {self.num_classes}")
        print(f"Label categories: 🍏🍏 {self.label_categories}")

        # === SegFormer 모델 로드 ===
        if pretrained:
            config = SegformerConfig.from_pretrained(backbone_model_name)
            config.num_labels = num_classes
            self.model = SegformerForSemanticSegmentation.from_pretrained(
                backbone_model_name,
                config=config,
                ignore_mismatched_sizes=True
            )
        else:
            config = SegformerConfig.from_pretrained(backbone_model_name)
            config.num_labels = num_classes
            self.model = SegformerForSemanticSegmentation(config)

        # === 4채널 입력을 위한 첫 번째 레이어 수정 (한 번만!) ===
        try:
            original_conv = self.model.segformer.encoder.patch_embeddings[0].proj
            new_conv = nn.Conv2d(
                in_channels=4,  # RGB + NIR
                out_channels=original_conv.out_channels,
                kernel_size=original_conv.kernel_size,
                stride=original_conv.stride,
                padding=original_conv.padding,
                bias=original_conv.bias is not None
            )
            
            # 가중치 복사
            with torch.no_grad():
                new_conv.weight[:, :3, :, :] = original_conv.weight
                new_conv.weight[:, 3:, :, :] = original_conv.weight[:, :1, :, :]  # NIR을 R 채널로 초기화
                if original_conv.bias is not None:
                    new_conv.bias.copy_(original_conv.bias)
            
            self.model.segformer.encoder.patch_embeddings[0].proj = new_conv
            print(f"Successfully initialized Segformer with 4 channels input")
            
        except Exception as e:
            print(f"Error during 4-channel input modification: {e}")
            raise


        # === 클래스 가중치 설정 ===
        total_train_images = 12901
        train_counts = {
            'cloud_shadow': 931,      # 7.2% 이미지에 존재
            'double_plant': 1761,     # 13.6% 이미지에 존재
            'planter_skip': 270,      # 2.1% 이미지에 존재 (가장 희귀)
            'standing_water': 815,    # 6.3% 이미지에 존재
            'waterway': 1769,         # 13.7% 이미지에 존재
            'weed_cluster': 8890      # 68.9% 이미지에 존재 (매우 흔함)
        }

        print("\n=== 클래스 분포 분석 (전체 12,901개 이미지 기준) ===")
        for category, count in train_counts.items():
            percentage = (count / total_train_images) * 100
            absence_rate = ((total_train_images - count) / total_train_images) * 100
            print(f"{category}: {count}/{total_train_images} images ({percentage:.1f}% 존재, {absence_rate:.1f}% 부재)")

        # 농업적 중요도와 희귀성을 결합한 가중치 (최종 결과를 위해 조정)
        agricultural_importance = {
            'planter_skip': 15.0,     # 극희귀 클래스 강력 부스팅 (최종 2.0 목표)
            'standing_water': 6.5,    # 희귀 + 중요 (최종 1.4 목표)
            'cloud_shadow': 5.2,      # 중간 중요도 + 희귀 (최종 1.2 목표)
            'double_plant': 3.8,      # 중요하지만 상당히 흔함 (최종 1.1 목표)
            'waterway': 3.2,          # 낮은 중요도 + 흔함 (최종 1.0 목표)
            'weed_cluster': 0.52      # dominant 클래스 억제 (최종 0.9 목표)
        }
        # raw weight 계산
        raw_weights = []
                
        # === 클래스 가중치 계산 (단계별) ===
        for category in self.label_categories:  # <- self.label_categories 사용
            count = train_counts.get(category, 1)
            presence_ratio = count / total_train_images
            inv_freq_weight = 1.0 / (presence_ratio + 1e-6)
            importance = agricultural_importance.get(category, 1.0)
            raw_weight = inv_freq_weight * importance
            raw_weights.append(raw_weight)

            # print(f"Label categories: {self.label_categories}")  # <- self.label_categories 사용
            print(f"  - 존재 이미지: {count}/{total_train_images} ({presence_ratio*100:.1f}%)")
            print(f"  - 역빈도: {inv_freq_weight:.3f}")
            print(f"  - 중요도: {importance}")
            print(f"  - Raw 가중치: {raw_weight:.3f}")

        # 정규화: 평균이 1.0이 되도록
        mean_weight = sum(raw_weights) / len(raw_weights)
        print(f"\n평균 raw 가중치: {mean_weight:.3f}")

        # 최종 가중치 계산 (1.0 기준으로 조정, 범위 확장)
        class_weights = []
        print("\n=== 최종 가중치 (정규화 후) ===")
        for i, category in enumerate(self.label_categories):
            raw_weight = raw_weights[i]
            adjusted_weight = 1.0 + 0.15 * (raw_weight / mean_weight - 1.0)
            final_weight = max(0.8, min(adjusted_weight, 2.2))  # 범위를 2.2까지 확장
            
            class_weights.append(final_weight)
            print(f"{category}: {final_weight:.3f}")

        self.class_weights = torch.tensor(class_weights, dtype=torch.float32)

        # === 손실 함수 ===
        self.combined_loss = CombinedTverskyFocalLoss(
            tversky_weight=0.7,     # Tversky 비중 증가
            focal_weight=0.3,       
            tversky_alpha=0.2,      # FN 페널티 증가 (recall 향상)
            tversky_beta=0.8,       
            focal_alpha=1.0,
            focal_gamma=2.5,        # hard example 집중
            class_weights=self.class_weights
        )

        # === 메트릭 ===
        self.iou_metric = JaccardIndex(task='multilabel', num_labels=num_classes, threshold=0.5)
        self.f1_metric = TorchF1Score(task='multilabel', num_labels=num_classes, threshold=0.5)

    def forward(self, x):
        """Forward pass through SegFormer model"""        
        # SegFormer forward
        outputs = self.model(pixel_values=x)
        logits = outputs.logits

        # SegFormer 출력을 입력 크기로 업샘플링
        logits = F.interpolate(
            logits, 
            size=x.shape[-2:], 
            mode='bilinear', 
            align_corners=False
        )
        # contiguous() 호출로 메모리 레이아웃 문제 해결
        logits = logits.contiguous()
        return logits

    def shared_step(self, batch, stage):
        """Shared step for train/val/test"""
        images, masks = batch
    
        # 입력 검증
        if images.shape[1] != 4:
            raise ValueError(f"Expected 4 channels, got {images.shape[1]}")
        if masks.shape[1] != len(self.label_categories):
            raise ValueError(f"Expected {len(self.label_categories)} mask channels, got {masks.shape[1]}")
        

        try:
            # Forward pass
            logits = self.forward(images)

            # 손실 계산
            loss = self.combined_loss(logits, masks)
            
            # 메트릭 계산
            with torch.no_grad():
                prob_masks = torch.sigmoid(logits)
                pred_masks = (prob_masks > 0.5).float()
                
                # 메트릭 계산 - int 타입으로 변환 (bincount 에러 해결)
                pred_masks_int = pred_masks.int()
                masks_int = masks.int()
                
                iou_score = self.iou_metric(pred_masks_int, masks_int)
                f1_score = self.f1_metric(pred_masks_int, masks_int)
                
            # print(f"DEBUG_SHARED_STEP: {stage} - IoU: {iou_score:.4f}, F1: {f1_score:.4f}")
            
        except Exception as e:
            print(f"ERROR_SHARED_STEP: {stage} - {e}")
            print(f"Images shape: {images.shape}, dtype: {images.dtype}")
            print(f"Masks shape: {masks.shape}, dtype: {masks.dtype}")
            if 'logits' in locals():
                print(f"Logits shape: {logits.shape}, dtype: {logits.dtype}")
            raise
        
        
        # Logging
        sync_needed = stage in ['val', 'test'] 
        self.log(f'{stage}_loss', loss, prog_bar=True, sync_dist=sync_needed)
        self.log(f'{stage}_iou', iou_score, prog_bar=True, sync_dist=sync_needed)
        self.log(f'{stage}_f1', f1_score, prog_bar=True, sync_dist=sync_needed)
        
        return {"loss": loss, "iou": iou_score, "f1": f1_score}

    def training_step(self, batch, batch_idx):
        result = self.shared_step(batch, "train")
        return result['loss']

    def validation_step(self, batch, batch_idx):
        result = self.shared_step(batch, "val")
        return result['loss']

    def test_step(self, batch, batch_idx):
        result = self.shared_step(batch, "test")
        return result['loss']
    
    def configure_optimizers(self):
        """Configure optimizer and scheduler"""
        # 차별화된 학습률 (Encoder vs Decoder)
        encoder_params = []
        decoder_params = []
        
        for name, param in self.model.named_parameters():
            if 'segformer.encoder' in name:  # Pretrained encoder
                encoder_params.append(param)
            else:  # Decoder (classification head)
                decoder_params.append(param)
        
        optimizer = torch.optim.AdamW([
            {
                'params': encoder_params, 
                'lr': self.hparams.learning_rate * 0.1,  # Encoder: 낮은 학습률
                'weight_decay': 1e-4
            },
            {
                'params': decoder_params, 
                'lr': self.hparams.learning_rate,        # Decoder: 기본 학습률
                'weight_decay': 1e-3                     # Decoder: 강한 정규화
            }
        ], betas=(0.9, 0.95))

        
        # 스케줄러도 함께 최적화
        # CosineAnnealingLR + Warmup 조합
        def lr_lambda(current_step):
            warmup_steps = 100  # 초기 100 스텝 동안 warmup
            if current_step < warmup_steps:
                return float(current_step) / float(max(1, warmup_steps))
            return 1.0
        
        warmup_scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
        cosine_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, 
            T_max=30,      # 30 에포크
            eta_min=1e-7   # 최소 학습률
        )
        
        # Sequential scheduler (Warmup → CosineAnnealing)
        scheduler = torch.optim.lr_scheduler.SequentialLR(
            optimizer,
            schedulers=[warmup_scheduler, cosine_scheduler],
            milestones=[100]  # 100 스텝 후 cosine으로 전환
        )

        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "interval": "step",  # step 단위 업데이트 권장
                "frequency": 1,
            },
        }    
            
    def on_train_epoch_end(self):
        pass

    def on_validation_epoch_end(self):
        pass

    def on_test_epoch_end(self):
        pass

def create_directories(paths):
    """필요한 디렉터리들을 생성합니다."""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)
        print(f"Directory ensured: {path}")

def validate_dataset_path(dataset_path):
    """데이터셋 경로가 유효한지 확인합니다."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset path does not exist: {dataset_path}")
    
    expected_dirs = ['train', 'val']
    missing_dirs = []
    for dir_name in expected_dirs:
        dir_path = os.path.join(dataset_path, dir_name)
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"Warning: Expected directories not found: {missing_dirs}")

import torch
import torch.nn as nn
import torch.nn.functional as F

class TverskyLoss(nn.Module):
    """
    Class-wise weighted Tversky Loss for multi-label segmentation
    Tversky Index = TP / (TP + α*FN + β*FP)
    Loss = 1 - Tversky Index
    """
    def __init__(self, alpha=0.7, beta=0.3, smooth=1e-6, class_weights=None):
        super(TverskyLoss, self).__init__()
        self.alpha = alpha  # False Negative에 대한 가중치
        self.beta = beta   # False Positive에 대한 가중치
        self.smooth = smooth
        self.class_weights = class_weights
        
    def forward(self, inputs, targets):
        # print(f"DEBUG_TVERSKY: inputs shape: {inputs.shape}, targets shape: {targets.shape}")
        
        # Sigmoid 적용하여 확률로 변환
        inputs = torch.sigmoid(inputs)
        batch_size, num_classes = inputs.shape[:2]
        
        # Class별로 Tversky Loss 계산
        total_loss = 0.0
        for class_idx in range(num_classes):
            # 해당 클래스의 입력과 타겟 추출 - contiguous() 추가!
            class_input = inputs[:, class_idx].contiguous().view(-1)
            class_target = targets[:, class_idx].contiguous().view(-1)
            
            # True Positives, False Negatives, False Positives 계산
            TP = (class_input * class_target).sum()
            FN = ((1 - class_input) * class_target).sum()
            FP = (class_input * (1 - class_target)).sum()
            
            # Tversky Index 계산
            tversky_index = (TP + self.smooth) / (TP + self.alpha * FN + self.beta * FP + self.smooth)
            class_loss = 1 - tversky_index
            
            # Class weight 적용
            if self.class_weights is not None:
                class_weight = self.class_weights[class_idx]
                class_loss = class_loss * class_weight
                
            total_loss += class_loss
        
        # 평균 계산하여 반환 (이 부분이 빠져있었습니다!)
        final_loss = total_loss / num_classes
        # print(f"DEBUG_TVERSKY: Fin loss: {final_loss.item():.4f}")
        return final_loss


class FocalLoss(nn.Module):
    """
    Class-wise weighted Focal Loss for addressing class imbalance
    FL(p_t) = -α_t * (1-p_t)^γ * log(p_t)
    """
    def __init__(self, alpha=1.0, gamma=1.0, class_weights=None, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.class_weights = class_weights
        self.reduction = reduction
        
    def forward(self, inputs, targets):
        # print(f"DEBUG_FOCAL: inputs shape: {inputs.shape}, targets shape: {targets.shape}")
        
        batch_size, num_classes = inputs.shape[:2]
        
        # Class별로 Focal Loss 계산
        total_loss = 0.0
        for class_idx in range(num_classes):
            # 해당 클래스의 입력과 타겟 추출 - contiguous() 추가!
            class_input = inputs[:, class_idx].contiguous()
            class_target = targets[:, class_idx].contiguous()
            
            # BCE with logits
            bce_loss = F.binary_cross_entropy_with_logits(class_input, class_target, reduction='none')
            
            # p_t 계산
            p_t = torch.exp(-bce_loss)
            
            # Focal weight 계산: (1-p_t)^gamma
            focal_weight = (1 - p_t) ** self.gamma
            
            # Alpha weight 적용
            alpha_weight = self.alpha
            
            # Focal loss 계산
            class_focal_loss = alpha_weight * focal_weight * bce_loss
            
            # Class weight 적용
            if self.class_weights is not None:
                class_weight = self.class_weights[class_idx]
                class_focal_loss = class_focal_loss * class_weight
                
            if self.reduction == 'mean':
                class_focal_loss = class_focal_loss.mean()
            elif self.reduction == 'sum':
                class_focal_loss = class_focal_loss.sum()
                
            total_loss += class_focal_loss
        
        # 평균 계산 (들여쓰기 수정!)
        final_loss = total_loss / num_classes
        # print(f"DEBUG_FOCAL: Fin loss: {final_loss.item():.4f}")
        return final_loss


class CombinedTverskyFocalLoss(nn.Module):
    """
    Class-wise weighted Tversky Loss와 Focal Loss를 결합한 손실 함수
    """
    def __init__(self, tversky_weight=0.7, focal_weight=0.3,
                tversky_alpha=0.3, tversky_beta=0.7,
                focal_alpha=1.0, focal_gamma=2.0, class_weights=None):
        super(CombinedTverskyFocalLoss, self).__init__()
        self.tversky_weight = tversky_weight
        self.focal_weight = focal_weight
        
        self.tversky_loss = TverskyLoss(
            alpha=tversky_alpha,
            beta=tversky_beta,
            class_weights=class_weights
        )
        self.focal_loss = FocalLoss(
            alpha=focal_alpha,
            gamma=focal_gamma,
            class_weights=class_weights
        )
        
    def forward(self, inputs, targets):
        # print(f"DEBUG_COMBINED: Starting loss calculation...")
        # print(f"DEBUG_COMBINED: inputs shape: {inputs.shape}, targets shape: {targets.shape}")
        
        # print(f"DEBUG_COMBINED: Calling Tversky loss...")
        tversky = self.tversky_loss(inputs, targets)
        # print(f"DEBUG_COMBINED: Tversky loss: {tversky.item():.4f}")
        
        # print(f"DEBUG_COMBINED: Calling Focal loss...")
        focal = self.focal_loss(inputs, targets)
        # print(f"DEBUG_COMBINED: Focal loss: {focal.item():.4f}")
        
        combined_loss = self.tversky_weight * tversky + self.focal_weight * focal
        # print(f"DEBUG_COMBINED: Combined loss: {combined_loss.item():.4f}")
        
        return combined_loss
    

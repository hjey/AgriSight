
baseline = {
    'DATASET_ROOT_PATH': 'Agriculture-Vision',
    'BATCH_SIZE':         8,
    'NUM_WORKERS':        4,
    'PIN_MEMORY':         True,
    'MAX_EPOCHS':        10,
    'IMAGE_SIZE':       (256, 256),
    'LOG_DIR':         'tb_logs',
    'CHECKPOINT_DIR':  './segformer_checkpoints_baseline',
    'RESULTS_DIR':     './results',
    'LEARNING_RATE':   1e-4,
    'BACKBONE_MODEL': 'nvidia/segformer-b0-finetuned-ade-512-512',
    'LABEL_CATEGORIES': [
        'cloud_shadow',
        'double_plant',
        'planter_skip',
        'standing_water',
        'waterway',
        'weed_cluster'
    ]
}

optimized = {
    'DATASET_ROOT_PATH': 'Agriculture-Vision',
    'BATCH_SIZE':        64,
    'NUM_WORKERS':       12,
    'PIN_MEMORY':        True,
    'MAX_EPOCHS':        30,
    'IMAGE_SIZE':      (256, 256),
    'LOG_DIR':        'tb_logs',
    'CHECKPOINT_DIR': './segformer_checkpoints_optimized',
    'RESULTS_DIR':    './results_a100',
    'LEARNING_RATE':  3e-4,
    'BACKBONE_MODEL':'nvidia/segformer-b0-finetuned-ade-512-512',
    'LABEL_CATEGORIES': [
        'cloud_shadow',
        'double_plant',
        'planter_skip',
        'standing_water',
        'waterway',
        'weed_cluster'
    ]
}

"""
ML-Based Prompt Injection Detection
====================================
Uses Meta's Llama Prompt Guard 2 (86M) model to detect prompt injection
and jailbreak attempts with high accuracy.

Model: meta-llama/Llama-Prompt-Guard-2-86M
- Runs locally on CPU (86M parameters, very fast)
- Classifies text as: BENIGN, INJECTION, or JAILBREAK
- Acts as a second defense layer alongside regex-based detection

Reference: https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M
"""

import logging
import torch
from typing import Tuple, Optional
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger("uvicorn")


class MLPromptGuard:
    """
    ML-based prompt injection detector using Llama Prompt Guard 2.
    
    Labels:
        0 = BENIGN   - Safe input
        1 = INJECTION - Prompt injection attempt
        2 = JAILBREAK - Jailbreak attempt
    """
    
    LABEL_MAP = {0: "BENIGN", 1: "INJECTION", 2: "JAILBREAK"}
    
    def __init__(self, model_name: str, threshold: float = 0.75, hf_token: Optional[str] = None):
        """
        Args:
            model_name: HuggingFace model ID
            threshold: Probability threshold for flagging (0.0-1.0)
            hf_token: HuggingFace token for gated models
        """
        self.model_name = model_name
        self.threshold = threshold
        self.hf_token = hf_token
        self._model = None
        self._tokenizer = None
        self._loaded = False
        self._load_failed = False
    
    def _load_model(self):
        """Lazy-load model on first use to avoid blocking startup."""
        if self._loaded or self._load_failed:
            return
        
        try:
            logger.info(f"🧠 Loading Prompt Guard model: {self.model_name}...")
            
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=self.hf_token
            )
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                token=self.hf_token
            )
            self._model.eval()  # Set to evaluation mode
            
            self._loaded = True
            logger.info("✅ Prompt Guard model loaded successfully")
            
        except Exception as e:
            self._load_failed = True
            logger.error(f"❌ Failed to load Prompt Guard model: {e}")
            logger.warning("⚠️ ML prompt guard disabled, falling back to regex-only")
    
    @property
    def is_available(self) -> bool:
        """Check if the model is loaded and ready."""
        if not self._loaded and not self._load_failed:
            self._load_model()
        return self._loaded
    
    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify text as BENIGN, INJECTION, or JAILBREAK.
        
        Args:
            text: Input text to classify
            
        Returns:
            Tuple of (label, confidence) e.g. ("INJECTION", 0.98)
            Returns ("BENIGN", 0.0) if model is unavailable
        """
        if not self.is_available:
            return "BENIGN", 0.0
        
        try:
            inputs = self._tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512
            )
            
            with torch.no_grad():
                outputs = self._model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=-1)
            
            # Get the predicted label and its probability
            max_prob, predicted_class = torch.max(probabilities, dim=-1)
            label = self.LABEL_MAP.get(predicted_class.item(), "BENIGN")
            confidence = max_prob.item()
            
            return label, confidence
            
        except Exception as e:
            logger.error(f"❌ ML classification error: {e}")
            return "BENIGN", 0.0
    
    def is_malicious(self, text: str) -> Tuple[bool, str, float]:
        """
        Check if input text is malicious.
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (is_malicious, label, confidence)
        """
        label, confidence = self.classify(text)
        
        is_threat = label in ("INJECTION", "JAILBREAK") and confidence >= self.threshold
        
        if is_threat:
            logger.warning(
                f"🚨 ML Guard detected {label} (confidence: {confidence:.2%})"
            )
        
        return is_threat, label, confidence
    
    def get_detailed_scores(self, text: str) -> dict:
        """
        Get probability scores for all labels.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dict with scores for each label
        """
        if not self.is_available:
            return {"BENIGN": 1.0, "INJECTION": 0.0, "JAILBREAK": 0.0, "available": False}
        
        try:
            inputs = self._tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            with torch.no_grad():
                outputs = self._model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=-1)[0]
            
            scores = {
                self.LABEL_MAP[i]: probabilities[i].item()
                for i in range(len(probabilities))
            }
            scores["available"] = True
            
            return scores
            
        except Exception as e:
            logger.error(f"❌ ML scoring error: {e}")
            return {"BENIGN": 1.0, "INJECTION": 0.0, "JAILBREAK": 0.0, "available": False}


# Singleton - initialized lazily
_ml_guard_instance: Optional[MLPromptGuard] = None


def get_ml_prompt_guard() -> MLPromptGuard:
    """Get or create the singleton MLPromptGuard instance."""
    global _ml_guard_instance
    
    if _ml_guard_instance is None:
        from ai_service.core.config import settings
        _ml_guard_instance = MLPromptGuard(
            model_name=settings.HF_PROMPT_GUARD_MODEL,
            threshold=settings.PROMPT_GUARD_ML_THRESHOLD,
            hf_token=settings.HF_TOKEN
        )
    
    return _ml_guard_instance


def preload_prompt_guard_model():
    """Pre-load model at startup for faster first inference."""
    from ai_service.core.config import settings
    
    if not settings.PROMPT_GUARD_ML_ENABLED:
        logger.info("ℹ️ ML Prompt Guard is disabled in config")
        return
    
    logger.info("🛡️ Preloading ML Prompt Guard model...")
    guard = get_ml_prompt_guard()
    
    if guard.is_available:
        # Warm up with a test inference
        label, conf = guard.classify("Hello, I want to plan a trip to Paris")
        logger.info(f"✅ ML Prompt Guard ready (warmup: {label}, {conf:.2%})")
    else:
        logger.warning("⚠️ ML Prompt Guard unavailable, using regex-only protection")

"""
FastAPI Backend for Dynamic AI Firewall
Production-ready API for network threat detection and response

"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import numpy as np
from datetime import datetime
import uvicorn
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.detection.integrated_detector import IntegratedDetector
from stable_baselines3 import PPO

# Initialize FastAPI app
app = FastAPI(
    title="Dynamic AI Firewall API",
    description="Real-time network threat detection using RL + Anomaly Detection + Novelty Scoring",
    version="1.0.0"
)

# CORS middleware (for dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global detector (loaded on startup)
detector: Optional[IntegratedDetector] = None


# Pydantic models for API
class NetworkFlow(BaseModel):
    """Single network flow with 20 features"""
    flow_duration: float = Field(..., description="Flow duration in ms")
    total_fwd_packets: float
    total_bwd_packets: float
    total_length_fwd_packets: float
    total_length_bwd_packets: float
    flow_bytes_per_sec: float
    flow_packets_per_sec: float
    flow_iat_mean: float
    flow_iat_std: float
    flow_iat_max: float
    fwd_iat_mean: float
    bwd_iat_mean: float
    syn_flag_count: float
    rst_flag_count: float
    psh_flag_count: float
    ack_flag_count: float
    destination_port: float
    packet_length_mean: float
    packet_length_variance: float
    average_packet_size: float
    
    # Optional metadata
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    timestamp: Optional[str] = None
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array for model input"""
        return np.array([[
            self.flow_duration,
            self.total_fwd_packets,
            self.total_bwd_packets,
            self.total_length_fwd_packets,
            self.total_length_bwd_packets,
            self.flow_bytes_per_sec,
            self.flow_packets_per_sec,
            self.flow_iat_mean,
            self.flow_iat_std,
            self.flow_iat_max,
            self.fwd_iat_mean,
            self.bwd_iat_mean,
            self.syn_flag_count,
            self.rst_flag_count,
            self.psh_flag_count,
            self.ack_flag_count,
            self.destination_port,
            self.packet_length_mean,
            self.packet_length_variance,
            self.average_packet_size
        ]], dtype=np.float32)


class DetectionResponse(BaseModel):
    """Detection result"""
    decision: str = Field(..., description="ALLOW, BLOCK, RATE_LIMIT, FLAG_MONITOR, HONEYPOT")
    threat_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    confidence: float = Field(..., description="Confidence score 0-1")
    explanation: Dict = Field(..., description="Detailed reasoning")
    timestamp: str
    processing_time_ms: float


class BatchDetectionRequest(BaseModel):
    """Batch detection request"""
    flows: List[NetworkFlow]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    models: Dict[str, bool]
    timestamp: str


# Startup: Load models
@app.on_event("startup")
async def load_models():
    """Load AI models on startup"""
    global detector
    
    print("\n" + "="*70)
    print("LOADING AI FIREWALL MODELS")
    print("="*70)
    
    try:
        # Check for trained models
        model_path = None
        if os.path.exists("models/firewall_all_data.zip"):
            model_path = "models/firewall_all_data.zip"
        elif os.path.exists("models/firewall_final.zip"):
            model_path = "models/firewall_final.zip"
        
        if model_path:
            print(f"\n✓ Loading RL model: {model_path}")
            detector = IntegratedDetector(model_path)
            print("✓ AI Firewall models loaded successfully")
        else:
            print("\n⚠️  No trained models found")
            print("   API will run but detection will fail")
            print("   Train models first: python TRAIN_ALL_DATA.py")
        
    except Exception as e:
        print(f"\n❌ Error loading models: {e}")
        print("   API will start but detection endpoints will fail")
    
    print("\n" + "="*70)


# API Endpoints

@app.get("/", response_model=Dict)
async def root():
    """Root endpoint"""
    return {
        "name": "Dynamic AI Firewall API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "detect": "/api/v1/detect",
            "batch_detect": "/api/v1/detect/batch",
            "stats": "/api/v1/stats"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if detector is not None else "degraded",
        model_loaded=detector is not None,
        models={
            "rl_agent": detector is not None,
            "anomaly_detector": detector.anomaly_detector is not None if detector else False,
            "novelty_scorer": detector.novelty_scorer is not None if detector else False
        },
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/detect", response_model=DetectionResponse)
async def detect_threat(flow: NetworkFlow):
    """
    Detect threats in a single network flow
    
    This is the main endpoint used by the sensor agent
    """
    if detector is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    start_time = datetime.now()
    
    try:
        # Convert to numpy array
        X = flow.to_array()
        
        # Get decision
        decision = detector.detect(X)[0]
        threat_level = detector.get_threat_level(X)[0]
        
        # Get explanation
        explanation = detector.explain_decision(X[0])
        
        # Calculate confidence (based on RL action probabilities)
        confidence = 0.85  # Placeholder - can extract from model
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return DetectionResponse(
            decision=decision,
            threat_level=threat_level,
            confidence=confidence,
            explanation=explanation,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection error: {str(e)}")


@app.post("/api/v1/detect/batch", response_model=List[DetectionResponse])
async def batch_detect(request: BatchDetectionRequest):
    """
    Batch detection for multiple flows
    More efficient than multiple single requests
    """
    if detector is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    results = []
    
    for flow in request.flows:
        try:
            result = await detect_threat(flow)
            results.append(result)
        except Exception as e:
            # Continue processing other flows even if one fails
            results.append(DetectionResponse(
                decision="ERROR",
                threat_level="UNKNOWN",
                confidence=0.0,
                explanation={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                processing_time_ms=0.0
            ))
    
    return results


@app.get("/api/v1/stats")
async def get_stats():
    """Get firewall statistics"""
    # TODO: Implement actual statistics from database/logs
    return {
        "total_flows_processed": 0,
        "threats_detected": 0,
        "false_positives": 0,
        "uptime_seconds": 0,
        "avg_processing_time_ms": 0.0
    }


@app.post("/api/v1/feedback")
async def submit_feedback(
    flow_id: str,
    true_label: str,
    predicted_label: str,
    background_tasks: BackgroundTasks
):
    """
    Submit feedback for continuous learning
    Used to improve model over time
    """
    # TODO: Implement feedback storage and retraining pipeline
    background_tasks.add_task(log_feedback, flow_id, true_label, predicted_label)
    
    return {
        "status": "feedback_received",
        "message": "Thank you! This will help improve the model."
    }


async def log_feedback(flow_id: str, true_label: str, predicted_label: str):
    """Background task to log feedback"""
    # TODO: Store in database for later retraining
    print(f"Feedback: {flow_id} - True: {true_label}, Predicted: {predicted_label}")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "detail": str(exc)}


@app.exception_handler(500)
async def server_error_handler(request, exc):
    return {"error": "Internal server error", "detail": str(exc)}


if __name__ == "__main__":
    print("\n" + "="*70)
    print("DYNAMIC AI FIREWALL - API SERVER")
    print("="*70)
    print("\nStarting FastAPI server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set True for development
        log_level="info"
    )

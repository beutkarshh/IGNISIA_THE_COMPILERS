"""
Real-Time AI Agent Pipeline Service
Processes streaming telemetry data and provides live trend analysis
"""

import asyncio
import json
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Deque
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class TelemetryDataPoint:
    """Single telemetry measurement"""
    subject_id: int
    itemid: int
    valuenum: float
    valueuom: str
    charttime: str
    timestamp: datetime

@dataclass
class AITrendPrediction:
    """AI prediction for a specific vital sign"""
    itemid: int
    vital_name: str
    current_value: float
    trend_direction: str  # 'rising', 'falling', 'stable'
    trend_confidence: float  # 0.0 to 1.0
    prediction_next_30s: float
    abrupt_change_risk: float  # 0.0 to 1.0
    pattern_detected: Optional[str]
    alert_level: str  # 'none', 'caution', 'warning', 'critical'

@dataclass
class AIAnalysisResult:
    """Complete AI analysis result"""
    patient_id: int
    analysis_timestamp: datetime
    processing_time_ms: int
    cycle_number: int
    trend_predictions: List[AITrendPrediction]
    overall_risk_score: float
    pattern_summary: str
    alert_count: Dict[str, int]  # count by alert_level
    confidence_score: float

class RealTimeAIService:
    """
    Real-time AI service that processes streaming telemetry data
    """
    
    def __init__(self, buffer_size: int = 3):
        self.buffer_size = buffer_size  # Process every 3 data cycles
        self.patient_buffers: Dict[int, Deque[List[TelemetryDataPoint]]] = {}
        self.cycle_counters: Dict[int, int] = {}
        self.last_analysis: Dict[int, AIAnalysisResult] = {}
        self.subscribers: List[callable] = []
        
        # Vital sign mappings (MIMIC-III item IDs)
        self.vital_mappings = {
            211: 'Heart Rate',
            220045: 'Heart Rate',
            456: 'Mean Blood Pressure',
            52: 'Mean Blood Pressure', 
            220052: 'Mean Blood Pressure',
            6702: 'Mean Blood Pressure',
            220181: 'Non Invasive Blood Pressure mean',
            225312: 'ART mean',
            618: 'Respiratory Rate',
            615: 'Respiratory Rate',
            220210: 'Respiratory Rate',
            224690: 'Respiratory Rate',
            646: 'SpO2',
            220277: 'SpO2'
        }
    
    def add_subscriber(self, callback: callable):
        """Add callback for real-time AI results"""
        self.subscribers.append(callback)
    
    async def process_telemetry_batch(self, patient_id: int, telemetry_batch: List[Dict[str, Any]]):
        """
        Process a batch of telemetry data for a patient
        """
        # Convert to TelemetryDataPoint objects
        data_points = []
        for item in telemetry_batch:
            try:
                data_point = TelemetryDataPoint(
                    subject_id=item.get('subject_id', patient_id),
                    itemid=item['itemid'],
                    valuenum=float(item['valuenum']),
                    valueuom=item.get('valueuom', ''),
                    charttime=item['charttime'],
                    timestamp=datetime.now()
                )
                data_points.append(data_point)
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid telemetry data point: {e}")
                continue
        
        if not data_points:
            return
        
        # Initialize patient buffer if needed
        if patient_id not in self.patient_buffers:
            self.patient_buffers[patient_id] = deque(maxlen=self.buffer_size)
            self.cycle_counters[patient_id] = 0
        
        # Add to buffer
        self.patient_buffers[patient_id].append(data_points)
        self.cycle_counters[patient_id] += 1
        
        # Process if buffer is full
        if len(self.patient_buffers[patient_id]) >= self.buffer_size:
            await self._analyze_trends(patient_id)
    
    async def _analyze_trends(self, patient_id: int):
        """
        Perform AI trend analysis on buffered data
        """
        start_time = datetime.now()
        
        try:
            buffer = self.patient_buffers[patient_id]
            cycle_number = self.cycle_counters[patient_id]
            
            # Group data by vital sign (itemid)
            vital_timeseries = self._group_by_vital(buffer)
            
            # Analyze each vital sign
            trend_predictions = []
            for itemid, timeseries in vital_timeseries.items():
                prediction = await self._analyze_vital_trend(itemid, timeseries)
                if prediction:
                    trend_predictions.append(prediction)
            
            # Calculate overall metrics
            overall_risk = self._calculate_overall_risk(trend_predictions)
            pattern_summary = self._generate_pattern_summary(trend_predictions)
            alert_counts = self._count_alerts(trend_predictions)
            confidence = self._calculate_confidence(trend_predictions)
            
            # Create analysis result
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            result = AIAnalysisResult(
                patient_id=patient_id,
                analysis_timestamp=datetime.now(),
                processing_time_ms=processing_time,
                cycle_number=cycle_number,
                trend_predictions=trend_predictions,
                overall_risk_score=overall_risk,
                pattern_summary=pattern_summary,
                alert_count=alert_counts,
                confidence_score=confidence
            )
            
            # Store and notify subscribers
            self.last_analysis[patient_id] = result
            await self._notify_subscribers(result)
            
            logger.info(f"AI analysis completed for patient {patient_id}, cycle {cycle_number}")
            
        except Exception as e:
            logger.error(f"Error in AI trend analysis for patient {patient_id}: {e}")
    
    def _group_by_vital(self, buffer: Deque[List[TelemetryDataPoint]]) -> Dict[int, List[TelemetryDataPoint]]:
        """Group telemetry data by vital sign (itemid)"""
        vital_timeseries = {}
        
        for batch in buffer:
            for point in batch:
                if point.itemid not in vital_timeseries:
                    vital_timeseries[point.itemid] = []
                vital_timeseries[point.itemid].append(point)
        
        return vital_timeseries
    
    async def _analyze_vital_trend(self, itemid: int, timeseries: List[TelemetryDataPoint]) -> Optional[AITrendPrediction]:
        """Analyze trend for a single vital sign"""
        if len(timeseries) < 2:
            return None
        
        try:
            # Sort by timestamp
            timeseries.sort(key=lambda x: x.timestamp)
            
            # Extract values
            values = [point.valuenum for point in timeseries]
            current_value = values[-1]
            
            # Simple trend analysis
            trend_direction, confidence = self._calculate_trend(values)
            
            # Predict next value (simple linear extrapolation)
            prediction = self._predict_next_value(values)
            
            # Detect abrupt changes
            abrupt_risk = self._detect_abrupt_change_risk(values)
            
            # Pattern detection
            pattern = self._detect_pattern(values)
            
            # Determine alert level
            alert_level = self._determine_alert_level(itemid, current_value, trend_direction, abrupt_risk)
            
            vital_name = self.vital_mappings.get(itemid, f"ItemID_{itemid}")
            
            return AITrendPrediction(
                itemid=itemid,
                vital_name=vital_name,
                current_value=current_value,
                trend_direction=trend_direction,
                trend_confidence=confidence,
                prediction_next_30s=prediction,
                abrupt_change_risk=abrupt_risk,
                pattern_detected=pattern,
                alert_level=alert_level
            )
            
        except Exception as e:
            logger.error(f"Error analyzing trend for vital {itemid}: {e}")
            return None
    
    def _calculate_trend(self, values: List[float]) -> tuple[str, float]:
        """Calculate trend direction and confidence"""
        if len(values) < 2:
            return 'stable', 0.0
        
        # Simple moving average trend
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        change_percent = ((second_half - first_half) / first_half) * 100 if first_half != 0 else 0
        
        if abs(change_percent) < 5:
            return 'stable', min(0.8, 1.0 - abs(change_percent)/5)
        elif change_percent > 0:
            return 'rising', min(0.95, change_percent / 20)
        else:
            return 'falling', min(0.95, abs(change_percent) / 20)
    
    def _predict_next_value(self, values: List[float]) -> float:
        """Simple linear prediction"""
        if len(values) < 2:
            return values[-1] if values else 0.0
        
        # Linear regression (simple)
        n = len(values)
        x_avg = (n - 1) / 2  # 0, 1, 2, ... avg
        y_avg = sum(values) / n
        
        numerator = sum((i - x_avg) * (values[i] - y_avg) for i in range(n))
        denominator = sum((i - x_avg) ** 2 for i in range(n))
        
        if denominator == 0:
            return values[-1]
        
        slope = numerator / denominator
        intercept = y_avg - slope * x_avg
        
        # Predict next point
        next_x = n
        return slope * next_x + intercept
    
    def _detect_abrupt_change_risk(self, values: List[float]) -> float:
        """Detect risk of abrupt change"""
        if len(values) < 3:
            return 0.0
        
        # Calculate volatility
        diffs = [abs(values[i] - values[i-1]) for i in range(1, len(values))]
        avg_change = sum(diffs) / len(diffs)
        recent_change = diffs[-1] if diffs else 0
        
        # Risk based on recent change vs historical
        if avg_change == 0:
            return 0.0
        
        volatility_ratio = recent_change / avg_change
        
        # Risk increases with volatility
        return min(1.0, volatility_ratio / 3.0)
    
    def _detect_pattern(self, values: List[float]) -> Optional[str]:
        """Simple pattern detection"""
        if len(values) < 3:
            return None
        
        # Check for oscillation
        changes = [values[i] - values[i-1] for i in range(1, len(values))]
        if len(changes) >= 2:
            sign_changes = sum(1 for i in range(1, len(changes)) 
                             if (changes[i] > 0) != (changes[i-1] > 0))
            if sign_changes >= len(changes) * 0.6:
                return "oscillating"
        
        # Check for acceleration
        if len(changes) >= 2:
            accel = [changes[i] - changes[i-1] for i in range(1, len(changes))]
            avg_accel = sum(accel) / len(accel)
            if avg_accel > 0.5:
                return "accelerating"
            elif avg_accel < -0.5:
                return "decelerating"
        
        return None
    
    def _determine_alert_level(self, itemid: int, value: float, trend: str, abrupt_risk: float) -> str:
        """Determine alert level based on vital sign analysis"""
        # Simple thresholds (would be more sophisticated in production)
        if itemid in [211, 220045]:  # Heart Rate
            if value > 120 or value < 50:
                return 'critical'
            elif (value > 110 or value < 60) and trend != 'stable':
                return 'warning'
            elif abrupt_risk > 0.7:
                return 'caution'
        
        elif itemid in [456, 52, 220052, 6702]:  # Mean BP
            if value > 110 or value < 60:
                return 'critical'
            elif (value > 100 or value < 70) and trend != 'stable':
                return 'warning'
            elif abrupt_risk > 0.7:
                return 'caution'
        
        return 'none'
    
    def _calculate_overall_risk(self, predictions: List[AITrendPrediction]) -> float:
        """Calculate overall patient risk score"""
        if not predictions:
            return 0.0
        
        risk_weights = {
            'none': 0.0,
            'caution': 0.25,
            'warning': 0.6,
            'critical': 1.0
        }
        
        total_risk = sum(risk_weights.get(pred.alert_level, 0) for pred in predictions)
        return min(100.0, (total_risk / len(predictions)) * 100)
    
    def _generate_pattern_summary(self, predictions: List[AITrendPrediction]) -> str:
        """Generate human-readable pattern summary"""
        if not predictions:
            return "No data available"
        
        alerts = [pred for pred in predictions if pred.alert_level != 'none']
        trends = [pred.trend_direction for pred in predictions]
        
        if alerts:
            return f"{len(alerts)} vital sign(s) showing concerning patterns"
        elif 'rising' in trends and 'falling' in trends:
            return "Mixed trending patterns observed"
        elif trends.count('rising') > trends.count('falling'):
            return "Generally trending upward"
        elif trends.count('falling') > trends.count('rising'):
            return "Generally trending downward"
        else:
            return "Stable vital sign patterns"
    
    def _count_alerts(self, predictions: List[AITrendPrediction]) -> Dict[str, int]:
        """Count alerts by level"""
        counts = {'none': 0, 'caution': 0, 'warning': 0, 'critical': 0}
        for pred in predictions:
            counts[pred.alert_level] += 1
        return counts
    
    def _calculate_confidence(self, predictions: List[AITrendPrediction]) -> float:
        """Calculate overall confidence in analysis"""
        if not predictions:
            return 0.0
        
        avg_confidence = sum(pred.trend_confidence for pred in predictions) / len(predictions)
        return avg_confidence
    
    async def _notify_subscribers(self, result: AIAnalysisResult):
        """Notify all subscribers of new analysis result"""
        for callback in self.subscribers:
            try:
                await callback(result)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def get_latest_analysis(self, patient_id: int) -> Optional[AIAnalysisResult]:
        """Get the latest analysis result for a patient"""
        return self.last_analysis.get(patient_id)
    
    def to_dict(self, result: AIAnalysisResult) -> Dict[str, Any]:
        """Convert analysis result to dictionary for JSON serialization"""
        data = asdict(result)
        # Convert datetime to ISO string
        data['analysis_timestamp'] = result.analysis_timestamp.isoformat()
        return data

# Global service instance
realtime_ai_service = RealTimeAIService()
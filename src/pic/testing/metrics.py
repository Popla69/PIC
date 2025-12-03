"""Performance metrics and KPI calculators."""

from typing import List
import statistics


class PerformanceMetrics:
    """Calculate performance KPIs for PIC system."""
    
    @staticmethod
    def calculate_fpr(flagged_count: int, total_benign: int) -> float:
        """Calculate False Positive Rate.
        
        FPR = flagged / total_benign
        
        Args:
            flagged_count: Number of benign events flagged as malicious
            total_benign: Total number of benign events
            
        Returns:
            False positive rate (0.0 to 1.0)
        """
        if total_benign == 0:
            return 0.0
        return flagged_count / total_benign
    
    @staticmethod
    def calculate_tpr(detected_count: int, total_malicious: int) -> float:
        """Calculate True Positive Rate (Detection Rate).
        
        TPR = detected / total_malicious
        
        Args:
            detected_count: Number of malicious events detected
            total_malicious: Total number of malicious events
            
        Returns:
            True positive rate (0.0 to 1.0)
        """
        if total_malicious == 0:
            return 0.0
        return detected_count / total_malicious
    
    @staticmethod
    def calculate_latency_percentiles(latencies: List[float]) -> dict:
        """Calculate latency percentiles.
        
        Args:
            latencies: List of latency measurements in milliseconds
            
        Returns:
            Dictionary with P50, P95, P99 percentiles
        """
        if not latencies:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        
        sorted_latencies = sorted(latencies)
        
        return {
            "p50": statistics.quantiles(sorted_latencies, n=100)[49],  # 50th percentile
            "p95": statistics.quantiles(sorted_latencies, n=100)[94],  # 95th percentile
            "p99": statistics.quantiles(sorted_latencies, n=100)[98],  # 99th percentile
        }
    
    @staticmethod
    def calculate_overhead(
        instrumented_latencies: List[float],
        baseline_latencies: List[float]
    ) -> float:
        """Calculate instrumentation overhead percentage.
        
        Overhead = (mean_instrumented - mean_baseline) / mean_baseline * 100
        
        Args:
            instrumented_latencies: Latencies with instrumentation
            baseline_latencies: Latencies without instrumentation
            
        Returns:
            Overhead percentage
        """
        if not baseline_latencies or not instrumented_latencies:
            return 0.0
        
        mean_baseline = statistics.mean(baseline_latencies)
        mean_instrumented = statistics.mean(instrumented_latencies)
        
        if mean_baseline == 0:
            return 0.0
        
        overhead = ((mean_instrumented - mean_baseline) / mean_baseline) * 100
        return overhead
    
    @staticmethod
    def calculate_accuracy(tp: int, tn: int, fp: int, fn: int) -> float:
        """Calculate overall accuracy.
        
        Accuracy = (TP + TN) / (TP + TN + FP + FN)
        
        Args:
            tp: True positives
            tn: True negatives
            fp: False positives
            fn: False negatives
            
        Returns:
            Accuracy (0.0 to 1.0)
        """
        total = tp + tn + fp + fn
        if total == 0:
            return 0.0
        return (tp + tn) / total
    
    @staticmethod
    def calculate_precision(tp: int, fp: int) -> float:
        """Calculate precision.
        
        Precision = TP / (TP + FP)
        
        Args:
            tp: True positives
            fp: False positives
            
        Returns:
            Precision (0.0 to 1.0)
        """
        if tp + fp == 0:
            return 0.0
        return tp / (tp + fp)
    
    @staticmethod
    def calculate_f1_score(precision: float, recall: float) -> float:
        """Calculate F1 score.
        
        F1 = 2 * (precision * recall) / (precision + recall)
        
        Args:
            precision: Precision value
            recall: Recall (TPR) value
            
        Returns:
            F1 score (0.0 to 1.0)
        """
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

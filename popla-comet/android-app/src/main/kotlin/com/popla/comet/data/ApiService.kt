package com.popla.comet.data

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    
    @Multipart
    @POST("api/v1/analyze")
    suspend fun analyzeImage(
        @Part file: MultipartBody.Part,
        @Part("prompt") prompt: RequestBody? = null,
        @Part("user_id") userId: RequestBody? = null,
        @Part("use_cache") useCache: RequestBody? = null
    ): Response<AnalysisResponse>
    
    @POST("api/v1/analyze/base64")
    suspend fun analyzeImageBase64(
        @Body request: AnalysisRequest
    ): Response<AnalysisResponse>
    
    @Multipart
    @POST("api/v1/batch/analyze")
    suspend fun batchAnalyze(
        @Part files: List<MultipartBody.Part>,
        @Part("user_id") userId: RequestBody? = null
    ): Response<BatchAnalysisResponse>
    
    @GET("api/v1/history")
    suspend fun getHistory(
        @Query("user_id") userId: String? = null,
        @Query("limit") limit: Int = 50
    ): Response<HistoryResponse>
    
    @GET("api/v1/result/{analysis_id}")
    suspend fun getResult(
        @Path("analysis_id") analysisId: String
    ): Response<AnalysisResult>
    
    @GET("health")
    suspend fun healthCheck(): Response<HealthResponse>
    
    @GET("api/v1/status")
    suspend fun getStatus(): Response<StatusResponse>
}

// Data models
data class AnalysisRequest(
    val image_data: String,
    val analysis_type: String = "general",
    val prompt: String? = null
)

data class AnalysisResponse(
    val analysis_id: String,
    val timestamp: String,
    val status: String,
    val result: ResultData?,
    val error: String?,
    val processing_time: Double
)

data class ResultData(
    val description: String,
    val confidence: Double,
    val tags: List<String>,
    val objects_detected: List<String>
)

data class BatchAnalysisResponse(
    val batch_id: String,
    val total_images: Int,
    val successful: Int,
    val failed: Int,
    val processing_time: Double,
    val results: List<BatchResult>
)

data class BatchResult(
    val index: Int,
    val status: String,
    val description: String?,
    val confidence: Double?,
    val tags: List<String>?,
    val objects_detected: List<String>?,
    val error: String?
)

data class HistoryResponse(
    val total: Int,
    val results: List<AnalysisResult>
)

data class AnalysisResult(
    val id: String,
    val timestamp: String,
    val status: String,
    val processing_time: Double,
    val description: String?,
    val confidence: Double?,
    val tags: List<String>?,
    val objects_detected: List<String>?
)

data class HealthResponse(
    val status: String,
    val service: String,
    val version: String,
    val openai_configured: Boolean,
    val cache_stats: CacheStats?,
    val database: String?
)

data class CacheStats(
    val size: Int,
    val max_size: Int,
    val hits: Int,
    val misses: Int,
    val hit_rate: Double,
    val ttl_minutes: Double
)

data class StatusResponse(
    val api_version: String,
    val service: String,
    val status: String,
    val features: Map<String, Boolean>,
    val statistics: Statistics?
)

data class Statistics(
    val total_analyses: Int,
    val successful_analyses: Int,
    val failed_analyses: Int,
    val average_processing_time: Double,
    val unique_users: Int
)
